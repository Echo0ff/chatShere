"""
ChatSphere 数据库模型
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserStatus(str, enum.Enum):
    """用户状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"
    DELETED = "deleted"


class MessageType(str, enum.Enum):
    """消息类型枚举"""

    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    EMOJI = "emoji"


class ChatType(str, enum.Enum):
    """聊天类型枚举"""

    PRIVATE = "private"
    GROUP = "group"
    ROOM = "room"


class OAuthProvider(str, enum.Enum):
    """OAuth提供商枚举"""

    GOOGLE = "google"
    GITHUB = "github"
    LOCAL = "local"


# 多对多关系表：用户-房间
user_room_association = Table(
    "user_rooms",
    Base.metadata,
    Column("user_id", String(50), ForeignKey("users.id", ondelete="CASCADE")),
    Column("room_id", String(50), ForeignKey("rooms.id", ondelete="CASCADE")),
    Column("joined_at", DateTime, default=func.now()),
    Column("is_admin", Boolean, default=False),
    UniqueConstraint("user_id", "room_id", name="unique_user_room"),
)

# 多对多关系表：用户-群组
user_group_association = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", String(50), ForeignKey("users.id", ondelete="CASCADE")),
    Column("group_id", String(50), ForeignKey("groups.id", ondelete="CASCADE")),
    Column("joined_at", DateTime, default=func.now()),
    Column("is_admin", Boolean, default=False),
    Column("is_owner", Boolean, default=False),
    UniqueConstraint("user_id", "group_id", name="unique_user_group"),
)


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(String(50), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)

    # 认证信息
    hashed_password = Column(String(255), nullable=True)  # OAuth用户可能没有密码
    oauth_provider = Column(Enum(OAuthProvider), default=OAuthProvider.LOCAL)
    oauth_id = Column(String(255), nullable=True)

    # 用户信息
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)

    # 设置
    is_verified = Column(Boolean, default=False)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_seen = Column(DateTime, nullable=True)

    # 关系
    sent_messages = relationship(
        "Message", foreign_keys="Message.from_user_id", back_populates="sender"
    )
    received_messages = relationship("MessageReadStatus", back_populates="user")
    rooms = relationship("Room", secondary=user_room_association, back_populates="members")
    groups = relationship("Group", secondary=user_group_association, back_populates="members")
    owned_groups = relationship("Group", back_populates="owner")
    refresh_tokens = relationship("RefreshToken", back_populates="user")

    # 索引
    __table_args__ = (
        Index("idx_user_email_status", "email", "status"),
        Index("idx_user_oauth", "oauth_provider", "oauth_id"),
        Index("idx_user_created", "created_at"),
    )


class RefreshToken(Base):
    """刷新令牌模型"""

    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    # 关系
    user = relationship("User", back_populates="refresh_tokens")


class Room(Base):
    """房间模型"""

    __tablename__ = "rooms"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # 房间设置
    is_public = Column(Boolean, default=True)
    is_temporary = Column(Boolean, default=False)
    max_members = Column(Integer, default=100)
    require_approval = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    members = relationship("User", secondary=user_room_association, back_populates="rooms")
    messages = relationship("Message", back_populates="room")


class Group(Base):
    """群组模型"""

    __tablename__ = "groups"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # 群组设置
    is_private = Column(Boolean, default=False)
    require_approval = Column(Boolean, default=True)
    max_members = Column(Integer, default=500)

    # 创建者
    owner_id = Column(String(50), ForeignKey("users.id"), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="owned_groups")
    members = relationship("User", secondary=user_group_association, back_populates="groups")
    messages = relationship("Message", back_populates="group")


class Message(Base):
    """消息模型"""

    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 发送者
    from_user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 接收者（私聊、群聊、房间）
    to_user_id = Column(String(50), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    group_id = Column(String(50), ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    room_id = Column(String(50), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)

    # 消息内容
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    chat_type = Column(Enum(ChatType), nullable=False)

    # 附件信息
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(BigInteger, nullable=True)

    # 回复消息
    reply_to_id = Column(BigInteger, ForeignKey("messages.id"), nullable=True)

    # 消息状态
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    sender = relationship("User", foreign_keys=[from_user_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[to_user_id])
    group = relationship("Group", back_populates="messages")
    room = relationship("Room", back_populates="messages")
    reply_to = relationship("Message", remote_side=[id])
    read_status = relationship("MessageReadStatus", back_populates="message")

    # 索引
    __table_args__ = (
        Index("idx_message_from_user", "from_user_id", "created_at"),
        Index("idx_message_to_user", "to_user_id", "created_at"),
        Index("idx_message_group", "group_id", "created_at"),
        Index("idx_message_room", "room_id", "created_at"),
        Index("idx_message_chat_type", "chat_type", "created_at"),
    )


class MessageReadStatus(Base):
    """消息读取状态模型"""

    __tablename__ = "message_read_status"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 状态
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)

    # 时间戳
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # 关系
    message = relationship("Message", back_populates="read_status")
    user = relationship("User", back_populates="received_messages")

    # 约束
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="unique_message_user_read"),
        Index("idx_read_status_user_unread", "user_id", "is_read"),
        Index("idx_read_status_message", "message_id"),
    )


class Conversation(Base):
    """会话模型（用于聊天列表）"""

    __tablename__ = "conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 会话对象
    other_user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    group_id = Column(String(50), ForeignKey("groups.id", ondelete="CASCADE"), nullable=True)
    room_id = Column(String(50), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=True)

    # 会话信息
    chat_type = Column(Enum(ChatType), nullable=False)
    last_message_id = Column(BigInteger, ForeignKey("messages.id"), nullable=True)
    unread_count = Column(Integer, default=0)

    # 会话设置
    is_muted = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", foreign_keys=[user_id])
    other_user = relationship("User", foreign_keys=[other_user_id])
    group = relationship("Group")
    room = relationship("Room")
    last_message = relationship("Message")

    # 约束和索引
    __table_args__ = (
        Index("idx_conversation_user_updated", "user_id", "updated_at"),
        Index("idx_conversation_type", "chat_type"),
    )


class UserSession(Base):
    """用户会话模型（WebSocket连接跟踪）"""

    __tablename__ = "user_sessions"

    id = Column(String(255), primary_key=True)  # 会话ID
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 连接信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    # 关系
    user = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_session_user_active", "user_id", "is_active"),
        Index("idx_session_expires", "expires_at"),
    )
