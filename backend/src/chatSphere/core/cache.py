"""
Redis 缓存管理
"""
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as redis
from redis.asyncio import Redis

from .config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis缓存管理器"""

    def __init__(self):
        self.redis: Optional[Redis] = None
        self._initialized = False
        self.key_prefix = "chatsphere:"

    async def initialize(self):
        """初始化Redis连接"""
        if self._initialized:
            return

        try:
            self.redis = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True,
            )

            # 测试连接
            await self.redis.ping()
            logger.info("Redis连接已建立")
            self._initialized = True

        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            raise

    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已关闭")
            self._initialized = False

    def _make_key(self, key: str) -> str:
        """生成带前缀的缓存键"""
        return f"{self.key_prefix}{key}"

    # 基础缓存操作
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)

            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (str, int, float, bool)):
                serialized_value = str(value)
            else:
                # 复杂对象使用pickle
                serialized_value = pickle.dumps(value).decode("latin1")

            expire_time = expire or settings.redis_expire_seconds
            return await self.redis.set(cache_key, serialized_value, ex=expire_time)

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """获取缓存"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            value = await self.redis.get(cache_key)

            if value is None:
                return default

            # 尝试反序列化
            try:
                # 首先尝试JSON
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                try:
                    # 然后尝试pickle
                    return pickle.loads(value.encode("latin1"))
                except:
                    # 最后返回原始字符串
                    return value

        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            return bool(await self.redis.delete(cache_key))
        except Exception as e:
            logger.error(f"删除缓存失败 {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            return bool(await self.redis.exists(cache_key))
        except Exception as e:
            logger.error(f"检查缓存失败 {key}: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """设置缓存过期时间"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            return bool(await self.redis.expire(cache_key, seconds))
        except Exception as e:
            logger.error(f"设置缓存过期时间失败 {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """自增缓存值"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            return await self.redis.incrby(cache_key, amount)
        except Exception as e:
            logger.error(f"自增缓存失败 {key}: {e}")
            return 0

    # 列表操作
    async def list_push(self, key: str, *values: Any) -> int:
        """向列表推送元素"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                for v in values
            ]
            return await self.redis.lpush(cache_key, *serialized_values)
        except Exception as e:
            logger.error(f"列表推送失败 {key}: {e}")
            return 0

    async def list_pop(self, key: str) -> Any:
        """从列表弹出元素"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            value = await self.redis.rpop(cache_key)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"列表弹出失败 {key}: {e}")
            return None

    async def list_range(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表范围"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            values = await self.redis.lrange(cache_key, start, end)
            result = []
            for value in values:
                try:
                    result.append(json.loads(value))
                except:
                    result.append(value)
            return result
        except Exception as e:
            logger.error(f"获取列表范围失败 {key}: {e}")
            return []

    # 集合操作
    async def set_add(self, key: str, *members: Any) -> int:
        """向集合添加成员"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            serialized_members = [
                json.dumps(m, ensure_ascii=False) if isinstance(m, (dict, list)) else str(m)
                for m in members
            ]
            return await self.redis.sadd(cache_key, *serialized_members)
        except Exception as e:
            logger.error(f"集合添加失败 {key}: {e}")
            return 0

    async def set_remove(self, key: str, *members: Any) -> int:
        """从集合移除成员"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            serialized_members = [
                json.dumps(m, ensure_ascii=False) if isinstance(m, (dict, list)) else str(m)
                for m in members
            ]
            return await self.redis.srem(cache_key, *serialized_members)
        except Exception as e:
            logger.error(f"集合移除失败 {key}: {e}")
            return 0

    async def set_members(self, key: str) -> List[Any]:
        """获取集合所有成员"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            members = await self.redis.smembers(cache_key)
            result = []
            for member in members:
                try:
                    result.append(json.loads(member))
                except:
                    result.append(member)
            return result
        except Exception as e:
            logger.error(f"获取集合成员失败 {key}: {e}")
            return []

    # 哈希操作
    async def hash_set(self, key: str, field: str, value: Any) -> bool:
        """设置哈希字段"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            serialized_value = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, (dict, list))
                else str(value)
            )
            return bool(await self.redis.hset(cache_key, field, serialized_value))
        except Exception as e:
            logger.error(f"设置哈希字段失败 {key}.{field}: {e}")
            return False

    async def hash_get(self, key: str, field: str) -> Any:
        """获取哈希字段"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            value = await self.redis.hget(cache_key, field)
            if value:
                try:
                    return json.loads(value)
                except:
                    return value
            return None
        except Exception as e:
            logger.error(f"获取哈希字段失败 {key}.{field}: {e}")
            return None

    async def hash_get_all(self, key: str) -> Dict[str, Any]:
        """获取哈希所有字段"""
        if not self.redis:
            await self.initialize()

        try:
            cache_key = self._make_key(key)
            values = await self.redis.hgetall(cache_key)
            result = {}
            for field, value in values.items():
                try:
                    result[field] = json.loads(value)
                except:
                    result[field] = value
            return result
        except Exception as e:
            logger.error(f"获取哈希所有字段失败 {key}: {e}")
            return {}


class ChatCacheManager(CacheManager):
    """聊天相关的缓存管理器"""

    # 用户相关缓存
    async def cache_user_session(self, user_id: str, session_data: dict, expire: int = 3600):
        """缓存用户会话"""
        return await self.set(f"user_session:{user_id}", session_data, expire)

    async def get_user_session(self, user_id: str) -> Optional[dict]:
        """获取用户会话"""
        return await self.get(f"user_session:{user_id}")

    async def delete_user_session(self, user_id: str):
        """删除用户会话"""
        return await self.delete(f"user_session:{user_id}")

    async def cache_user_online_status(self, user_id: str, is_online: bool = True):
        """缓存用户在线状态"""
        key = f"user_online:{user_id}"
        if is_online:
            return await self.set(key, "online", expire=settings.websocket_timeout + 30)
        else:
            return await self.delete(key)

    async def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return await self.exists(f"user_online:{user_id}")

    # 房间相关缓存
    async def add_user_to_room(self, room_id: str, user_id: str):
        """将用户添加到房间"""
        return await self.set_add(f"room_users:{room_id}", user_id)

    async def remove_user_from_room(self, room_id: str, user_id: str):
        """从房间移除用户"""
        return await self.set_remove(f"room_users:{room_id}", user_id)

    async def get_room_users(self, room_id: str) -> List[str]:
        """获取房间用户列表"""
        return await self.set_members(f"room_users:{room_id}")

    async def cache_room_info(self, room_id: str, room_data: dict):
        """缓存房间信息"""
        return await self.set(f"room_info:{room_id}", room_data, expire=1800)

    async def get_room_info(self, room_id: str) -> Optional[dict]:
        """获取房间信息"""
        return await self.get(f"room_info:{room_id}")

    # 消息相关缓存
    async def cache_recent_messages(self, chat_key: str, messages: List[dict], expire: int = 600):
        """缓存最近消息"""
        return await self.set(f"recent_messages:{chat_key}", messages, expire)

    async def get_recent_messages(self, chat_key: str) -> List[dict]:
        """获取最近消息"""
        return await self.get(f"recent_messages:{chat_key}", [])

    async def cache_unread_count(self, user_id: str, count: int):
        """缓存未读消息数量"""
        return await self.set(f"unread_count:{user_id}", count, expire=86400)

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读消息数量"""
        return await self.get(f"unread_count:{user_id}", 0)

    async def increment_unread_count(self, user_id: str) -> int:
        """增加未读消息数量"""
        return await self.increment(f"unread_count:{user_id}")

    # 速率限制
    async def check_rate_limit(
        self, user_id: str, action: str, limit: int = 10, window: int = 60
    ) -> bool:
        """检查速率限制"""
        key = f"rate_limit:{action}:{user_id}"
        current = await self.increment(key)

        if current == 1:
            await self.expire(key, window)

        return current <= limit

    # JWT token 黑名单
    async def blacklist_token(self, token_jti: str, expire: int = None):
        """将JWT token加入黑名单"""
        expire_time = expire or settings.access_token_expire_minutes * 60
        return await self.set(f"blacklist_token:{token_jti}", "1", expire_time)

    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """检查token是否在黑名单"""
        return await self.exists(f"blacklist_token:{token_jti}")

    # 验证码缓存
    async def cache_verification_code(self, email: str, code: str, expire: int = 300):
        """缓存验证码"""
        return await self.set(f"verification_code:{email}", code, expire)

    async def get_verification_code(self, email: str) -> Optional[str]:
        """获取验证码"""
        return await self.get(f"verification_code:{email}")

    async def delete_verification_code(self, email: str):
        """删除验证码"""
        return await self.delete(f"verification_code:{email}")


# 全局缓存管理器实例
cache_manager = ChatCacheManager()


# 健康检查函数
async def check_redis_health() -> dict:
    """检查Redis健康状态"""
    try:
        if not cache_manager.redis:
            await cache_manager.initialize()

        await cache_manager.redis.ping()
        info = await cache_manager.redis.info()

        return {
            "status": "healthy",
            "redis": "connected",
            "version": info.get("redis_version", "unknown"),
            "used_memory": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
        }
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}
