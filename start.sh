#!/bin/bash
# ChatSphere 快速启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_message() {
    echo -e "${1}${2}${NC}"
}

print_message $BLUE "🚀 ChatSphere 快速启动"
echo

# 检查是否为首次运行
if [[ ! -f ".env" ]]; then
    print_message $YELLOW "⚙️  首次运行，正在初始化..."

    # 复制环境配置文件
    if [[ -f "backend/.env.example" ]]; then
        cp backend/.env.example backend/.env
        print_message $GREEN "✅ 已创建后端环境配置文件"
    fi

    if [[ -f "frontend/.env.example" ]]; then
        cp frontend/.env.example frontend/.env.local
        print_message $GREEN "✅ 已创建前端环境配置文件"
    fi

    # 创建标记文件
    touch .env
fi

# 启动开发环境
print_message $YELLOW "🔧 启动开发环境..."
./scripts/deploy.sh dev

echo
print_message $GREEN "🎉 ChatSphere 开发环境已启动！"
print_message $BLUE "📱 前端地址: http://localhost:5173"
print_message $BLUE "🔧 后端地址: http://localhost:8000"
print_message $BLUE "📚 API 文档: http://localhost:8000/docs"
echo
print_message $YELLOW "💡 提示:"
print_message $NC "  - 使用 Ctrl+C 停止服务"
print_message $NC "  - 查看日志: docker-compose -f docker-compose.dev.yml logs -f"
print_message $NC "  - 重启服务: ./scripts/deploy.sh dev --build"
