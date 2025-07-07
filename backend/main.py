"""
ChatSphere 聊天室主应用
企业级版本 - 集成JWT、OAuth2、ORM、Redis、中间件
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.exceptions import RequestValidationError

from config import settings, is_development
from src.chatSphere.core.database import db_manager, get_db, check_database_health
from src.chatSphere.core.cache import cache_manager, check_redis_health
from src.chatSphere.core.auth import get_current_active_user, get_optional_user
from src.chatSphere.core.models import User, Message, Room, Group, ChatType, MessageType
from src.chatSphere.core.middleware import setup_middleware, WebSocketConnectionMiddleware
from src.chatSphere.core.websocket_manager import ConnectionManager
from src.chatSphere.services.responses import ApiResponse, ResponseCode, ResponseMessage, HTTP_STATUS_MAP, format_validation_errors

# 导入路由
from src.chatSphere.api.routes.auth import router as auth_router

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/chatsphere.log') if not is_development() else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局连接管理器
connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 启动 ChatSphere 服务器...")
    
    try:
        # 初始化数据库
        await db_manager.initialize()
        await db_manager.create_tables()
        logger.info("✅ 数据库连接已建立")
        
        # 初始化Redis
        await cache_manager.initialize()
        logger.info("✅ Redis连接已建立")
        
        # 清理旧的WebSocket连接缓存
        await connection_manager.cleanup_expired_connections()
        logger.info("✅ WebSocket连接管理器已初始化")
        
        logger.info("🎉 所有服务启动完成！")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise
    finally:
        # 清理资源
        logger.info("🔄 关闭服务器...")
        
        try:
            await connection_manager.disconnect_all()
            await cache_manager.close()
            await db_manager.close()
            logger.info("✅ 所有资源已清理")
        except Exception as e:
            logger.error(f"❌ 资源清理失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="🚀 企业级实时聊天系统 - 支持JWT认证、OAuth2登录、私聊群聊、消息状态管理",
    lifespan=lifespan,
    docs_url="/docs" if is_development() else None,
    redoc_url="/redoc" if is_development() else None,
)

# 先设置自定义中间件
setup_middleware(app)

# 最后设置CORS（这样CORS会最先执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 注册路由 ====================

# 注册认证路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])


# ==================== WebSocket路由 ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    统一WebSocket端点 - 支持认证和消息路由
    """
    logger.info("WebSocket连接尝试开始")
    
    # 接受WebSocket连接
    await websocket.accept()
    logger.info("WebSocket连接已接受")
    
    # 从查询参数中提取token
    token = websocket.query_params.get("token")
    logger.info(f"提取到token: {token is not None}")
    
    if not token:
        logger.warning("WebSocket连接缺少token")
        await websocket.close(code=4001, reason="缺少认证token")
        return
    
    # 认证用户
    try:
        from src.chatSphere.core.auth import auth_manager
        from src.chatSphere.core.database import get_db
        
        # 创建数据库会话
        async for session in get_db():
            payload = await auth_manager.verify_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                logger.warning("Token中缺少用户ID")
                await websocket.close(code=4001, reason="无效token")
                return
                
            user = await auth_manager.get_user_by_id(session, user_id)
            if not user:
                logger.warning(f"用户不存在: {user_id}")
                await websocket.close(code=4001, reason="用户不存在")
                return
            
            logger.info(f"用户认证成功: {user.username}")
            
            # 建立连接
            await connection_manager.connect(websocket, user, session)
            
            try:
                while True:
                    # 接收消息
                    data = await websocket.receive_text()
                    await connection_manager.handle_message(user.id, data, session)
                    
            except WebSocketDisconnect:
                logger.info(f"用户 {user.username} 断开连接")
            except Exception as e:
                logger.error(f"WebSocket错误 {user.username}: {e}")
            finally:
                await connection_manager.disconnect(user.id, session)
            break
            
    except Exception as e:
        logger.error(f"WebSocket认证失败: {e}")
        await websocket.close(code=4001, reason="认证失败")
        return


# ==================== REST API路由 ====================

# 健康检查
@app.get("/health")
async def health_check():
    """系统健康检查"""
    db_health = await check_database_health()
    redis_health = await check_redis_health()
    
    overall_status = "healthy" if (
        db_health["status"] == "healthy" and 
        redis_health["status"] == "healthy"
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "services": {
            "database": db_health,
            "redis": redis_health,
            "websocket": {
                "status": "healthy",
                "active_connections": len(connection_manager.active_connections)
            }
        }
    }


@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws?token=YOUR_JWT_TOKEN"
    }


# 用户相关路由
@app.get("/api/v1/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "oauth_provider": current_user.oauth_provider.value,
        "created_at": current_user.created_at.isoformat(),
        "last_seen": current_user.last_seen.isoformat() if current_user.last_seen else None
    }


@app.get("/api/v1/users/online")
async def get_online_users(
    current_user: User = Depends(get_current_active_user)
):
    """获取在线用户列表"""
    online_users = await connection_manager.get_online_users()
    return {
        "count": len(online_users),
        "users": online_users
    }


