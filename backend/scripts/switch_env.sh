#!/bin/bash

# ChatSphere 环境切换脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 显示帮助信息
show_help() {
    echo "ChatSphere 环境切换脚本"
    echo ""
    echo "用法: $0 [环境名称]"
    echo ""
    echo "支持的环境:"
    echo "  development  - 开发环境"
    echo "  testing      - 测试环境"
    echo "  production   - 生产环境"
    echo ""
    echo "示例:"
    echo "  $0 development"
    echo "  $0 production"
}

# 检查环境文件是否存在
check_env_file() {
    local env=$1
    local env_file=".env.${env}"

    if [ ! -f "$env_file" ]; then
        print_message $RED "错误: 环境文件 $env_file 不存在"
        exit 1
    fi
}

# 备份当前.env文件
backup_current_env() {
    if [ -f ".env" ]; then
        local timestamp=$(date +%Y%m%d_%H%M%S)
        cp .env ".env.backup.${timestamp}"
        print_message $YELLOW "已备份当前.env文件为 .env.backup.${timestamp}"
    fi
}

# 切换环境
switch_environment() {
    local env=$1
    local env_file=".env.${env}"

    print_message $BLUE "切换到 ${env} 环境..."

    # 检查环境文件
    check_env_file $env

    # 备份当前环境
    backup_current_env

    # 复制新环境文件
    cp "$env_file" ".env"
    print_message $GREEN "✓ 已切换到 ${env} 环境"

    # 显示当前环境信息
    show_current_env
}

# 显示当前环境信息
show_current_env() {
    if [ -f ".env" ]; then
        local current_env=$(grep "^ENVIRONMENT=" .env | cut -d'=' -f2)
        local debug=$(grep "^DEBUG=" .env | cut -d'=' -f2)
        local db_host=$(grep "^POSTGRES_HOST=" .env | cut -d'=' -f2)
        local redis_host=$(grep "^REDIS_HOST=" .env | cut -d'=' -f2)

        echo ""
        print_message $BLUE "当前环境信息:"
        echo "  环境: $current_env"
        echo "  调试模式: $debug"
        echo "  数据库主机: $db_host"
        echo "  Redis主机: $redis_host"
    else
        print_message $YELLOW "未找到.env文件"
    fi
}

# 验证环境设置
validate_environment() {
    local env=$1

    print_message $BLUE "验证 ${env} 环境设置..."

    case $env in
        "production")
            # 检查生产环境关键配置
            if grep -q "SECRET_KEY=your-secret-key" .env; then
                print_message $RED "警告: 生产环境SECRET_KEY未更改"
            fi
            if grep -q "DEBUG=true" .env; then
                print_message $RED "警告: 生产环境不应启用DEBUG模式"
            fi
            ;;
        "development")
            if grep -q "DEBUG=false" .env; then
                print_message $YELLOW "提示: 开发环境建议启用DEBUG模式"
            fi
            ;;
    esac

    print_message $GREEN "✓ 环境验证完成"
}

# 重启服务
restart_services() {
    local env=$1

    print_message $BLUE "重启服务以应用新环境..."

    # 停止现有服务
    if [ "$env" = "production" ]; then
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    else
        docker-compose down 2>/dev/null || true
    fi

    # 启动服务
    if [ "$env" = "production" ]; then
        docker-compose -f docker-compose.prod.yml up -d
    else
        docker-compose up -d postgres redis
    fi

    print_message $GREEN "✓ 服务已重启"
}

# 主函数
main() {
    # 检查参数
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi

    local environment=$1

    # 验证环境名称
    case $environment in
        "development"|"testing"|"production")
            ;;
        *)
            print_message $RED "错误: 不支持的环境 '$environment'"
            show_help
            exit 1
            ;;
    esac

    # 切换环境
    switch_environment $environment

    # 验证环境设置
    validate_environment $environment

    # 询问是否重启服务
    read -p "是否重启服务以应用新环境? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_services $environment
    fi

    echo ""
    print_message $GREEN "环境切换完成! 🎉"
    print_message $BLUE "提示: 如果是首次切换到此环境，请运行数据库初始化："
    print_message $BLUE "  python scripts/setup.py"
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
