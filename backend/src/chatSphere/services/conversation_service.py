"""
会话服务模块
处理会话更新、未读消息数管理等
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..core.models import Conversation, ChatType, user_group_association, user_room_association

logger = logging.getLogger(__name__)


async def update_conversation_with_new_message(
    session: AsyncSession,
    from_user_id: str,
    chat_type: str,
    chat_id: str,
    message_id: int
):
    """更新会话信息，包括最后消息和未读数"""
    try:
        conv_type = ChatType(chat_type)
        
        # 获取所有相关用户（需要更新他们的会话记录）
        relevant_users = []
        
        if chat_type == "private":
            # 私聊：发送者和接收者
            relevant_users = [from_user_id, chat_id]
        elif chat_type == "group":
            # 群组：所有成员
            stmt = select(user_group_association.c.user_id).where(
                user_group_association.c.group_id == chat_id
            )
            result = await session.execute(stmt)
            relevant_users = [row[0] for row in result.fetchall()]
        else:  # room
            # 房间：为所有在线用户创建/更新会话记录
            # 从缓存中获取当前房间的所有在线用户
            try:
                from ..core.cache_manager import cache_manager
                online_room_users = await cache_manager.get_room_users(chat_id)
                relevant_users = online_room_users
                
                # 确保发送者在列表中
                if from_user_id not in relevant_users:
                    relevant_users.append(from_user_id)
                    
                logger.info(f"房间 {chat_id} 在线用户: {relevant_users}")
                
            except Exception as e:
                logger.warning(f"获取房间在线用户失败，回退到现有会话用户: {e}")
                # 回退方案：只更新现有会话记录的用户
                stmt = select(Conversation.user_id).where(
                    Conversation.room_id == chat_id,
                    Conversation.chat_type == ChatType.ROOM
                ).distinct()
                result = await session.execute(stmt)
                existing_users = [row[0] for row in result.fetchall()]
                
                # 如果发送者没有会话记录，也要包含进来
                if from_user_id not in existing_users:
                    existing_users.append(from_user_id)
                
                relevant_users = existing_users
        
        # 为每个用户更新或创建会话记录
        for user_id in relevant_users:
            stmt = select(Conversation).where(
                Conversation.user_id == user_id,
                Conversation.chat_type == conv_type
            )
            
            if chat_type == "private":
                other_user_id = chat_id if user_id == from_user_id else from_user_id
                stmt = stmt.where(Conversation.other_user_id == other_user_id)
            elif chat_type == "group":
                stmt = stmt.where(Conversation.group_id == chat_id)
            else:  # room
                stmt = stmt.where(Conversation.room_id == chat_id)
            
            result = await session.execute(stmt)
            conversation = result.scalar_one_or_none()
            
            if conversation:
                # 更新现有会话
                conversation.last_message_id = message_id
                conversation.updated_at = func.now()
                # 如果不是发送者，未读数+1
                if user_id != from_user_id:
                    conversation.unread_count += 1
            else:
                # 创建新会话
                new_conv = Conversation(
                    user_id=user_id,
                    chat_type=conv_type,
                    last_message_id=message_id,
                    unread_count=0 if user_id == from_user_id else 1
                )
                
                if chat_type == "private":
                    other_user_id = chat_id if user_id == from_user_id else from_user_id
                    new_conv.other_user_id = other_user_id
                elif chat_type == "group":
                    new_conv.group_id = chat_id
                else:  # room
                    new_conv.room_id = chat_id
                
                session.add(new_conv)
        
        await session.commit()
        logger.info(f"会话信息更新成功: {chat_type}:{chat_id}, 消息:{message_id}")
        
    except Exception as e:
        logger.error(f"更新会话信息失败: {e}")
        await session.rollback()
        raise


async def mark_conversation_as_read(
    session: AsyncSession,
    user_id: str,
    chat_type: str,
    chat_id: str
):
    """标记会话为已读，清零未读数"""
    try:
        conv_type = ChatType(chat_type)
        
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.chat_type == conv_type
        )
        
        if chat_type == "private":
            stmt = stmt.where(Conversation.other_user_id == chat_id)
        elif chat_type == "group":
            stmt = stmt.where(Conversation.group_id == chat_id)
        else:  # room
            stmt = stmt.where(Conversation.room_id == chat_id)
        
        result = await session.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if conversation and conversation.unread_count > 0:
            conversation.unread_count = 0
            conversation.updated_at = func.now()
            await session.commit()
            logger.info(f"会话标记为已读: {user_id}, {chat_type}:{chat_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"标记会话已读失败: {e}")
        await session.rollback()
        raise


async def get_user_conversations_with_details(
    session: AsyncSession,
    user_id: str,
    limit: int = 20
):
    """获取用户的会话列表，包含详细信息"""
    from ..core.models import User, Group, Room, Message
    
    try:
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.is_archived == False
        ).order_by(Conversation.updated_at.desc()).limit(limit)
        
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
                "updated_at": conv.updated_at.isoformat(),
                "name": "",  # 会话显示名称
                "chat_id": "",  # 实际的聊天ID
            }
            
            # 添加聊天对象信息和名称
            if conv.chat_type == ChatType.PRIVATE and conv.other_user_id:
                # 获取对方用户信息
                user_stmt = select(User).where(User.id == conv.other_user_id)
                user_result = await session.execute(user_stmt)
                other_user = user_result.scalar_one_or_none()
                
                if other_user:
                    conv_data["chat_id"] = other_user.id
                    conv_data["name"] = other_user.display_name or other_user.username
                    conv_data["other_user"] = {
                        "id": other_user.id,
                        "username": other_user.username,
                        "display_name": other_user.display_name,
                        "avatar_url": other_user.avatar_url
                    }
                    
            elif conv.chat_type == ChatType.GROUP and conv.group_id:
                # 获取群组信息
                group_stmt = select(Group).where(Group.id == conv.group_id)
                group_result = await session.execute(group_stmt)
                group = group_result.scalar_one_or_none()
                
                if group:
                    conv_data["chat_id"] = group.id
                    conv_data["name"] = group.name
                    conv_data["group"] = {
                        "id": group.id,
                        "name": group.name,
                        "avatar_url": group.avatar_url
                    }
                    
            elif conv.chat_type == ChatType.ROOM and conv.room_id:
                # 获取房间信息
                room_stmt = select(Room).where(Room.id == conv.room_id)
                room_result = await session.execute(room_stmt)
                room = room_result.scalar_one_or_none()
                
                if room:
                    conv_data["chat_id"] = room.id
                    conv_data["name"] = room.name
                    conv_data["room"] = {
                        "id": room.id,
                        "name": room.name
                    }
            
            # 添加最后一条消息
            if conv.last_message_id:
                msg_stmt = select(Message).where(Message.id == conv.last_message_id)
                msg_result = await session.execute(msg_stmt)
                last_message = msg_result.scalar_one_or_none()
                
                if last_message:
                    conv_data["last_message"] = {
                        "content": last_message.content,
                        "created_at": last_message.created_at.isoformat(),
                        "from_user_id": last_message.from_user_id,
                        "message_type": last_message.message_type.value
                    }
            
            # 只添加有效的会话（有名称的）
            if conv_data["name"]:
                conv_list.append(conv_data)
        
        return conv_list
        
    except Exception as e:
        logger.error(f"获取用户会话列表失败: {e}")
        raise 