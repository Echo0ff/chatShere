#!/bin/bash

# ChatSphere 服务器环境初始化脚本
# 适用于 Ubuntu 20.04+ 服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message $BLUE "开始初始化 ChatSphere 服务器环境..."

# 更新系统
print_message $YELLOW "更新系统包..."
apt update && apt upgrade -y

# 安装基础软件
print_message $YELLOW "安装基础软件..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# 安装 Docker
print_message $YELLOW "安装 Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
    systemctl start docker
    systemctl enable docker
    print_message $GREEN "✓ Docker 安装完成"
else
    print_message $GREEN "✓ Docker 已安装"
fi

# 安装 Docker Compose
print_message $YELLOW "安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_message $GREEN "✓ Docker Compose 安装完成"
else
    print_message $GREEN "✓ Docker Compose 已安装"
fi

# 配置防火墙
print_message $YELLOW "配置防火墙..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# 允许必要的端口
ufw allow ssh
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 3000/tcp  # Grafana
ufw allow 9000/tcp  # Portainer
ufw allow 9090/tcp  # Prometheus

# 启用防火墙
ufw --force enable
print_message $GREEN "✓ 防火墙配置完成"

# 配置 fail2ban
print_message $YELLOW "配置 fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

systemctl restart fail2ban
systemctl enable fail2ban
print_message $GREEN "✓ fail2ban 配置完成"

# 创建应用目录
print_message $YELLOW "创建应用目录..."
mkdir -p /opt/chatsphere
mkdir -p /opt/chatsphere/logs
mkdir -p /opt/chatsphere/backups
chown -R $USER:$USER /opt/chatsphere

# 配置 Docker 日志轮转
print_message $YELLOW "配置 Docker 日志轮转..."
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker

# 安装监控工具
print_message $YELLOW "安装系统监控工具..."
apt install -y htop iotop nethogs

# 创建部署用户（可选）
print_message $YELLOW "创建部署用户..."
if ! id "deploy" &>/dev/null; then
    useradd -m -s /bin/bash deploy
    usermod -aG docker deploy
    mkdir -p /home/deploy/.ssh
    chown deploy:deploy /home/deploy/.ssh
    chmod 700 /home/deploy/.ssh
    print_message $GREEN "✓ 部署用户创建完成"
fi

# 配置系统参数优化
print_message $YELLOW "优化系统参数..."
cat >> /etc/sysctl.conf << EOF

# ChatSphere 性能优化
vm.max_map_count=262144
net.core.rmem_max=134217728
net.core.wmem_max=134217728
net.ipv4.tcp_rmem=4096 65536 134217728
net.ipv4.tcp_wmem=4096 65536 134217728
net.core.netdev_max_backlog=5000
EOF

sysctl -p

# 创建备份脚本
print_message $YELLOW "创建备份脚本..."
cat > /opt/chatsphere/backup.sh << 'EOF'
#!/bin/bash

# ChatSphere 备份脚本
BACKUP_DIR="/opt/chatsphere/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/chatsphere/current"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cd $APP_DIR/backend
docker-compose -f docker-compose.staging.yml exec -T postgres pg_dump -U postgres chatsphere_staging > $BACKUP_DIR/db_backup_$DATE.sql

# 备份应用数据
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt/chatsphere current

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
EOF

chmod +x /opt/chatsphere/backup.sh

# 设置定时备份
print_message $YELLOW "设置定时备份..."
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/chatsphere/backup.sh >> /opt/chatsphere/logs/backup.log 2>&1") | crontab -

# 创建启动脚本
print_message $YELLOW "创建服务管理脚本..."
cat > /opt/chatsphere/chatsphere.sh << 'EOF'
#!/bin/bash

APP_DIR="/opt/chatsphere/current/backend"
COMPOSE_FILE="docker-compose.staging.yml"

case "$1" in
    start)
        cd $APP_DIR
        docker-compose -f $COMPOSE_FILE up -d
        echo "ChatSphere 服务已启动"
        ;;
    stop)
        cd $APP_DIR
        docker-compose -f $COMPOSE_FILE down
        echo "ChatSphere 服务已停止"
        ;;
    restart)
        cd $APP_DIR
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE up -d
        echo "ChatSphere 服务已重启"
        ;;
    status)
        cd $APP_DIR
        docker-compose -f $COMPOSE_FILE ps
        ;;
    logs)
        cd $APP_DIR
        docker-compose -f $COMPOSE_FILE logs -f ${2:-chatsphere}
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs [service]}"
        exit 1
        ;;
esac
EOF

chmod +x /opt/chatsphere/chatsphere.sh
ln -sf /opt/chatsphere/chatsphere.sh /usr/local/bin/chatsphere

# 显示服务器信息
print_message $GREEN "=========================================="
print_message $GREEN "ChatSphere 服务器环境初始化完成!"
print_message $GREEN "=========================================="
echo ""
print_message $BLUE "服务器信息:"
echo "  IP地址: $(curl -s ifconfig.me)"
echo "  系统: $(lsb_release -d | cut -f2)"
echo "  Docker: $(docker --version)"
echo "  Docker Compose: $(docker-compose --version)"
echo ""
print_message $BLUE "目录结构:"
echo "  应用目录: /opt/chatsphere"
echo "  备份目录: /opt/chatsphere/backups"
echo "  日志目录: /opt/chatsphere/logs"
echo ""
print_message $BLUE "服务管理:"
echo "  启动服务: chatsphere start"
echo "  停止服务: chatsphere stop"
echo "  重启服务: chatsphere restart"
echo "  查看状态: chatsphere status"
echo "  查看日志: chatsphere logs"
echo ""
print_message $BLUE "访问地址:"
echo "  应用: http://$(curl -s ifconfig.me)"
echo "  监控: http://$(curl -s ifconfig.me):3000"
echo "  容器管理: http://$(curl -s ifconfig.me):9000"
echo ""
print_message $YELLOW "下一步:"
echo "1. 配置 GitHub Actions Secrets"
echo "2. 推送代码到 GitHub 触发自动部署"
echo "3. 或手动克隆代码进行部署"

print_message $GREEN "初始化完成! 🎉" 