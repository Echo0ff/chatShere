#!/bin/bash
# ChatSphere 极速开发环境启动脚本
# 专门解决构建慢的问题

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

print_message $BLUE "⚡ ChatSphere 极速开发环境"
echo

# 检查是否已有运行的容器
if docker ps | grep -q "chatsphere.*dev"; then
    print_message $YELLOW "🔄 发现运行中的开发容器，正在重启..."
    docker-compose -f docker-compose.dev.yml restart
    print_message $GREEN "✅ 重启完成！"
    exit 0
fi

# 启用最快的Docker构建设置
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

print_message $YELLOW "🚀 启动极速构建模式..."

# 创建临时的docker-compose文件，使用最快的Dockerfile
cat > docker-compose.ultra-fast.yml << 'EOF'
services:
  postgres:
    image: postgres:15-alpine
    container_name: chatsphere-postgres-dev
    environment:
      POSTGRES_DB: chatsphere_dev
      POSTGRES_USER: chatsphere
      POSTGRES_PASSWORD: dev_password_123
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    networks:
      - chatsphere-dev

  redis:
    image: redis:7-alpine
    container_name: chatsphere-redis-dev
    command: redis-server --appendonly yes --requirepass dev_redis_123
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    networks:
      - chatsphere-dev

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.fast
    container_name: chatsphere-backend-dev
    environment:
      - DATABASE_URL=postgresql://chatsphere:dev_password_123@postgres:5432/chatsphere_dev
      - REDIS_URL=redis://:dev_redis_123@redis:6379/0
      - SECRET_KEY=dev_secret_key_not_for_production
      - DEBUG=true
      - ENVIRONMENT=development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis
    networks:
      - chatsphere-dev

  frontend:
    image: node:18-alpine
    container_name: chatsphere-frontend-dev
    working_dir: /app
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0"
    networks:
      - chatsphere-dev

volumes:
  postgres_dev_data:
  redis_dev_data:

networks:
  chatsphere-dev:
    driver: bridge
EOF

print_message $YELLOW "📦 启动服务（数据库优先）..."

# 先启动数据库服务
docker-compose -f docker-compose.ultra-fast.yml up -d postgres redis

print_message $YELLOW "⏳ 等待数据库启动..."
sleep 10

print_message $YELLOW "🔨 构建并启动应用服务..."

# 并行构建和启动应用服务
docker-compose -f docker-compose.ultra-fast.yml up -d backend frontend

print_message $YELLOW "⏳ 等待服务启动..."
sleep 15

# 健康检查
print_message $YELLOW "🔍 检查服务状态..."

if curl -f http://localhost:8000/health &> /dev/null; then
    print_message $GREEN "✅ 后端服务正常"
else
    print_message $YELLOW "⚠️  后端服务启动中..."
fi

if curl -f http://localhost:5173 &> /dev/null; then
    print_message $GREEN "✅ 前端服务正常"
else
    print_message $YELLOW "⚠️  前端服务启动中..."
fi

echo
print_message $GREEN "🎉 极速开发环境启动完成！"
print_message $BLUE "📱 前端: http://localhost:5173"
print_message $BLUE "🔧 后端: http://localhost:8000"
print_message $BLUE "📚 API文档: http://localhost:8000/docs"

echo
print_message $YELLOW "💡 管理命令:"
print_message $NC "  查看日志: docker-compose -f docker-compose.ultra-fast.yml logs -f"
print_message $NC "  停止服务: docker-compose -f docker-compose.ultra-fast.yml down"
print_message $NC "  重启服务: $0"

# 清理临时文件
trap 'rm -f docker-compose.ultra-fast.yml' EXIT
