#!/bin/bash
# ChatSphere 构建性能诊断脚本

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

print_message $BLUE "🔍 ChatSphere 构建性能诊断"
echo

# 1. 检查网络连接速度
print_message $YELLOW "📡 检查网络连接速度..."

echo "测试官方Docker Hub:"
time curl -o /dev/null -s -w "连接时间: %{time_connect}s, 总时间: %{time_total}s\n" https://registry-1.docker.io/

echo "测试阿里云镜像:"
time curl -o /dev/null -s -w "连接时间: %{time_connect}s, 总时间: %{time_total}s\n" https://mirrors.aliyun.com/

echo "测试Python官方源:"
time curl -o /dev/null -s -w "连接时间: %{time_connect}s, 总时间: %{time_total}s\n" https://pypi.org/

echo

# 2. 检查Docker配置
print_message $YELLOW "🐳 检查Docker配置..."

echo "Docker版本:"
docker version --format "{{.Server.Version}}"

echo "Docker存储驱动:"
docker info --format "{{.Driver}}"

echo "Docker根目录:"
docker info --format "{{.DockerRootDir}}"

echo "可用磁盘空间:"
df -h $(docker info --format "{{.DockerRootDir}}")

echo

# 3. 检查系统资源
print_message $YELLOW "💻 检查系统资源..."

echo "CPU信息:"
nproc
cat /proc/cpuinfo | grep "model name" | head -1

echo "内存信息:"
free -h

echo "磁盘IO性能测试:"
dd if=/dev/zero of=/tmp/test_write bs=1M count=100 2>&1 | grep -E "(copied|MB/s)"
rm -f /tmp/test_write

echo

# 4. 测试不同构建方式的速度
print_message $YELLOW "⚡ 测试不同构建方式..."

# 测试基础镜像拉取速度
print_message $BLUE "测试基础镜像拉取速度:"
time docker pull python:3.11-slim

# 测试简单构建
print_message $BLUE "测试极简Dockerfile构建:"
cat > /tmp/test.Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN echo "构建测试完成"
EOF

time docker build -f /tmp/test.Dockerfile -t test-build ./backend/
docker rmi test-build
rm /tmp/test.Dockerfile

echo

# 5. 给出建议
print_message $GREEN "💡 性能优化建议:"

echo "1. 如果网络慢，考虑:"
echo "   - 使用国内Docker镜像源"
echo "   - 使用国内Python包源"
echo "   - 在网络好的时候预先拉取基础镜像"

echo
echo "2. 如果磁盘IO慢，考虑:"
echo "   - 将Docker数据目录移到SSD"
echo "   - 清理Docker缓存: docker system prune -a"

echo
echo "3. 如果内存不足，考虑:"
echo "   - 增加虚拟内存"
echo "   - 减少并行构建数量"

echo
echo "4. 推荐的快速构建方案:"
echo "   - 使用 ./scripts/ultra-fast-dev.sh"
echo "   - 或者使用 docker-compose -f docker-compose.dev.yml up -d"

print_message $GREEN "✅ 诊断完成！"