# 房间相关路由
@app.get("/api/v1/rooms")
async def get_public_rooms(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取公共房间列表"""
    from sqlalchemy import select
    
    stmt = select(Room).where(Room.is_public == True).limit(20)
    result = await session.execute(stmt)
    rooms = result.scalars().all()
    
    room_list = []
    for room in rooms:
        # 获取房间在线用户数
        online_count = len(await cache_manager.get_room_users(room.id))
        
        room_list.append({
            "id": room.id,
            "name": room.name,
            "description": room.description,
            "max_members": room.max_members,
            "online_count": online_count,
            "created_at": room.created_at.isoformat()
        })
    
    return {"rooms": room_list}


# 消息相关路由
@app.get("/api/v1/messages/{chat_type}/{chat_id}")
async def get_chat_messages(
    chat_type: str,
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取聊天消息历史"""
    from sqlalchemy import select, desc
    
    # 验证聊天类型
    if chat_type not in ["private", "group", "room"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的聊天类型"
        )
    
    # 构建查询
    if chat_type == "private":
        stmt = select(Message).where(
            ((Message.from_user_id == current_user.id) & (Message.to_user_id == chat_id)) |
            ((Message.from_user_id == chat_id) & (Message.to_user_id == current_user.id))
        ).order_by(desc(Message.created_at)).limit(limit).offset(offset)
    elif chat_type == "group":
        stmt = select(Message).where(
            Message.group_id == chat_id
        ).order_by(desc(Message.created_at)).limit(limit).offset(offset)
    else:  # room
        stmt = select(Message).where(
            Message.room_id == chat_id
        ).order_by(desc(Message.created_at)).limit(limit).offset(offset)
    
    result = await session.execute(stmt)
    messages = result.scalars().all()
    
    # 格式化消息
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "from_user_id": msg.from_user_id,
            "content": msg.content,
            "message_type": msg.message_type.value,
            "created_at": msg.created_at.isoformat(),
            "is_edited": msg.is_edited,
            "reply_to_id": msg.reply_to_id
        })
    
    # 反转顺序（最新的在底部）
    message_list.reverse()
    
    return {
        "messages": message_list,
        "total": len(message_list),
        "has_more": len(messages) == limit
    }


@app.get("/api/v1/conversations")
async def get_user_conversations(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取用户会话列表"""
    from sqlalchemy import select, desc
    from src.chatSphere.core.models import Conversation
    
    stmt = select(Conversation).where(
        Conversation.user_id == current_user.id,
        Conversation.is_archived == False
    ).order_by(desc(Conversation.updated_at)).limit(20)
    
    result = await session.execute(stmt)
    conversations = result.scalars().all()
    
    conv_list = []
    for conv in conversations:
        conv_data = {
            "id": conv.id,
            "chat_type": conv.chat_type.value,
            "unread_count": conv.unread_count,
            "is_pinned": conv.is_pinned,
            "is_muted": conv.is_muted,
            "updated_at": conv.updated_at.isoformat()
        }
        
        # 添加聊天对象信息
        if conv.chat_type == ChatType.PRIVATE and conv.other_user:
            conv_data["other_user"] = {
                "id": conv.other_user.id,
                "username": conv.other_user.username,
                "display_name": conv.other_user.display_name,
                "avatar_url": conv.other_user.avatar_url
            }
        elif conv.chat_type == ChatType.GROUP and conv.group:
            conv_data["group"] = {
                "id": conv.group.id,
                "name": conv.group.name,
                "avatar_url": conv.group.avatar_url
            }
        elif conv.chat_type == ChatType.ROOM and conv.room:
            conv_data["room"] = {
                "id": conv.room.id,
                "name": conv.room.name
            }
        
        # 添加最后一条消息
        if conv.last_message:
            conv_data["last_message"] = {
                "content": conv.last_message.content,
                "created_at": conv.last_message.created_at.isoformat(),
                "from_user_id": conv.last_message.from_user_id
            }
        
        conv_list.append(conv_data)
    
    return {"conversations": conv_list}


# 统计信息
@app.get("/api/v1/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db)
):
    """获取系统统计信息"""
    from sqlalchemy import select, func
    
    # 在线用户数
    online_users_count = len(connection_manager.active_connections)
    
    # 总用户数
    total_users_stmt = select(func.count(User.id))
    total_users_result = await session.execute(total_users_stmt)
    total_users = total_users_result.scalar()
    
    # 今日消息数
    today = datetime.utcnow().date()
    today_messages_stmt = select(func.count(Message.id)).where(
        func.date(Message.created_at) == today
    )
    today_messages_result = await session.execute(today_messages_stmt)
    today_messages = today_messages_result.scalar()
    
    # 总消息数
    total_messages_stmt = select(func.count(Message.id))
    total_messages_result = await session.execute(total_messages_stmt)
    total_messages = total_messages_result.scalar()
    
    return {
        "online_users": online_users_count,
        "total_users": total_users,
        "today_messages": today_messages,
        "total_messages": total_messages,
        "server_time": datetime.utcnow().isoformat()
    }


# 包含认证路由
from src.chatSphere.api.routes.auth import router as auth_router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])

# 错误处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(
            message=str(exc.detail),
            code=ResponseCode.INTERNAL_ERROR
        ).dict()
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    response = format_validation_errors(exc.errors())
    return JSONResponse(
        status_code=HTTP_STATUS_MAP[ResponseCode.VALIDATION_ERROR],
        content=response.dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )
