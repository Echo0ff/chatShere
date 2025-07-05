#!/usr/bin/env python3
"""
ChatSphere 初始化脚本
自动创建测试用户和基础数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database import db_manager
from auth import auth_manager
from models import User, Room, OAuthProvider
from cache import cache_manager


async def create_test_users():
    """创建测试用户"""
    print("🔄 创建测试用户...")
    
    async with db_manager.get_session() as session:
        # 管理员用户
        admin_user = await auth_manager.create_user(
            session=session,
            email="admin@chatsphere.com",
            username="admin",
            display_name="管理员",
            password="admin123",
            oauth_provider=OAuthProvider.LOCAL
        )
        print(f"✅ 创建管理员用户: {admin_user.username}")
        
        # 测试用户1
        test_user1 = await auth_manager.create_user(
            session=session,
            email="alice@example.com",
            username="alice",
            display_name="Alice",
            password="password123",
            oauth_provider=OAuthProvider.LOCAL
        )
        print(f"✅ 创建测试用户: {test_user1.username}")
        
        # 测试用户2
        test_user2 = await auth_manager.create_user(
            session=session,
            email="bob@example.com",
            username="bob",
            display_name="Bob",
            password="password123",
            oauth_provider=OAuthProvider.LOCAL
        )
        print(f"✅ 创建测试用户: {test_user2.username}")


async def create_default_rooms():
    """创建默认房间"""
    print("🔄 创建默认房间...")
    
    async with db_manager.get_session() as session:
        rooms_data = [
            {
                "id": "general",
                "name": "大厅",
                "description": "欢迎来到 ChatSphere！这里是公共聊天区域。",
                "is_public": True,
                "max_members": 1000
            },
            {
                "id": "tech",
                "name": "技术讨论",
                "description": "讨论技术话题的专属房间",
                "is_public": True,
                "max_members": 500
            },
            {
                "id": "random",
                "name": "随便聊聊",
                "description": "轻松愉快的闲聊区域",
                "is_public": True,
                "max_members": 300
            }
        ]
        
        for room_data in rooms_data:
            room = Room(**room_data)
            session.add(room)
            print(f"✅ 创建房间: {room.name}")
        
        await session.commit()


async def setup_cache():
    """设置缓存"""
    print("🔄 初始化缓存...")
    
    # 清理旧的缓存
    await cache_manager.delete("chatsphere:*")
    
    # 设置一些初始缓存数据
    await cache_manager.set("app:initialized", True, expire=86400)
    
    print("✅ 缓存初始化完成")


async def main():
    """主函数"""
    print("🚀 开始初始化 ChatSphere...")
    
    try:
        # 初始化数据库
        await db_manager.initialize()
        await db_manager.create_tables()
        print("✅ 数据库初始化完成")
        
        # 初始化缓存
        await cache_manager.initialize()
        await setup_cache()
        
        # 创建基础数据
        await create_test_users()
        await create_default_rooms()
        
        print("\n🎉 ChatSphere 初始化完成！")
        print("\n📋 测试账户信息:")
        print("   管理员: admin@chatsphere.com / admin123")
        print("   用户1: alice@example.com / password123")
        print("   用户2: bob@example.com / password123")
        print("\n🌐 访问地址:")
        print("   应用: http://localhost:8000")
        print("   文档: http://localhost:8000/docs")
        print("   健康检查: http://localhost:8000/health")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)
    finally:
        # 清理资源
        await cache_manager.close()
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main()) 