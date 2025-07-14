#!/usr/bin/env python3
"""
WebSocket 测试客户端
用于测试聊天室功能
"""

import asyncio
import json
import sys
from datetime import datetime

import websockets


class ChatClient:
    def __init__(self, user_id: str, username: str, room_id: str = "general"):
        self.user_id = user_id
        self.username = username
        self.room_id = room_id
        self.websocket = None

    async def connect(self, host: str = "localhost", port: int = 8000):
        """连接到聊天服务器"""
        uri = (
            f"ws://{host}:{port}/ws/{self.user_id}?username={self.username}&room_id={self.room_id}"
        )
        print(f"🔌 连接到: {uri}")

        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ 成功连接！用户: {self.username}, 房间: {self.room_id}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    async def send_message(self, content: str):
        """发送聊天消息"""
        if not self.websocket:
            print("❌ 未连接到服务器")
            return

        message = {"type": "chat", "content": content}

        try:
            await self.websocket.send(json.dumps(message))
        except Exception as e:
            print(f"❌ 发送消息失败: {e}")

    async def listen(self):
        """监听服务器消息"""
        if not self.websocket:
            return

        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 连接已断开")
        except Exception as e:
            print(f"❌ 接收消息时出错: {e}")

    async def handle_message(self, data: dict):
        """处理接收到的消息"""
        msg_type = data.get("type", "unknown")
        timestamp = data.get("timestamp", "")

        if msg_type == "chat":
            username = data.get("username", "Unknown")
            content = data.get("content", "")
            print(f"💬 [{timestamp}] {username}: {content}")

        elif msg_type == "welcome":
            message = data.get("message", "")
            users_count = data.get("users_count", 0)
            print(f"🎉 {message} (当前在线: {users_count})")

        elif msg_type == "user_joined":
            username = data.get("username", "")
            users_count = data.get("users_count", 0)
            print(f"📥 {username} 加入了聊天室 (当前在线: {users_count})")

        elif msg_type == "user_left":
            username = data.get("username", "")
            users_count = data.get("users_count", 0)
            print(f"📤 {username} 离开了聊天室 (当前在线: {users_count})")

        else:
            print(f"📨 [{msg_type}] {data}")

    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()


async def main():
    if len(sys.argv) < 3:
        print("用法: python test_client.py <user_id> <username> [room_id]")
        print("示例: python test_client.py user123 张三 general")
        return

    user_id = sys.argv[1]
    username = sys.argv[2]
    room_id = sys.argv[3] if len(sys.argv) > 3 else "general"

    client = ChatClient(user_id, username, room_id)

    if await client.connect():
        # 启动消息监听任务
        listen_task = asyncio.create_task(client.listen())

        print("\n💡 输入消息并按回车发送，输入 'quit' 退出")
        print("=" * 50)

        try:
            while True:
                # 读取用户输入
                message = await asyncio.get_event_loop().run_in_executor(None, input, "")

                if message.lower() in ["quit", "exit", "q"]:
                    break

                if message.strip():
                    await client.send_message(message)

        except KeyboardInterrupt:
            pass

        finally:
            print("\n👋 正在断开连接...")
            listen_task.cancel()
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
