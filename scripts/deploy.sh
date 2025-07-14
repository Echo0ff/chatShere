#!/bin/bash
# ChatSphere 部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印带颜色的消息
print_message() {
    echo -e "${1}${2}${NC}"
}

# 显示帮助信息
show_help() {
    echo "ChatSphere 部署脚本"
    echo
    echo "用法: $0 [环境] [选项]"
    echo
    echo "环境:"
    echo "  dev         开发环境"
    echo "  test        测试环境"
    echo "  prod        生产环境"
    echo
    echo "选项:"
    echo "  --build     强制重新构建镜像"
    echo "  --fast      使用快速构建（开发环境）"
    echo "  --clean     清理旧的容器和镜像"
    echo "  --monitoring 启动监控服务"
    echo "  --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 dev                    # 启动开发环境"
    echo "  $0 dev --fast            # 快速构建开发环境"
    echo "  $0 prod --build          # 重新构建并启动生产环境"
    echo "  $0 test --clean --build  # 清理、构建并启动测试环境"
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        print_message $RED "❌ Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "❌ Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    print_message $GREEN "✅ Docker 和 Docker Compose 已安装"
}

# 清理旧的容器和镜像
cleanup() {
    print_message $YELLOW "🧹 清理旧的容器和镜像..."
    
    # 停止并删除容器
    docker-compose -f docker-compose.${ENVIRONMENT}.yml down --remove-orphans || true
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷（谨慎使用）
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        docker volume prune -f
    fi
    
    print_message $GREEN "✅ 清理完成"
}

# 构建镜像
build_images() {
    print_message $YELLOW "🔨 构建 Docker 镜像..."

    if [[ "$ENVIRONMENT" == "dev" ]]; then
        if [[ "$FAST_BUILD" == true ]]; then
            print_message $BLUE "⚡ 使用快速构建模式..."
            # 启用 BuildKit 和缓存
            export DOCKER_BUILDKIT=1
            export COMPOSE_DOCKER_CLI_BUILD=1

            # 使用缓存构建
            docker-compose -f docker-compose.dev.yml build --parallel
        else
            docker-compose -f docker-compose.dev.yml build
        fi
    elif [[ "$ENVIRONMENT" == "test" ]]; then
        docker-compose -f docker-compose.test.yml build
    elif [[ "$ENVIRONMENT" == "prod" ]]; then
        # 生产环境检查密钥文件
        if [[ ! -d "secrets" ]] || [[ ! -f "secrets/secret_key.txt" ]]; then
            print_message $RED "❌ 生产环境需要密钥文件，请先运行 ./scripts/generate-secrets.sh"
            exit 1
        fi
        docker-compose -f docker-compose.prod.yml build
    fi

    print_message $GREEN "✅ 镜像构建完成"
}

# 启动服务
start_services() {
    print_message $YELLOW "🚀 启动 ChatSphere ${ENVIRONMENT} 环境..."
    
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        docker-compose -f docker-compose.dev.yml up -d
    elif [[ "$ENVIRONMENT" == "test" ]]; then
        docker-compose -f docker-compose.test.yml up -d
    elif [[ "$ENVIRONMENT" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml up -d
    fi
    
    print_message $GREEN "✅ 服务启动完成"
}

# 启动监控服务
start_monitoring() {
    print_message $YELLOW "📊 启动监控服务..."
    docker-compose -f docker-compose.monitoring.yml up -d
    print_message $GREEN "✅ 监控服务启动完成"
    print_message $BLUE "📊 Grafana: http://localhost:3001 (admin/admin123)"
    print_message $BLUE "📈 Prometheus: http://localhost:9090"
}

# 健康检查
health_check() {
    print_message $YELLOW "🔍 执行健康检查..."
    
    sleep 10  # 等待服务启动
    
    # 检查后端健康状态
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_message $GREEN "✅ 后端服务健康"
    else
        print_message $RED "❌ 后端服务不健康"
    fi
    
    # 检查前端（通过 Nginx）
    if [[ "$ENVIRONMENT" != "dev" ]]; then
        if curl -f http://localhost/health &> /dev/null; then
            print_message $GREEN "✅ 前端服务健康"
        else
            print_message $RED "❌ 前端服务不健康"
        fi
    fi
}

# 显示服务状态
show_status() {
    print_message $BLUE "📋 服务状态:"
    docker-compose -f docker-compose.${ENVIRONMENT}.yml ps
    
    echo
    print_message $BLUE "🌐 访问地址:"
    if [[ "$ENVIRONMENT" == "dev" ]]; then
        print_message $NC "前端: http://localhost:5173"
        print_message $NC "后端: http://localhost:8000"
        print_message $NC "API 文档: http://localhost:8000/docs"
    else
        print_message $NC "应用: http://localhost"
        print_message $NC "API 文档: http://localhost/api/docs"
    fi
}

# 主函数
main() {
    # 解析参数
    ENVIRONMENT=""
    BUILD=false
    FAST_BUILD=false
    CLEAN=false
    MONITORING=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|test|prod)
                ENVIRONMENT="$1"
                shift
                ;;
            --build)
                BUILD=true
                shift
                ;;
            --fast)
                FAST_BUILD=true
                BUILD=true  # 快速构建也需要构建
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --monitoring)
                MONITORING=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_message $RED "❌ 未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检查环境参数
    if [[ -z "$ENVIRONMENT" ]]; then
        print_message $RED "❌ 请指定环境: dev, test, 或 prod"
        show_help
        exit 1
    fi
    
    print_message $BLUE "🚀 ChatSphere 部署脚本 - ${ENVIRONMENT} 环境"
    echo
    
    # 检查依赖
    check_dependencies
    
    # 清理（如果需要）
    if [[ "$CLEAN" == true ]]; then
        cleanup
    fi
    
    # 构建镜像（如果需要）
    if [[ "$BUILD" == true ]]; then
        build_images
    fi
    
    # 启动服务
    start_services
    
    # 启动监控（如果需要）
    if [[ "$MONITORING" == true ]]; then
        start_monitoring
    fi
    
    # 健康检查
    health_check
    
    # 显示状态
    show_status
    
    echo
    print_message $GREEN "🎉 ChatSphere ${ENVIRONMENT} 环境部署完成！"
}

# 运行主函数
main "$@"
