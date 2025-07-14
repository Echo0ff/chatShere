#!/bin/bash
# ChatSphere 密钥生成脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${1}${2}${NC}"
}

print_message $BLUE "🔐 ChatSphere 密钥生成工具"
echo

# 创建 secrets 目录
mkdir -p secrets

# 生成强密码的函数
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# 生成超长密钥的函数
generate_secret_key() {
    openssl rand -base64 64 | tr -d "=+/"
}

# 检查文件是否存在
check_file_exists() {
    if [ -f "secrets/$1" ]; then
        print_message $YELLOW "⚠️  文件 secrets/$1 已存在，是否覆盖? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_message $BLUE "跳过 $1"
            return 1
        fi
    fi
    return 0
}

# 生成 PostgreSQL 密码
if check_file_exists "postgres_password.txt"; then
    POSTGRES_PASSWORD=$(generate_password)
    echo "$POSTGRES_PASSWORD" > secrets/postgres_password.txt
    print_message $GREEN "✅ 生成 PostgreSQL 密码"
fi

# 生成 Redis 密码
if check_file_exists "redis_password.txt"; then
    REDIS_PASSWORD=$(generate_password)
    echo "$REDIS_PASSWORD" > secrets/redis_password.txt
    print_message $GREEN "✅ 生成 Redis 密码"
fi

# 生成应用密钥
if check_file_exists "secret_key.txt"; then
    SECRET_KEY=$(generate_secret_key)
    echo "$SECRET_KEY" > secrets/secret_key.txt
    print_message $GREEN "✅ 生成应用密钥"
fi

# 生成数据库连接字符串
if check_file_exists "database_url.txt"; then
    if [ -f "secrets/postgres_password.txt" ]; then
        POSTGRES_PASSWORD=$(cat secrets/postgres_password.txt)
    else
        print_message $RED "❌ 请先生成 PostgreSQL 密码"
        exit 1
    fi
    DATABASE_URL="postgresql://chatsphere:${POSTGRES_PASSWORD}@postgres:5432/chatsphere_prod"
    echo "$DATABASE_URL" > secrets/database_url.txt
    print_message $GREEN "✅ 生成数据库连接字符串"
fi

# 生成 Redis 连接字符串
if check_file_exists "redis_url.txt"; then
    if [ -f "secrets/redis_password.txt" ]; then
        REDIS_PASSWORD=$(cat secrets/redis_password.txt)
    else
        print_message $RED "❌ 请先生成 Redis 密码"
        exit 1
    fi
    REDIS_URL="redis://:${REDIS_PASSWORD}@redis:6379/0"
    echo "$REDIS_URL" > secrets/redis_url.txt
    print_message $GREEN "✅ 生成 Redis 连接字符串"
fi

# 设置文件权限
chmod 600 secrets/*.txt
print_message $GREEN "✅ 设置密钥文件权限为 600"

echo
print_message $GREEN "🎉 密钥生成完成！"
print_message $YELLOW "⚠️  请妥善保管这些密钥文件，不要提交到版本控制系统"
print_message $BLUE "💡 生产环境部署时，请将这些文件安全地传输到服务器"

echo
print_message $BLUE "生成的文件："
ls -la secrets/*.txt

echo
print_message $YELLOW "下一步："
print_message $NC "1. 将密钥文件复制到生产服务器的 /opt/chatsphere/secrets/ 目录"
print_message $NC "2. 确保文件权限为 600 且所有者为部署用户"
print_message $NC "3. 运行 docker-compose -f docker-compose.prod.yml up -d"
