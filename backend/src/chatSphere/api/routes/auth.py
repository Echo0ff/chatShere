"""
认证相关路由
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.chatSphere.core.auth import auth_manager, get_current_active_user, oauth_manager
from src.chatSphere.core.cache import cache_manager
from src.chatSphere.core.database import get_db, transactional
from src.chatSphere.core.models import OAuthProvider, User
from src.chatSphere.services.responses import (
    HTTP_STATUS_MAP,
    ApiResponse,
    ResponseCode,
    ResponseMessage,
)

router = APIRouter()


# ==================== Pydantic模型 ====================


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    display_name: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OAuth2Login(BaseModel):
    provider: str  # "google" or "github"
    access_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    display_name: str
    avatar_url: Optional[str]
    oauth_provider: str
    created_at: str
    last_seen: Optional[str]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ==================== 路由处理器 ====================


@router.post("/register", response_model=ApiResponse)
@transactional
async def register_user(user_data: UserRegister, session: AsyncSession = Depends(get_db)):
    """用户注册"""

    try:
        # 验证密码强度（简单版本）
        if len(user_data.password) < 6:
            return JSONResponse(
                status_code=HTTP_STATUS_MAP[ResponseCode.WEAK_PASSWORD],
                content=ApiResponse.error(
                    message=ResponseMessage.WEAK_PASSWORD,
                    code=ResponseCode.WEAK_PASSWORD,
                    data={"field": "password", "requirement": "至少6位字符"},
                ).dict(),
            )

        # 验证用户名格式
        if len(user_data.username) < 3 or not user_data.username.isalnum():
            return JSONResponse(
                status_code=HTTP_STATUS_MAP[ResponseCode.BAD_REQUEST],
                content=ApiResponse.error(
                    message="用户名格式不正确",
                    code=ResponseCode.BAD_REQUEST,
                    data={"field": "username", "requirement": "至少3位，只能包含字母和数字"},
                ).dict(),
            )

        # 创建用户
        user = await auth_manager.create_user(
            session=session,
            email=user_data.email,
            username=user_data.username,
            display_name=user_data.display_name,
            password=user_data.password,
            oauth_provider=OAuthProvider.LOCAL,
        )

        # 生成token
        tokens = await auth_manager.generate_tokens(session, user)

        # 缓存用户会话
        await cache_manager.cache_user_session(
            user.id,
            {
                "user_id": user.id,
                "username": user.username,
                "last_login": datetime.utcnow().isoformat(),
            },
        )

        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "oauth_provider": user.oauth_provider.value,
                "created_at": user.created_at.isoformat(),
                "last_seen": user.last_seen.isoformat() if user.last_seen else None,
            },
            **tokens,
        }

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.CREATED],
            content=ApiResponse.created(
                data=response_data, message=ResponseMessage.REGISTER_SUCCESS
            ).dict(),
        )

    except HTTPException as e:
        # 处理业务逻辑异常
        if "邮箱已被使用" in str(e.detail):
            error_code = ResponseCode.EMAIL_ALREADY_EXISTS
            message = ResponseMessage.EMAIL_ALREADY_EXISTS
        elif "用户名已被使用" in str(e.detail):
            error_code = ResponseCode.USERNAME_ALREADY_EXISTS
            message = ResponseMessage.USERNAME_ALREADY_EXISTS
        else:
            error_code = ResponseCode.BAD_REQUEST
            message = str(e.detail)

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[error_code],
            content=ApiResponse.error(message=message, code=error_code).dict(),
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.INTERNAL_ERROR],
            content=ApiResponse.error(
                message=ResponseMessage.INTERNAL_ERROR,
                code=ResponseCode.INTERNAL_ERROR,
                data={"detail": str(e)},
            ).dict(),
        )


@router.post("/login", response_model=ApiResponse)
@transactional
async def login_user(user_data: UserLogin, session: AsyncSession = Depends(get_db)):
    """用户登录"""

    try:
        # 检查速率限制
        if not await cache_manager.check_rate_limit(
            user_data.email, "login", limit=5, window=300  # 5分钟内最多5次尝试
        ):
            return JSONResponse(
                status_code=HTTP_STATUS_MAP[ResponseCode.TOO_MANY_REQUESTS],
                content=ApiResponse.error(
                    message="登录尝试过于频繁，请稍后再试", code=ResponseCode.TOO_MANY_REQUESTS
                ).dict(),
            )

        # 认证用户
        user = await auth_manager.authenticate_user(session, user_data.email, user_data.password)

        if not user:
            return JSONResponse(
                status_code=HTTP_STATUS_MAP[ResponseCode.INVALID_CREDENTIALS],
                content=ApiResponse.error(
                    message=ResponseMessage.INVALID_CREDENTIALS,
                    code=ResponseCode.INVALID_CREDENTIALS,
                ).dict(),
            )

        # 更新最后登录时间
        user.last_seen = datetime.utcnow()

        # 生成token
        tokens = await auth_manager.generate_tokens(session, user)

        # 缓存用户会话
        await cache_manager.cache_user_session(
            user.id,
            {
                "user_id": user.id,
                "username": user.username,
                "last_login": datetime.utcnow().isoformat(),
            },
        )

        response_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "oauth_provider": user.oauth_provider.value,
                "created_at": user.created_at.isoformat(),
                "last_seen": user.last_seen.isoformat(),
            },
            **tokens,
        }

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.SUCCESS],
            content=ApiResponse.success(
                data=response_data, message=ResponseMessage.LOGIN_SUCCESS
            ).dict(),
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.INTERNAL_ERROR],
            content=ApiResponse.error(
                message=ResponseMessage.INTERNAL_ERROR,
                code=ResponseCode.INTERNAL_ERROR,
                data={"detail": str(e)},
            ).dict(),
        )


@router.post("/oauth2/login", response_model=LoginResponse)
@transactional
async def oauth2_login(oauth_data: OAuth2Login, session: AsyncSession = Depends(get_db)):
    """OAuth2登录"""

    # 验证提供商
    if oauth_data.provider not in ["google", "github"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的OAuth2提供商")

    try:
        provider = OAuthProvider.GOOGLE if oauth_data.provider == "google" else OAuthProvider.GITHUB

        # 处理OAuth登录
        result = await oauth_manager.process_oauth_login(
            session=session,
            provider=provider,
            access_token=oauth_data.access_token,
            auth_manager=auth_manager,
        )

        # 缓存用户会话
        await cache_manager.cache_user_session(
            result["user"]["id"],
            {
                "user_id": result["user"]["id"],
                "username": result["user"]["username"],
                "last_login": datetime.utcnow().isoformat(),
                "oauth_provider": oauth_data.provider,
            },
        )

        return LoginResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"OAuth2登录失败: {str(e)}"
        )


@router.post("/token/refresh", response_model=ApiResponse)
@transactional
async def refresh_access_token(
    token_data: RefreshTokenRequest, session: AsyncSession = Depends(get_db)
):
    """刷新访问token"""

    try:
        tokens = await auth_manager.refresh_access_token(session, token_data.refresh_token)

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.SUCCESS],
            content=ApiResponse.success(
                data=tokens, message=ResponseMessage.TOKEN_REFRESHED
            ).dict(),
        )

    except HTTPException as e:
        if "invalid" in str(e.detail).lower():
            error_code = ResponseCode.INVALID_TOKEN
            message = ResponseMessage.INVALID_TOKEN
        elif "expired" in str(e.detail).lower():
            error_code = ResponseCode.TOKEN_EXPIRED
            message = ResponseMessage.TOKEN_EXPIRED
        else:
            error_code = ResponseCode.BAD_REQUEST
            message = str(e.detail)

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[error_code],
            content=ApiResponse.error(message=message, code=error_code).dict(),
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.INTERNAL_ERROR],
            content=ApiResponse.error(
                message=ResponseMessage.INTERNAL_ERROR,
                code=ResponseCode.INTERNAL_ERROR,
                data={"detail": str(e)},
            ).dict(),
        )


@router.post("/logout", response_model=ApiResponse)
@transactional
async def logout_user(
    current_user: User = Depends(get_current_active_user), session: AsyncSession = Depends(get_db)
):
    """用户登出"""

    try:
        # 清理用户会话缓存
        await cache_manager.clear_user_session(current_user.id)

        # 这里可以添加其他登出逻辑，比如将token加入黑名单

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.SUCCESS],
            content=ApiResponse.success(message=ResponseMessage.LOGOUT_SUCCESS).dict(),
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.INTERNAL_ERROR],
            content=ApiResponse.error(
                message=ResponseMessage.INTERNAL_ERROR,
                code=ResponseCode.INTERNAL_ERROR,
                data={"detail": str(e)},
            ).dict(),
        )


@router.post("/revoke-token")
async def revoke_token(
    token: str = Form(...), current_user: User = Depends(get_current_active_user)
):
    """撤销token"""

    try:
        await auth_manager.revoke_token(token)
        return {"message": "Token已撤销"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Token撤销失败: {str(e)}"
        )


@router.get("/me", response_model=ApiResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """获取当前用户资料"""

    try:
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "display_name": current_user.display_name,
            "avatar_url": current_user.avatar_url,
            "oauth_provider": current_user.oauth_provider.value,
            "created_at": current_user.created_at.isoformat(),
            "last_seen": current_user.last_seen.isoformat() if current_user.last_seen else None,
        }

        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.SUCCESS],
            content=ApiResponse.success(data=user_data, message="获取用户信息成功").dict(),
        )

    except Exception as e:
        return JSONResponse(
            status_code=HTTP_STATUS_MAP[ResponseCode.INTERNAL_ERROR],
            content=ApiResponse.error(
                message=ResponseMessage.INTERNAL_ERROR,
                code=ResponseCode.INTERNAL_ERROR,
                data={"detail": str(e)},
            ).dict(),
        )


@router.put("/me")
@transactional
async def update_user_profile(
    display_name: Optional[str] = Form(None),
    avatar_url: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """更新用户资料"""

    try:
        # 更新字段
        if display_name is not None:
            current_user.display_name = display_name
        if avatar_url is not None:
            current_user.avatar_url = avatar_url
        if bio is not None:
            current_user.bio = bio

        current_user.updated_at = datetime.utcnow()

        return {"message": "资料更新成功"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"资料更新失败: {str(e)}"
        )


@router.post("/change-password")
@transactional
async def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """修改密码"""

    # 验证当前密码
    if not current_user.hashed_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OAuth用户无法修改密码")

    if not auth_manager.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前密码错误")

    # 验证新密码
    if len(new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码长度至少6位")

    try:
        # 更新密码
        current_user.hashed_password = auth_manager.get_password_hash(new_password)
        current_user.updated_at = datetime.utcnow()

        return {"message": "密码修改成功"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"密码修改失败: {str(e)}"
        )


@router.get("/validate-token")
async def validate_token(current_user: User = Depends(get_current_active_user)):
    """验证token有效性"""

    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "timestamp": datetime.utcnow().isoformat(),
    }
