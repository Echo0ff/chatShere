#!/bin/bash
# Docker 国内镜像源配置脚本

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

print_message $BLUE "🔧 配置 Docker 国内镜像源"
echo

# 创建 Docker 配置目录
sudo mkdir -p /etc/docker

# 备份现有配置
if [[ -f /etc/docker/daemon.json ]]; then
    sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)
    print_message $YELLOW "已备份现有的 daemon.json"
fi

# 创建新的 daemon.json
print_message $YELLOW "配置 Docker 镜像源..."
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://dockerproxy.com",
    "https://docker.nju.edu.cn"
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF

# 重启 Docker 服务
print_message $YELLOW "重启 Docker 服务..."
sudo systemctl daemon-reload
sudo systemctl restart docker

# 验证配置
print_message $YELLOW "验证配置..."
sleep 3

if sudo systemctl is-active --quiet docker; then
    print_message $GREEN "✅ Docker 服务运行正常"
else
    print_message $RED "❌ Docker 服务启动失败"
    exit 1
fi

# 显示配置信息
print_message $YELLOW "当前镜像源配置:"
docker info | grep -A 10 "Registry Mirrors:" || echo "镜像源信息获取失败"

echo
print_message $GREEN "🎉 Docker 镜像源配置完成！"
print_message $BLUE "💡 现在可以尝试拉取镜像:"
print_message $NC "docker pull hello-world"
