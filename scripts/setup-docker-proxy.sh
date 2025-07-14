#!/bin/bash
# Docker 代理配置脚本 - 适用于 WSL + Clash

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

print_message $BLUE "🔧 配置 Docker 代理设置"
echo

# 获取 Windows 主机 IP（WSL 环境）
WINDOWS_HOST=$(ip route show | grep -i default | awk '{ print $3}')
print_message $YELLOW "检测到 Windows 主机 IP: $WINDOWS_HOST"

# Clash 默认端口
HTTP_PROXY_PORT="7890"
HTTPS_PROXY_PORT="7890"

# 构建代理 URL
HTTP_PROXY="http://${WINDOWS_HOST}:${HTTP_PROXY_PORT}"
HTTPS_PROXY="http://${WINDOWS_HOST}:${HTTPS_PROXY_PORT}"

print_message $YELLOW "配置代理地址:"
print_message $NC "HTTP Proxy: $HTTP_PROXY"
print_message $NC "HTTPS Proxy: $HTTPS_PROXY"

# 创建 Docker 配置目录
sudo mkdir -p /etc/systemd/system/docker.service.d

# 创建代理配置文件
print_message $YELLOW "创建 Docker 代理配置..."
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf > /dev/null <<EOF
[Service]
Environment="HTTP_PROXY=$HTTP_PROXY"
Environment="HTTPS_PROXY=$HTTPS_PROXY"
Environment="NO_PROXY=localhost,127.0.0.1,::1,*.local"
EOF

# 创建 Docker daemon 配置
print_message $YELLOW "配置 Docker daemon..."
sudo mkdir -p /etc/docker

# 检查是否已有 daemon.json
if [[ -f /etc/docker/daemon.json ]]; then
    sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup
    print_message $YELLOW "已备份现有的 daemon.json"
fi

# 创建新的 daemon.json（包含国内镜像源）
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ],
  "proxies": {
    "default": {
      "httpProxy": "$HTTP_PROXY",
      "httpsProxy": "$HTTPS_PROXY",
      "noProxy": "localhost,127.0.0.1,::1,*.local"
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# 重新加载 systemd 配置
print_message $YELLOW "重新加载 systemd 配置..."
sudo systemctl daemon-reload

# 重启 Docker 服务
print_message $YELLOW "重启 Docker 服务..."
sudo systemctl restart docker

# 验证配置
print_message $YELLOW "验证 Docker 配置..."
sleep 3

if sudo systemctl is-active --quiet docker; then
    print_message $GREEN "✅ Docker 服务运行正常"
else
    print_message $RED "❌ Docker 服务启动失败"
    exit 1
fi

# 测试网络连接
print_message $YELLOW "测试网络连接..."
if docker info > /dev/null 2>&1; then
    print_message $GREEN "✅ Docker 网络连接正常"
else
    print_message $RED "❌ Docker 网络连接失败"
fi

echo
print_message $GREEN "🎉 Docker 代理配置完成！"
print_message $BLUE "💡 提示:"
print_message $NC "1. 确保 Clash 代理软件正在运行"
print_message $NC "2. 确保 Clash 允许局域网连接"
print_message $NC "3. 如果仍有问题，请检查防火墙设置"

echo
print_message $YELLOW "下一步: 尝试拉取镜像测试"
print_message $NC "docker pull hello-world"
