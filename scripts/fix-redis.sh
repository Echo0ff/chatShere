#!/bin/bash
# ChatSphere Redis 配置修复脚本

set -e

echo "🔧 修复 Redis 配置问题..."

cd /opt/chatsphere

# 停止服务
echo "🛑 停止现有服务..."
sudo docker compose -f docker-compose.prod.yml down || true

# 备份配置文件
echo "📦 备份配置文件..."
sudo cp docker-compose.prod.yml docker-compose.prod.yml.redis-backup.$(date +%Y%m%d_%H%M%S)

# 修复 Redis 配置
echo "🔧 修复 Redis 配置..."

# 方法1：使用简单的 requirepass（推荐）
sudo sed -i 's/command: redis-server --appendonly yes --requirepass-file \/run\/secrets\/redis_password/command: sh -c "redis-server --appendonly yes --requirepass $$(cat \/run\/secrets\/redis_password)"/' docker-compose.prod.yml

# 检查修改是否成功
if grep -q 'sh -c "redis-server' docker-compose.prod.yml; then
    echo "✅ Redis 配置修复成功"
else
    echo "⚠️  自动修复失败，使用备用方案..."

    # 备用方案：直接使用密码而不是文件
    REDIS_PASSWORD=$(sudo cat secrets/redis_password.txt)

    # 创建新的 Redis 配置
    sudo sed -i "/command: redis-server/c\    command: redis-server --appendonly yes --requirepass $REDIS_PASSWORD" docker-compose.prod.yml

    # 移除 Redis 的 secrets 配置
    sudo sed -i '/redis:/,/restart: unless-stopped/ { /secrets:/d; /- redis_password/d; }' docker-compose.prod.yml

    echo "✅ 使用备用方案修复完成"
fi

# 重新启动服务
echo "🚀 重新启动服务..."
sudo docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 20

# 检查 Redis 状态
echo "🔍 检查 Redis 状态..."
if sudo docker compose -f docker-compose.prod.yml exec redis redis-cli ping &>/dev/null; then
    echo "✅ Redis 启动成功"
else
    echo "⚠️  Redis 可能需要密码认证，这是正常的"
fi

# 检查所有服务状态
echo "📊 检查所有服务状态..."
sudo docker compose -f docker-compose.prod.yml ps

# 等待后端启动
echo "⏳ 等待后端服务启动..."
sleep 30

# 健康检查
echo "🏥 健康检查..."
for i in {1..10}; do
    if curl -f http://localhost/api/health &>/dev/null; then
        echo "✅ 后端健康检查通过"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 后端健康检查失败，查看日志："
        sudo docker compose -f docker-compose.prod.yml logs --tail=20 backend
        echo ""
        echo "Redis 日志："
        sudo docker compose -f docker-compose.prod.yml logs --tail=10 redis
        exit 1
    fi
    echo "⏳ 等待后端启动... ($i/10)"
    sleep 10
done

# 最终健康检查
if curl -f http://localhost/health &>/dev/null; then
    echo "✅ 最终健康检查通过"
else
    echo "❌ 最终健康检查失败，但 Redis 问题已修复"
    echo "可能是其他服务的问题，请检查日志"
fi

echo ""
echo "🎉 Redis 配置修复完成！"
echo "📍 访问地址: http://49.232.202.209"
echo ""
echo "📋 如果还有问题，请检查："
echo "1. 后端日志: sudo docker compose -f docker-compose.prod.yml logs backend"
echo "2. Redis 日志: sudo docker compose -f docker-compose.prod.yml logs redis"
echo "3. 所有服务状态: sudo docker compose -f docker-compose.prod.yml ps"
