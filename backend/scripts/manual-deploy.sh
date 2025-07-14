#!/bin/bash

# ChatSphere 手动部署脚本
# 用于首次部署或紧急情况下的手动部署

set -e

# 配置
SERVER_IP="49.232.202.209"
APP_DIR="/opt/chatsphere"
REPO_URL="https://github.com/YOUR_USERNAME/chatSphere.git"  # 替换为你的仓库地址

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 [local|remote] [branch]"
    echo "  local  - 本地部署到远程服务器"
    echo "  remote - 在远程服务器上直接部署"
    echo "  branch - 要部署的分支 (默认: main)"
    exit 1
fi

MODE=$1
BRANCH=${2:-main}

deploy_local() {
    print_message $BLUE "开始本地部署到远程服务器..."

    # 检查 SSH 连接
    print_message $YELLOW "测试 SSH 连接..."
    if ! ssh -o ConnectTimeout=10 root@$SERVER_IP "echo 'SSH 连接正常'"; then
        print_message $RED "SSH 连接失败，请检查:"
        echo "1. 服务器 IP 地址是否正确"
        echo "2. SSH 密钥是否配置正确"
        echo "3. 服务器是否允许 root 登录"
        exit 1
    fi

    # 打包本地代码
    print_message $YELLOW "打包本地代码..."
    tar -czf chatsphere.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' .

    # 上传代码到服务器
    print_message $YELLOW "上传代码到服务器..."
    scp chatsphere.tar.gz root@$SERVER_IP:/tmp/

    # 在服务器上部署
    ssh root@$SERVER_IP << 'ENDSSH'
        set -e

        # 创建应用目录
        mkdir -p /opt/chatsphere
        cd /opt/chatsphere

        # 备份当前版本
        if [ -d "current" ]; then
            rm -rf backup
            mv current backup
        fi

        # 解压新代码
        mkdir -p current
        cd current
        tar -xzf /tmp/chatsphere.tar.gz
        rm /tmp/chatsphere.tar.gz

        # 进入后端目录
        cd backend

        # 复制环境配置
        if [ ! -f .env.staging ]; then
            echo "错误: .env.staging 文件不存在"
            exit 1
        fi
        cp .env.staging .env

        # 停止旧服务
        docker-compose -f docker-compose.staging.yml down 2>/dev/null || true

        # 构建并启动服务
        docker-compose -f docker-compose.staging.yml build
        docker-compose -f docker-compose.staging.yml up -d

        # 等待服务启动
        echo "等待服务启动..."
        sleep 30

        # 健康检查
        if curl -f http://localhost/health; then
            echo "✓ 部署成功!"
            echo "应用访问地址: http://49.232.202.209"
        else
            echo "✗ 健康检查失败"
            docker-compose -f docker-compose.staging.yml logs chatsphere
            exit 1
        fi
ENDSSH

    # 清理本地临时文件
    rm chatsphere.tar.gz

    print_message $GREEN "本地部署完成!"
}

deploy_remote() {
    print_message $BLUE "在远程服务器上直接部署..."

    ssh root@$SERVER_IP << ENDSSH
        set -e

        # 创建应用目录
        mkdir -p /opt/chatsphere
        cd /opt/chatsphere

        # 备份当前版本
        if [ -d "current" ]; then
            rm -rf backup
            mv current backup
        fi

        # 克隆或更新代码
        if [ ! -d "current" ]; then
            git clone -b $BRANCH $REPO_URL current
        else
            cd current
            git fetch origin
            git checkout $BRANCH
            git reset --hard origin/$BRANCH
            cd ..
        fi

        cd current/backend

        # 检查环境配置
        if [ ! -f .env.staging ]; then
            echo "错误: .env.staging 文件不存在"
            echo "请先创建并配置 .env.staging 文件"
            exit 1
        fi

        # 复制环境配置
        cp .env.staging .env

        # 停止旧服务
        docker-compose -f docker-compose.staging.yml down 2>/dev/null || true

        # 清理旧镜像
        docker system prune -f

        # 构建并启动服务
        docker-compose -f docker-compose.staging.yml build
        docker-compose -f docker-compose.staging.yml up -d

        # 等待服务启动
        echo "等待服务启动..."
        sleep 30

        # 运行数据库迁移
        docker-compose -f docker-compose.staging.yml exec -T chatsphere python scripts/setup.py || true

        # 健康检查
        if curl -f http://localhost/health; then
            echo "✓ 部署成功!"
            echo "应用访问地址: http://49.232.202.209"
            echo "监控面板: http://49.232.202.209:3000"
            echo "容器管理: http://49.232.202.209:9000"
        else
            echo "✗ 健康检查失败"
            docker-compose -f docker-compose.staging.yml logs chatsphere
            exit 1
        fi
ENDSSH

    print_message $GREEN "远程部署完成!"
}

# 显示部署信息
print_message $BLUE "=========================================="
print_message $BLUE "ChatSphere 手动部署"
print_message $BLUE "=========================================="
echo "服务器: $SERVER_IP"
echo "分支: $BRANCH"
echo "模式: $MODE"
echo ""

# 执行部署
case $MODE in
    local)
        deploy_local
        ;;
    remote)
        deploy_remote
        ;;
    *)
        print_message $RED "错误: 不支持的部署模式 '$MODE'"
        echo "支持的模式: local, remote"
        exit 1
        ;;
esac

print_message $GREEN "部署完成! 🎉"
print_message $BLUE "访问地址: http://$SERVER_IP"
