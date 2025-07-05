#!/usr/bin/env python3
"""
ChatSphere 后端启动脚本
"""

import uvicorn
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="启动 ChatSphere 后端服务")
    parser.add_argument("--host", default="0.0.0.0", help="服务器主机地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="启用自动重载 (开发模式)")
    parser.add_argument("--log-level", default="info", help="日志级别 (默认: info)")
    
    args = parser.parse_args()
    
    print(f"🚀 启动 ChatSphere 后端服务...")
    print(f"📡 地址: http://{args.host}:{args.port}")
    print(f"🔌 WebSocket: ws://{args.host}:{args.port}/ws/{{user_id}}")
    
    if args.reload:
        print("🔄 自动重载已启用 (开发模式)")
    
    try:
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        sys.exit(0)

if __name__ == "__main__":
    main() 