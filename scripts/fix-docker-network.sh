#!/bin/bash
# Docker 网络问题修复脚本

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

print_message $BLUE "🔧 Docker 网络问题修复工具"
echo

# 检查当前 Docker 代理设置
print_message $YELLOW "📋 当前 Docker 代理设置:"
docker info | grep -i proxy || echo "未找到代理设置"
echo

# 提供解决方案选项
echo "请选择解决方案:"
echo "1. 临时禁用 Docker 代理（推荐）"
echo "2. 配置国内镜像源"
echo "3. 检查并启动代理服务"
echo "4. 手动配置 Docker 代理"
echo "5. 退出"
echo

read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        print_message $YELLOW "🔄 临时禁用 Docker 代理..."

        # 创建临时的 Docker 配置目录
        mkdir -p ~/.docker

        # 备份现有配置
        if [[ -f ~/.docker/config.json ]]; then
            cp ~/.docker/config.json ~/.docker/config.json.backup
            print_message $GREEN "✅ 已备份现有 Docker 配置"
        fi

        # 创建无代理的配置
        cat > ~/.docker/config.json << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "",
      "httpsProxy": "",
      "noProxy": ""
    }
  }
}
EOF

        print_message $GREEN "✅ 已禁用 Docker 代理"
        print_message $BLUE "💡 现在可以重新运行 Docker Compose 命令"
        ;;

    2)
        print_message $YELLOW "🌏 配置国内镜像源..."

        # 创建 Docker daemon 配置
        sudo mkdir -p /etc/docker

        # 备份现有配置
        if [[ -f /etc/docker/daemon.json ]]; then
            sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
            print_message $GREEN "✅ 已备份现有 daemon 配置"
        fi

        # 配置国内镜像源
        sudo tee /etc/docker/daemon.json > /dev/null << EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "insecure-registries": [],
  "debug": false,
  "experimental": false
}
EOF

        print_message $GREEN "✅ 已配置国内镜像源"
        print_message $YELLOW "⚠️  需要重启 Docker 服务"

        read -p "是否现在重启 Docker 服务? (y/N): " restart_docker
        if [[ "$restart_docker" =~ ^[Yy]$ ]]; then
            sudo systemctl restart docker
            print_message $GREEN "✅ Docker 服务已重启"
        fi
        ;;

    3)
        print_message $YELLOW "🔍 检查代理服务..."

        # 检查端口 7890 是否有服务在监听
        if netstat -tuln | grep -q ":7890"; then
            print_message $GREEN "✅ 代理服务正在运行"
        else
            print_message $RED "❌ 代理服务未运行"
            print_message $BLUE "💡 请启动您的代理软件（如 Clash、V2Ray 等）"
        fi

        # 测试代理连接
        if curl -x http://127.0.0.1:7890 --connect-timeout 5 -s http://www.google.com > /dev/null 2>&1; then
            print_message $GREEN "✅ 代理连接正常"
        else
            print_message $RED "❌ 代理连接失败"
        fi
        ;;

    4)
        print_message $YELLOW "⚙️  手动配置 Docker 代理..."

        echo "请输入代理信息（留空表示不使用代理）:"
        read -p "HTTP 代理 (如: http://127.0.0.1:7890): " http_proxy
        read -p "HTTPS 代理 (如: http://127.0.0.1:7890): " https_proxy
        read -p "不使用代理的地址 (如: localhost,127.0.0.1): " no_proxy

        mkdir -p ~/.docker

        if [[ -n "$http_proxy" || -n "$https_proxy" ]]; then
            cat > ~/.docker/config.json << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "$http_proxy",
      "httpsProxy": "$https_proxy",
      "noProxy": "$no_proxy"
    }
  }
}
EOF
            print_message $GREEN "✅ 已配置 Docker 代理"
        else
            cat > ~/.docker/config.json << EOF
{
  "proxies": {
    "default": {
      "httpProxy": "",
      "httpsProxy": "",
      "noProxy": ""
    }
  }
}
EOF
            print_message $GREEN "✅ 已禁用 Docker 代理"
        fi
        ;;

    5)
        print_message $BLUE "👋 退出"
        exit 0
        ;;

    *)
        print_message $RED "❌ 无效选项"
        exit 1
        ;;
esac

echo
print_message $GREEN "🎉 配置完成！"
print_message $BLUE "💡 建议测试命令:"
print_message $NC "  docker pull hello-world"
print_message $NC "  docker-compose -f docker-compose.dev.yml up -d"

echo
print_message $YELLOW "📝 如果问题仍然存在:"
print_message $NC "1. 检查网络连接"
print_message $NC "2. 重启 Docker Desktop"
print_message $NC "3. 尝试使用手机热点"
print_message $NC "4. 联系网络管理员"
