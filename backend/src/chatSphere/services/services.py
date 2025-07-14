import uuid
from datetime import datetime
from typing import Dict, List, Optional


class ChatRoom:
    """聊天室数据模型"""

    def __init__(self, room_id: str, name: str, description: str = ""):
        self.room_id = room_id
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.users: set = set()

    def add_user(self, user_id: str):
        """添加用户到房间"""
        self.users.add(user_id)

    def remove_user(self, user_id: str):
        """从房间移除用户"""
        self.users.discard(user_id)

    def get_user_count(self) -> int:
        """获取房间用户数量"""
        return len(self.users)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "user_count": len(self.users),
        }


class Message:
    """消息数据模型"""

    def __init__(
        self, user_id: str, username: str, content: str, room_id: str, message_type: str = "chat"
    ):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.username = username
        self.content = content
        self.room_id = room_id
        self.message_type = message_type
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "type": self.message_type,
            "user_id": self.user_id,
            "username": self.username,
            "content": self.content,
            "room_id": self.room_id,
            "timestamp": self.timestamp.isoformat(),
        }


class ChatService:
    """聊天服务类"""

    def __init__(self):
        self.rooms: Dict[str, ChatRoom] = {}
        self.message_history: Dict[str, List[Message]] = {}
        self._init_default_rooms()

    def _init_default_rooms(self):
        """初始化默认聊天室"""
        default_rooms = [
            ("general", "大厅", "欢迎来到聊天室大厅！"),
            ("tech", "技术讨论", "讨论技术相关话题"),
            ("random", "随便聊聊", "随意聊天的地方"),
        ]

        for room_id, name, description in default_rooms:
            self.create_room(room_id, name, description)

    def create_room(self, room_id: str, name: str, description: str = "") -> ChatRoom:
        """创建聊天室"""
        room = ChatRoom(room_id, name, description)
        self.rooms[room_id] = room
        self.message_history[room_id] = []
        return room

    def get_room(self, room_id: str) -> Optional[ChatRoom]:
        """获取聊天室"""
        return self.rooms.get(room_id)

    def get_all_rooms(self) -> List[dict]:
        """获取所有聊天室"""
        return [room.to_dict() for room in self.rooms.values()]

    def add_message(self, message: Message):
        """添加消息到历史记录"""
        room_id = message.room_id
        if room_id not in self.message_history:
            self.message_history[room_id] = []

        self.message_history[room_id].append(message)

        # 保持最近100条消息
        if len(self.message_history[room_id]) > 100:
            self.message_history[room_id] = self.message_history[room_id][-100:]

    def get_recent_messages(self, room_id: str, limit: int = 50) -> List[dict]:
        """获取房间最近的消息"""
        if room_id not in self.message_history:
            return []

        messages = self.message_history[room_id][-limit:]
        return [msg.to_dict() for msg in messages]


# 创建全局服务实例
chat_service = ChatService()
