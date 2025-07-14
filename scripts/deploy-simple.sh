#!/bin/bash
# ChatSphere 简化部署脚本
# 适用于方案1：服务器只保留最小文件，通过 Registry 拉取镜像

set -e

# 配置变量
DEPLOY_DIR="/opt/chatsphere"
HEALTH_CHECK_URL="http://localhost"
DOCKER_USERNAME="${DOCKER_USERNAME:-your-docker-username}"

echo "🚀 开始部署 ChatSphere..."

# 检查部署目录
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "❌ 部署目录不存在: $DEPLOY_DIR"
    echo "请先运行服务器初始化脚本: sudo ./server-setup.sh"
    exit 1
fi

cd "$DEPLOY_DIR"

# 检查必要文件
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ docker-compose.prod.yml 不存在"
    exit 1
fi

# 检查密钥文件
if [ ! -f "secrets/postgres_password.txt" ] || [ ! -f "secrets/redis_password.txt" ]; then
    echo "❌ 密钥文件不完整，请检查 secrets/ 目录"
    exit 1
fi

# 检查 Docker Compose 命令
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo "❌ Docker Compose 未安装"
        exit 1
    fi
fi

echo "🐳 使用 Docker Compose 命令: $DOCKER_COMPOSE_CMD"

# 备份当前配置
echo "📦 备份当前配置..."
cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️  没有找到配置文件进行备份"

# 登录到 Docker Registry（如果需要私有镜像）
echo "🔐 检查 Docker 登录状态..."
if [ -n "$DOCKER_PASSWORD" ] && [ -n "$DOCKER_USERNAME" ]; then
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
    echo "✅ Docker 登录成功"
fi

# 拉取最新镜像
echo "📥 拉取最新镜像..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml pull backend frontend

# 滚动更新 - 先更新后端
echo "🔄 更新后端服务..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --no-deps postgres redis
sleep 10

# 等待数据库就绪
echo "⏳ 等待数据库就绪..."
for i in {1..30}; do
    if $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml exec -T postgres pg_isready -U chatsphere -d chatsphere_prod &>/dev/null; then
        echo "✅ 数据库就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 数据库启动超时"
        exit 1
    fi
    echo "⏳ 等待数据库启动... ($i/30)"
    sleep 2
done

# 启动后端
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --no-deps backend
sleep 30

# 健康检查后端
echo "🏥 检查后端健康状态..."
for i in {1..10}; do
    if curl -f "$HEALTH_CHECK_URL/api/health" &>/dev/null; then
        echo "✅ 后端健康检查通过"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 后端健康检查失败"
        echo "📋 后端日志:"
        $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs --tail=20 backend
        exit 1
    fi
    echo "⏳ 等待后端启动... ($i/10)"
    sleep 10
done

# 更新前端和 Nginx
echo "🔄 更新前端和 Nginx 服务..."
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml up -d --no-deps frontend nginx
sleep 15

# 最终健康检查
echo "🏥 最终健康检查..."
for i in {1..5}; do
    if curl -f "$HEALTH_CHECK_URL/health" &>/dev/null; then
        echo "✅ 最终健康检查通过"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ 最终健康检查失败"
        echo "📋 Nginx 日志:"
        $DOCKER_COMPOSE_CMD -f docker-compose.prod.yml logs --tail=20 nginx
        exit 1
    fi
    echo "⏳ 等待服务完全启动... ($i/5)"
    sleep 10
done

# 显示服务状态
echo "📊 服务状态:"
$DOCKER_COMPOSE_CMD -f docker-compose.prod.yml ps

# 清理旧镜像
echo "🧹 清理旧镜像..."
docker image prune -f

echo ""
echo "🎉 生产环境部署成功!"
echo "📍 访问地址: http://49.232.202.209"
echo "📊 查看日志: cd $DEPLOY_DIR && docker-compose -f docker-compose.prod.yml logs -f"
echo "🔄 重启服务: cd $DEPLOY_DIR && docker-compose -f docker-compose.prod.yml restart"
echo "🛑 停止服务: cd $DEPLOY_DIR && docker-compose -f docker-compose.prod.yml down"
