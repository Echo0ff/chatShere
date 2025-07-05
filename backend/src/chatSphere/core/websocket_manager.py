"""
简化版WebSocket连接管理器
"""
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import logging

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .cache import cache_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接：user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 用户信息：user_id -> User
        self.user_sessions: Dict[str, User] = {}
    
    async def connect(self, websocket: WebSocket, user: User, session: AsyncSession):
        """用户连接"""
        # 如果用户已连接，先断开旧连接
        if user.id in self.active_connections:
            await self.force_disconnect(user.id)
        
        # 存储连接
        self.active_connections[user.id] = websocket
        self.user_sessions[user.id] = user
        
        # 更新用户在线状态
        await cache_manager.cache_user_online_status(user.id, True)
        
        # 更新数据库中的最后在线时间
        user.last_seen = datetime.utcnow()
        await session.commit()
        
        logger.info(f"用户 {user.username} ({user.id}) 已连接")
        
        # 发送连接成功消息
        await self.send_to_user(user.id, {
            "type": "connection_established",
            "message": "连接已建立",
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, user_id: str, session: AsyncSession):
        """用户断开连接"""
        if user_id not in self.active_connections:
            return
        
        # 移除连接
        del self.active_connections[user_id]
        user = self.user_sessions.pop(user_id, None)
        
        # 更新缓存中的在线状态
        await cache_manager.cache_user_online_status(user_id, False)
        
        # 更新数据库中的最后在线时间
        if user:
            user.last_seen = datetime.utcnow()
            await session.commit()
        
        logger.info(f"用户 {user_id} 已断开连接")
    
    async def force_disconnect(self, user_id: str):
        """强制断开用户连接"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].close()
            except:
                pass
            del self.active_connections[user_id]
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    async def disconnect_all(self):
        """断开所有连接"""
        for user_id in list(self.active_connections.keys()):
            await self.force_disconnect(user_id)
        
        # 清理缓存
        for user_id in list(self.user_sessions.keys()):
            await cache_manager.cache_user_online_status(user_id, False)
    
    async def send_to_user(self, user_id: str, message: dict) -> bool:
        """发送消息给指定用户"""
        if user_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[user_id]
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"发送消息给用户 {user_id} 失败: {e}")
            # 移除失效连接
            await self.force_disconnect(user_id)
            return False
    
    async def handle_message(self, user_id: str, data: str, session: AsyncSession):
        """处理用户消息"""
        try:
            message_data = json.loads(data)
            message_type = message_data.get("type", "")
            
            # 简化版本：只处理基本消息
            if message_type == "chat":
                await self.handle_chat_message(user_id, message_data)
            elif message_type == "ping":
                await self.handle_ping(user_id)
            else:
                await self.send_to_user(user_id, {
                    "type": "error",
                    "message": f"未知的消息类型: {message_type}"
                })
        
        except json.JSONDecodeError:
            await self.send_to_user(user_id, {
                "type": "error",
                "message": "无效的JSON格式"
            })
        except Exception as e:
            logger.error(f"处理用户 {user_id} 消息失败: {e}")
            await self.send_to_user(user_id, {
                "type": "error",
                "message": "消息处理失败"
            })
    
    async def handle_chat_message(self, user_id: str, message_data: dict):
        """处理聊天消息"""
        content = message_data.get("content", "").strip()
        room_id = message_data.get("room_id", "general")
        
        if not content:
            return
        
        user = self.user_sessions.get(user_id)
        if not user:
            return
        
        # 广播消息给所有在线用户（简化版本）
        broadcast_message = {
            "type": "chat_message",
            "from_user_id": user_id,
            "from_username": user.username,
            "from_display_name": user.display_name,
            "room_id": room_id,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for target_user_id in self.active_connections:
            if target_user_id != user_id:
                await self.send_to_user(target_user_id, broadcast_message)
    
    async def handle_ping(self, user_id: str):
        """处理心跳"""
        await self.send_to_user(user_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def get_online_users(self) -> List[dict]:
        """获取在线用户列表"""
        online_users = []
        for user_id, user in self.user_sessions.items():
            online_users.append({
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url
            })
        
        return online_users
    
    async def cleanup_expired_connections(self):
        """清理过期连接"""
        # 简化版本：暂时不实现
        pass 