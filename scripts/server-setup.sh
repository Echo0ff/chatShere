#!/bin/bash
# ChatSphere 服务器初始化脚本
# 用于第一次在服务器上设置部署环境

set -e

echo "🚀 初始化 ChatSphere 服务器环境..."

# 配置变量
DEPLOY_DIR="/opt/chatsphere"
DOCKER_USERNAME="${1:-your-docker-username}"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 创建部署目录
echo "📁 创建部署目录..."
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# 创建必要的子目录
mkdir -p secrets nginx ssl logs

# 创建 docker-compose.prod.yml（简化版，只包含镜像引用）
echo "📝 创建 docker-compose.prod.yml..."
cat > docker-compose.prod.yml << 'EOF'
# ChatSphere 生产环境 Docker Compose（简化版）
services:
  # PostgreSQL 数据库
  postgres:
    image: postgres:15-alpine
    container_name: chatsphere-postgres-prod
    environment:
      POSTGRES_DB: chatsphere_prod
      POSTGRES_USER: chatsphere
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    networks:
      - chatsphere-prod
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatsphere -d chatsphere_prod"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: chatsphere-redis-prod
    command: redis-server --appendonly yes --requirepass-file /run/secrets/redis_password
    secrets:
      - redis_password
    volumes:
      - redis_prod_data:/data
    networks:
      - chatsphere-prod
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # 后端服务（使用 Registry 镜像）
  backend:
    image: DOCKER_USERNAME/chatsphere-backend:latest
    container_name: chatsphere-backend-prod
    environment:
      - DATABASE_URL_FILE=/run/secrets/database_url
      - REDIS_URL_FILE=/run/secrets/redis_url
      - SECRET_KEY_FILE=/run/secrets/secret_key
      - DEBUG=false
      - ENVIRONMENT=production
      - CORS_ORIGINS=https://yourdomain.com
    secrets:
      - database_url
      - redis_url
      - secret_key
    volumes:
      - backend_prod_logs:/app/logs
      - backend_prod_uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - chatsphere-prod
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    restart: unless-stopped

  # 前端服务（使用 Registry 镜像）
  frontend:
    image: DOCKER_USERNAME/chatsphere-frontend:latest
    container_name: chatsphere-frontend-prod
    depends_on:
      - backend
    networks:
      - chatsphere-prod
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: chatsphere-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/prod.conf:/etc/nginx/conf.d/default.conf
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl:ro
      - nginx_prod_logs:/var/log/nginx
    depends_on:
      - frontend
      - backend
    networks:
      - chatsphere-prod
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

# 密钥管理
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  redis_password:
    file: ./secrets/redis_password.txt
  database_url:
    file: ./secrets/database_url.txt
  redis_url:
    file: ./secrets/redis_url.txt
  secret_key:
    file: ./secrets/secret_key.txt

# 数据卷
volumes:
  postgres_prod_data:
    driver: local
  redis_prod_data:
    driver: local
  backend_prod_logs:
    driver: local
  backend_prod_uploads:
    driver: local
  nginx_prod_logs:
    driver: local

# 网络
networks:
  chatsphere-prod:
    driver: bridge
    name: chatsphere-prod-network
EOF

# 替换 Docker 用户名
sed -i "s/DOCKER_USERNAME/$DOCKER_USERNAME/g" docker-compose.prod.yml

echo "🔐 创建密钥文件模板..."
# 创建密钥文件（需要用户手动填写）
cat > secrets/README.md << 'EOF'
# 密钥文件配置说明

请手动编辑以下文件，填入实际的密钥值：

1. postgres_password.txt - PostgreSQL 数据库密码
2. redis_password.txt - Redis 密码
3. database_url.txt - 完整的数据库连接字符串
4. redis_url.txt - 完整的 Redis 连接字符串
5. secret_key.txt - JWT 密钥（建议使用长随机字符串）

示例：
echo "your_secure_postgres_password" > postgres_password.txt
echo "your_secure_redis_password" > redis_password.txt
echo "postgresql://chatsphere:your_secure_postgres_password@postgres:5432/chatsphere_prod" > database_url.txt
echo "redis://:your_secure_redis_password@redis:6379/0" > redis_url.txt
echo "your_very_long_jwt_secret_key_here" > secret_key.txt
EOF

# 创建基本的 Nginx 配置
echo "🌐 创建 Nginx 配置..."
cat > nginx/prod.conf << 'EOF'
server {
    listen 80;
    server_name _;

    # 健康检查端点
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # API 代理到后端
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端静态文件
    location / {
        proxy_pass http://frontend:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/javascript
        application/json;

    include /etc/nginx/conf.d/*.conf;
}
EOF

# 设置权限
chown -R $SUDO_USER:$SUDO_USER $DEPLOY_DIR
chmod 755 $DEPLOY_DIR
chmod 700 $DEPLOY_DIR/secrets

echo "✅ 服务器环境初始化完成！"
echo ""
echo "📋 下一步操作："
echo "1. 编辑密钥文件: cd $DEPLOY_DIR/secrets && 按照 README.md 说明填写密钥"
echo "2. 创建部署脚本: 将 deploy-simple.sh 复制到 $DEPLOY_DIR/"
echo "3. 测试部署: sudo $DEPLOY_DIR/deploy-simple.sh"
echo ""
echo "📍 部署目录: $DEPLOY_DIR"
