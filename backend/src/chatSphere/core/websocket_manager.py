"""
简化版WebSocket连接管理器
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import cache_manager
from .models import User

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
        await self.send_to_user(
            user.id,
            {
                "type": "connection_established",
                "data": {
                    "message": "连接已建立",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "display_name": user.display_name,
                        "avatar_url": user.avatar_url,
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        # 自动将用户加入默认房间
        try:
            await cache_manager.add_user_to_room("general", user.id)
            logger.info(f"用户 {user.id} 已自动加入默认房间 general")
        except Exception as e:
            logger.error(f"添加用户到默认房间失败: {e}")

        # 广播在线用户列表给所有用户
        await self.broadcast_online_users()

    async def disconnect(self, user_id: str, session: AsyncSession):
        """用户断开连接"""
        if user_id not in self.active_connections:
            return

        # 移除连接
        del self.active_connections[user_id]
        user = self.user_sessions.pop(user_id, None)

        # 更新缓存中的在线状态
        await cache_manager.cache_user_online_status(user_id, False)

        # 从所有房间中移除用户（从默认房间开始）
        try:
            await cache_manager.remove_user_from_room("general", user_id)
            logger.info(f"用户 {user_id} 已从默认房间移除")
        except Exception as e:
            logger.error(f"从房间移除用户失败: {e}")

        # 更新数据库中的最后在线时间
        if user:
            user.last_seen = datetime.utcnow()
            await session.commit()

        logger.info(f"用户 {user_id} 已断开连接")

        # 广播在线用户列表给剩余用户
        await self.broadcast_online_users()

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

            logger.info(f"收到用户 {user_id} 的消息: {message_data}")

            # 处理不同类型的消息
            if message_type == "send_message":
                await self.handle_send_message(user_id, message_data, session)
            elif message_type == "chat":  # 保持向后兼容
                await self.handle_chat_message(user_id, message_data)
            elif message_type == "join_room":
                await self.handle_join_room(user_id, message_data)
            elif message_type == "leave_room":
                await self.handle_leave_room(user_id, message_data)
            elif message_type == "typing":
                await self.handle_typing(user_id, message_data)
            elif message_type == "ping":
                await self.handle_ping(user_id)
            else:
                await self.send_to_user(
                    user_id, {"type": "error", "data": {"message": f"未知的消息类型: {message_type}"}}
                )

        except json.JSONDecodeError:
            await self.send_to_user(user_id, {"type": "error", "data": {"message": "无效的JSON格式"}})
        except Exception as e:
            logger.error(f"处理用户 {user_id} 消息失败: {e}")
            await self.send_to_user(user_id, {"type": "error", "data": {"message": "消息处理失败"}})

    async def handle_send_message(self, user_id: str, message_data: dict, session: AsyncSession):
        """处理前端发送的消息"""
        data = message_data.get("data", {})
        content = data.get("content", "").strip()
        chat_type = data.get("chat_type", "room")
        chat_id = data.get("chat_id", "general")
        message_type = data.get("message_type", "text")
        reply_to_id = data.get("reply_to_id")

        if not content:
            return

        user = self.user_sessions.get(user_id)
        if not user:
            return

        try:
            # 保存消息到数据库
            from .models import ChatType, Message, MessageType

            # 确定消息类型和目标
            db_message = Message(
                from_user_id=user_id,
                content=content,
                message_type=MessageType.TEXT if message_type == "text" else MessageType.IMAGE,
                chat_type=ChatType.ROOM
                if chat_type == "room"
                else (ChatType.PRIVATE if chat_type == "private" else ChatType.GROUP),
                reply_to_id=reply_to_id,
            )

            # 根据聊天类型设置目标
            if chat_type == "private":
                db_message.to_user_id = chat_id
            elif chat_type == "room":
                db_message.room_id = chat_id
            elif chat_type == "group":
                db_message.group_id = chat_id

            session.add(db_message)
            await session.commit()
            await session.refresh(db_message)

            logger.info(f"消息已保存到数据库: {db_message.id}")

            # 更新会话信息（未读数等）
            try:
                from ..services.conversation_service import update_conversation_with_new_message

                await update_conversation_with_new_message(
                    session, user_id, chat_type, chat_id, db_message.id
                )
            except Exception as e:
                logger.error(f"更新会话信息失败: {e}")

            # 创建消息对象用于广播，包含房间信息
            message_obj = {
                "id": str(db_message.id),
                "from_user_id": user_id,
                "content": content,
                "message_type": message_type,
                "created_at": db_message.created_at.isoformat(),
                "is_edited": False,
                "reply_to_id": reply_to_id,
                "chat_type": chat_type,
                "chat_id": chat_id,
                "room_id": chat_id if chat_type == "room" else None,
                "to_user_id": chat_id if chat_type == "private" else None,
                "group_id": chat_id if chat_type == "group" else None,
            }

            # 构建广播消息
            broadcast_message = {
                "type": "message",
                "data": message_obj,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"广播消息: {broadcast_message}")

            # 根据聊天类型选择性广播
            target_users_for_broadcast = []
            if chat_type == "room":
                # 房间消息：广播给所有在线用户（房间是公开的）
                target_users_for_broadcast = list(self.active_connections.keys())
                for target_user_id in target_users_for_broadcast:
                    await self.send_to_user(target_user_id, broadcast_message)
            elif chat_type == "private":
                # 私聊消息：只发送给发送者和接收者
                target_users_for_broadcast = [user_id, chat_id]  # chat_id是接收者的用户ID
                for target_user_id in target_users_for_broadcast:
                    if target_user_id in self.active_connections:
                        await self.send_to_user(target_user_id, broadcast_message)
            elif chat_type == "group":
                # 群组消息：TODO - 需要查询群组成员，暂时广播给所有人
                target_users_for_broadcast = list(self.active_connections.keys())
                for target_user_id in target_users_for_broadcast:
                    await self.send_to_user(target_user_id, broadcast_message)

            # 广播会话更新通知，让相关用户刷新会话列表
            conversation_update_message = {
                "type": "conversation_updated",
                "data": {
                    "chat_type": chat_type,
                    "chat_id": chat_id,
                    "message_id": str(db_message.id),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"广播会话更新通知: {conversation_update_message}")

            # 向相关用户发送会话更新通知
            for target_user_id in target_users_for_broadcast:
                if target_user_id in self.active_connections:
                    await self.send_to_user(target_user_id, conversation_update_message)

        except Exception as e:
            logger.error(f"保存消息到数据库失败: {e}")
            # 发送错误消息给用户
            await self.send_to_user(user_id, {"type": "error", "data": {"message": "消息发送失败，请重试"}})

    async def handle_chat_message(self, user_id: str, message_data: dict):
        """处理聊天消息（旧格式，保持兼容性）"""
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
            "timestamp": datetime.utcnow().isoformat(),
        }

        for target_user_id in self.active_connections:
            if target_user_id != user_id:
                await self.send_to_user(target_user_id, broadcast_message)

    async def handle_join_room(self, user_id: str, message_data: dict):
        """处理加入房间"""
        data = message_data.get("data", {})
        room_id = data.get("room_id", "general")

        user = self.user_sessions.get(user_id)
        if not user:
            return

        # 将用户添加到房间缓存中
        try:
            await cache_manager.add_user_to_room(room_id, user_id)
            logger.info(f"用户 {user_id} 已加入房间 {room_id}")
        except Exception as e:
            logger.error(f"添加用户到房间缓存失败: {e}")

        # 广播用户加入消息
        join_message = {
            "type": "user_joined",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "display_name": user.display_name,
                "room_id": room_id,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        for target_user_id in self.active_connections:
            if target_user_id != user_id:
                await self.send_to_user(target_user_id, join_message)

    async def handle_leave_room(self, user_id: str, message_data: dict):
        """处理离开房间"""
        data = message_data.get("data", {})
        room_id = data.get("room_id", "general")

        user = self.user_sessions.get(user_id)
        if not user:
            return

        # 从房间缓存中移除用户
        try:
            await cache_manager.remove_user_from_room(room_id, user_id)
            logger.info(f"用户 {user_id} 已离开房间 {room_id}")
        except Exception as e:
            logger.error(f"从房间缓存移除用户失败: {e}")

        # 广播用户离开消息
        leave_message = {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "display_name": user.display_name,
                "room_id": room_id,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        for target_user_id in self.active_connections:
            if target_user_id != user_id:
                await self.send_to_user(target_user_id, leave_message)

    async def handle_typing(self, user_id: str, message_data: dict):
        """处理打字状态"""
        data = message_data.get("data", {})
        is_typing = data.get("is_typing", False)
        chat_id = data.get("chat_id", "general")

        user = self.user_sessions.get(user_id)
        if not user:
            return

        # 广播打字状态
        typing_message = {
            "type": "typing",
            "data": {
                "user_id": user_id,
                "username": user.username,
                "display_name": user.display_name,
                "is_typing": is_typing,
                "chat_id": chat_id,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        for target_user_id in self.active_connections:
            if target_user_id != user_id:
                await self.send_to_user(target_user_id, typing_message)

    async def handle_ping(self, user_id: str):
        """处理心跳"""
        await self.send_to_user(
            user_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
        )

    async def get_online_users(self) -> List[dict]:
        """获取在线用户列表"""
        online_users = []
        for user_id, user in self.user_sessions.items():
            online_users.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url,
                }
            )

        return online_users

    async def broadcast_online_users(self):
        """广播在线用户列表"""
        online_users = await self.get_online_users()

        message = {
            "type": "online_users",
            "data": online_users,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for user_id in self.active_connections:
            await self.send_to_user(user_id, message)

    async def cleanup_expired_connections(self):
        """清理过期连接"""
        # 简化版本：暂时不实现
        pass
