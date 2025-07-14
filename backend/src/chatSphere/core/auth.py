"""
JWT认证和OAuth2系统
"""
import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import cache_manager
from .config import settings
from .database import get_db
from .models import OAuthProvider, RefreshToken, User, UserStatus

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer
security = HTTPBearer()


class AuthManager:
    """认证管理器"""

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        self.refresh_token_expire_days = settings.refresh_token_expire_days

    # 密码相关
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)

    # JWT Token相关
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """创建访问令牌"""
        to_encode = data.copy()

        # 添加过期时间
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.utcnow(),
                "type": "access",
                "jti": str(uuid.uuid4()),  # JWT ID，用于黑名单
            }
        )

        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        return secrets.token_urlsafe(32)

    async def store_refresh_token(
        self, session: AsyncSession, user_id: str, token: str
    ) -> RefreshToken:
        """存储刷新令牌"""
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        refresh_token = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)

        session.add(refresh_token)
        await session.flush()
        await session.refresh(refresh_token)

        return refresh_token

    def decode_token(self, token: str) -> Dict[str, Any]:
        """解码JWT令牌"""
        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """验证并解码token"""
        payload = self.decode_token(token)

        # 检查token是否在黑名单
        jti = payload.get("jti")
        if jti and await cache_manager.is_token_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token已被撤销",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    async def revoke_token(self, token: str):
        """撤销token（加入黑名单）"""
        try:
            payload = self.decode_token(token)
            jti = payload.get("jti")
            if jti:
                # 计算剩余过期时间
                exp = payload.get("exp")
                if exp:
                    expire_time = exp - int(datetime.utcnow().timestamp())
                    if expire_time > 0:
                        await cache_manager.blacklist_token(jti, expire_time)
        except:
            pass  # Token已过期或无效，无需处理

    # 用户认证
    async def authenticate_user(
        self, session: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """用户名密码认证"""
        stmt = select(User).where(User.email == email, User.status == UserStatus.ACTIVE)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.hashed_password:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    async def get_user_by_id(self, session: AsyncSession, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id, User.status == UserStatus.ACTIVE)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        session: AsyncSession,
        email: str,
        username: str,
        display_name: str,
        password: str = None,
        oauth_provider: OAuthProvider = OAuthProvider.LOCAL,
        oauth_id: str = None,
        avatar_url: str = None,
    ) -> User:
        """创建用户"""

        # 检查邮箱是否已存在
        existing_user = await self.get_user_by_email(session, email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被使用")

        # 检查用户名是否已存在
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已被使用")

        # 创建用户
        user_data = {
            "id": str(uuid.uuid4()),
            "email": email,
            "username": username,
            "display_name": display_name,
            "oauth_provider": oauth_provider,
            "oauth_id": oauth_id,
            "avatar_url": avatar_url,
            "status": UserStatus.ACTIVE,
        }

        if password:
            user_data["hashed_password"] = self.get_password_hash(password)

        user = User(**user_data)
        session.add(user)
        await session.flush()
        await session.refresh(user)

        return user

    async def generate_tokens(self, session: AsyncSession, user: User) -> Dict[str, str]:
        """生成访问令牌和刷新令牌"""

        # 创建访问令牌
        access_token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "display_name": user.display_name,
        }
        access_token = self.create_access_token(access_token_data)

        # 创建刷新令牌
        refresh_token = self.create_refresh_token(user.id)
        await self.store_refresh_token(session, user.id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(
        self, session: AsyncSession, refresh_token: str
    ) -> Dict[str, str]:
        """使用刷新令牌获取新的访问令牌"""

        # 查找刷新令牌
        stmt = select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
        result = await session.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")

        # 获取用户
        user = await self.get_user_by_id(session, token_record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

        # 撤销旧的刷新令牌
        token_record.is_revoked = True

        # 生成新的令牌对
        return await self.generate_tokens(session, user)


class OAuth2Manager:
    """OAuth2管理器"""

    def __init__(self):
        self.google_client_id = settings.google_client_id
        self.google_client_secret = settings.google_client_secret
        self.github_client_id = settings.github_client_id
        self.github_client_secret = settings.github_client_secret

    async def get_google_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取Google用户信息"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="无法获取Google用户信息"
                )

            return response.json()

    async def get_github_user_info(self, access_token: str) -> Dict[str, Any]:
        """获取GitHub用户信息"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="无法获取GitHub用户信息"
                )

            return response.json()

    async def process_oauth_login(
        self,
        session: AsyncSession,
        provider: OAuthProvider,
        access_token: str,
        auth_manager: AuthManager,
    ) -> Dict[str, Any]:
        """处理OAuth登录"""

        # 获取用户信息
        if provider == OAuthProvider.GOOGLE:
            user_info = await self.get_google_user_info(access_token)
            oauth_id = user_info["id"]
            email = user_info["email"]
            display_name = user_info["name"]
            avatar_url = user_info.get("picture")
            username = email.split("@")[0]  # 简单的用户名生成

        elif provider == OAuthProvider.GITHUB:
            user_info = await self.get_github_user_info(access_token)
            oauth_id = str(user_info["id"])
            email = user_info.get("email")
            display_name = user_info.get("name") or user_info["login"]
            avatar_url = user_info.get("avatar_url")
            username = user_info["login"]

            if not email:
                # GitHub可能不返回邮箱，需要额外请求
                async with httpx.AsyncClient() as client:
                    email_response = await client.get(
                        "https://api.github.com/user/emails",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    if email_response.status_code == 200:
                        emails = email_response.json()
                        primary_email = next((e for e in emails if e["primary"]), None)
                        if primary_email:
                            email = primary_email["email"]

                if not email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="无法获取GitHub邮箱"
                    )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的OAuth提供商")

        # 查找现有用户
        stmt = select(User).where(User.oauth_provider == provider, User.oauth_id == oauth_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # 检查邮箱是否已被其他方式注册
            existing_user = await auth_manager.get_user_by_email(session, email)
            if existing_user:
                # 如果是本地注册的用户，可以选择绑定OAuth
                if existing_user.oauth_provider == OAuthProvider.LOCAL:
                    # 更新用户OAuth信息
                    existing_user.oauth_provider = provider
                    existing_user.oauth_id = oauth_id
                    if avatar_url:
                        existing_user.avatar_url = avatar_url
                    user = existing_user
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱已被其他OAuth提供商使用"
                    )
            else:
                # 创建新用户
                # 确保用户名唯一
                base_username = username
                counter = 1
                while True:
                    stmt = select(User).where(User.username == username)
                    result = await session.execute(stmt)
                    if not result.scalar_one_or_none():
                        break
                    username = f"{base_username}{counter}"
                    counter += 1

                user = await auth_manager.create_user(
                    session=session,
                    email=email,
                    username=username,
                    display_name=display_name,
                    oauth_provider=provider,
                    oauth_id=oauth_id,
                    avatar_url=avatar_url,
                )

        # 更新最后登录时间
        user.last_seen = datetime.utcnow()

        # 生成令牌
        tokens = await auth_manager.generate_tokens(session, user)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "oauth_provider": user.oauth_provider.value,
            },
            **tokens,
        }


# 创建管理器实例
auth_manager = AuthManager()
oauth_manager = OAuth2Manager()


# 依赖注入函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    """获取当前用户（依赖注入）"""

    # 验证token
    payload = await auth_manager.verify_token(credentials.credentials)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户
    user = await auth_manager.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户账户已被禁用")
    return current_user


# 可选的用户认证（用于WebSocket等场景）
async def get_optional_user(
    request: Request, session: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """可选的用户认证"""
    try:
        # 从查询参数或头部获取token
        token = request.query_params.get("token") or request.headers.get("authorization")

        if token:
            if token.startswith("Bearer "):
                token = token[7:]

            payload = await auth_manager.verify_token(token)
            user_id = payload.get("sub")

            if user_id:
                return await auth_manager.get_user_by_id(session, user_id)
    except:
        pass

    return None
