#!/bin/bash
# ChatSphere 快速构建脚本 - 针对开发环境优化

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    echo -e "${1}${2}${NC}"
}

print_message $BLUE "🚀 ChatSphere 快速构建 - 开发环境优化"
echo

# 检查Docker是否支持BuildKit
if ! docker buildx version &> /dev/null; then
    print_message $YELLOW "⚠️  Docker BuildKit 未启用，启用以获得更快的构建速度..."
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
fi

# 启用Docker BuildKit缓存
export BUILDKIT_PROGRESS=plain

print_message $YELLOW "🔧 配置构建优化..."

# 创建buildx构建器（如果不存在）
if ! docker buildx ls | grep -q "chatsphere-builder"; then
    print_message $YELLOW "📦 创建优化的构建器..."
    docker buildx create --name chatsphere-builder --use --bootstrap
    print_message $GREEN "✅ 构建器创建完成"
fi

# 使用构建器
docker buildx use chatsphere-builder

print_message $YELLOW "🏗️  开始快速构建..."

# 并行构建前后端
print_message $BLUE "🔨 并行构建前后端镜像..."

# 后端构建（使用缓存）
print_message $YELLOW "📦 构建后端镜像..."
docker buildx build \
    --platform linux/amd64 \
    --cache-from type=local,src=/tmp/.buildx-cache-backend \
    --cache-to type=local,dest=/tmp/.buildx-cache-backend-new,mode=max \
    -f backend/Dockerfile.dev \
    -t chatsphere-backend:dev \
    --load \
    backend/ &

BACKEND_PID=$!

# 前端构建（使用缓存）
print_message $YELLOW "📦 构建前端镜像..."
docker buildx build \
    --platform linux/amd64 \
    --cache-from type=local,src=/tmp/.buildx-cache-frontend \
    --cache-to type=local,dest=/tmp/.buildx-cache-frontend-new,mode=max \
    -f frontend/Dockerfile \
    --target development \
    -t chatsphere-frontend:dev \
    --load \
    frontend/ &

FRONTEND_PID=$!

# 等待构建完成
print_message $YELLOW "⏳ 等待构建完成..."
wait $BACKEND_PID
BACKEND_EXIT=$?

wait $FRONTEND_PID
FRONTEND_EXIT=$?

# 更新缓存
if [ -d "/tmp/.buildx-cache-backend-new" ]; then
    rm -rf /tmp/.buildx-cache-backend
    mv /tmp/.buildx-cache-backend-new /tmp/.buildx-cache-backend
fi

if [ -d "/tmp/.buildx-cache-frontend-new" ]; then
    rm -rf /tmp/.buildx-cache-frontend
    mv /tmp/.buildx-cache-frontend-new /tmp/.buildx-cache-frontend
fi

# 检查构建结果
if [ $BACKEND_EXIT -eq 0 ] && [ $FRONTEND_EXIT -eq 0 ]; then
    print_message $GREEN "✅ 所有镜像构建成功！"

    print_message $YELLOW "🚀 启动开发环境..."
    docker-compose -f docker-compose.dev.yml up -d

    print_message $GREEN "🎉 开发环境启动完成！"
    print_message $BLUE "📱 前端: http://localhost:5173"
    print_message $BLUE "🔧 后端: http://localhost:8000"
    print_message $BLUE "📚 API文档: http://localhost:8000/docs"
else
    print_message $RED "❌ 构建失败"
    exit 1
fi

echo
print_message $YELLOW "💡 提示："
print_message $NC "  - 下次构建会更快（使用了缓存）"
print_message $NC "  - 使用 docker-compose -f docker-compose.dev.yml logs -f 查看日志"
print_message $NC "  - 使用 Ctrl+C 停止服务"
