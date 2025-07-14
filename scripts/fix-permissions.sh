#!/bin/bash
# ChatSphere 权限问题修复脚本

set -e

echo "🔧 修复 ChatSphere 权限问题..."

cd /opt/chatsphere

# 备份原配置
sudo cp docker-compose.prod.yml docker-compose.prod.yml.backup.$(date +%Y%m%d_%H%M%S)

# 方法1：临时修复 - 让后端以 root 用户运行
echo "📝 方法1：临时修复 docker-compose.prod.yml..."

# 检查是否已经添加了 user: root
if ! grep -q "user: root" docker-compose.prod.yml; then
    # 在 backend 服务的 container_name 后添加 user: root
    sudo sed -i '/container_name: chatsphere-backend-prod/a\    user: root' docker-compose.prod.yml
    echo "✅ 已添加 user: root 到后端服务配置"
else
    echo "ℹ️  user: root 已存在，跳过修改"
fi

# 停止现有容器
echo "🛑 停止现有容器..."
sudo docker compose -f docker-compose.prod.yml down || true

# 重新启动服务
echo "🚀 重新启动服务..."
sudo docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
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
        exit 1
    fi
    echo "⏳ 等待后端启动... ($i/10)"
    sleep 10
done

# 最终健康检查
if curl -f http://localhost/health &>/dev/null; then
    echo "✅ 最终健康检查通过"
else
    echo "❌ 最终健康检查失败"
    exit 1
fi

echo ""
echo "🎉 权限问题修复完成！"
echo "📍 访问地址: http://49.232.202.209"
echo ""
echo "📋 后续建议："
echo "1. 重新构建镜像以永久修复权限问题"
echo "2. 推送修复后的代码到 GitHub"
echo "3. 通过 CI/CD 重新部署"
