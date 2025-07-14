# ChatSphere 部署指南

本文档详细介绍了 ChatSphere 项目的 Docker 化部署流程，包括开发、测试和生产环境的配置。

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [部署流程](#部署流程)
- [监控和维护](#监控和维护)
- [故障排除](#故障排除)

## 🔧 系统要求

### 最低要求
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: Linux (Ubuntu 20.04+ 推荐)

### 推荐配置
- **CPU**: 4 核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **网络**: 100Mbps 带宽

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/your-org/chatSphere.git
cd chatSphere
```

### 2. 选择环境部署

#### 开发环境
```bash
./scripts/deploy.sh dev
```

#### 测试环境
```bash
./scripts/deploy.sh test --build
```

#### 生产环境
```bash
# 首先生成密钥
./scripts/generate-secrets.sh

# 部署生产环境
./scripts/deploy.sh prod --build
```

### 3. 访问应用

| 环境 | 前端地址 | 后端地址 | API 文档 |
|------|----------|----------|----------|
| 开发 | http://localhost:5173 | http://localhost:8000 | http://localhost:8000/docs |
| 测试 | http://localhost | http://localhost/api | http://localhost/api/docs |
| 生产 | https://yourdomain.com | https://yourdomain.com/api | https://yourdomain.com/api/docs |

## ⚙️ 环境配置

### 开发环境 (Development)
- **目的**: 本地开发和调试
- **特点**: 热重载、详细日志、开发工具
- **配置文件**: `docker-compose.dev.yml`

### 测试环境 (Testing)
- **目的**: 集成测试和预发布验证
- **特点**: 生产级配置、性能测试
- **配置文件**: `docker-compose.test.yml`

### 生产环境 (Production)
- **目的**: 正式生产服务
- **特点**: 高可用、安全加固、监控告警
- **配置文件**: `docker-compose.prod.yml`

## 🔐 密钥管理

### 生成密钥
```bash
./scripts/generate-secrets.sh
```

### 密钥文件说明
- `secrets/postgres_password.txt` - PostgreSQL 密码
- `secrets/redis_password.txt` - Redis 密码
- `secrets/secret_key.txt` - 应用密钥
- `secrets/database_url.txt` - 数据库连接字符串
- `secrets/redis_url.txt` - Redis 连接字符串

### 安全注意事项
1. 密钥文件权限设置为 600
2. 不要将密钥文件提交到版本控制
3. 定期轮换生产环境密钥
4. 使用安全的传输方式部署密钥

## 🐳 Docker 配置详解

### 多阶段构建
每个 Dockerfile 都支持多阶段构建：
- `development` - 开发环境，包含开发工具
- `testing` - 测试环境，运行测试用例
- `production` - 生产环境，优化的运行时镜像

### 健康检查
所有服务都配置了健康检查：
- **后端**: `GET /health`
- **前端**: `GET /` (通过 Nginx)
- **数据库**: `pg_isready`
- **缓存**: `redis-cli ping`

### 资源限制
生产环境配置了资源限制：
- **后端**: 1GB 内存，1 CPU 核心
- **前端**: 256MB 内存，0.25 CPU 核心
- **数据库**: 1GB 内存，0.5 CPU 核心
- **缓存**: 512MB 内存，0.25 CPU 核心

## 📊 监控和维护

### 启动监控服务
```bash
./scripts/deploy.sh prod --monitoring
```

### 监控组件
- **Prometheus**: 指标收集 (http://localhost:9090)
- **Grafana**: 可视化面板 (http://localhost:3001)
- **Alertmanager**: 告警管理 (http://localhost:9093)
- **Node Exporter**: 系统监控
- **cAdvisor**: 容器监控

### 关键指标
- CPU 使用率
- 内存使用率
- 磁盘空间
- 网络流量
- 数据库连接数
- Redis 连接数
- HTTP 响应时间
- WebSocket 连接数

### 日志管理
```bash
# 查看服务日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 查看所有服务日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看特定时间段日志
docker-compose -f docker-compose.prod.yml logs --since="2024-01-01T00:00:00" backend
```

## 🔄 CI/CD 流程

### GitHub Actions 工作流
1. **代码检查**: 代码质量检查和测试
2. **镜像构建**: 构建 Docker 镜像并推送到仓库
3. **自动部署**: 部署到测试/生产环境
4. **健康检查**: 验证部署是否成功
5. **通知**: 发送部署结果通知

### 分支策略
- `main` 分支 → 生产环境
- `develop` 分支 → 测试环境
- 功能分支 → Pull Request 触发测试

### 部署密钥配置
在 GitHub Secrets 中配置以下密钥：
- `DOCKER_USERNAME` - Docker Hub 用户名
- `DOCKER_PASSWORD` - Docker Hub 密码
- `TEST_SERVER_HOST` - 测试服务器地址
- `TEST_SERVER_USERNAME` - 测试服务器用户名
- `TEST_SERVER_SSH_KEY` - 测试服务器 SSH 私钥
- `PROD_SERVER_HOST` - 生产服务器地址
- `PROD_SERVER_USERNAME` - 生产服务器用户名
- `PROD_SERVER_SSH_KEY` - 生产服务器 SSH 私钥

## 🛠️ 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 检查容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看容器日志
docker-compose -f docker-compose.prod.yml logs backend

# 重启服务
docker-compose -f docker-compose.prod.yml restart backend
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# 检查数据库日志
docker-compose -f docker-compose.prod.yml logs postgres

# 重置数据库连接
docker-compose -f docker-compose.prod.yml restart postgres
```

#### 3. 前端无法访问后端
```bash
# 检查网络连接
docker network ls
docker network inspect chatsphere-prod-network

# 检查 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 重新加载 Nginx 配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

#### 4. 性能问题
```bash
# 检查资源使用情况
docker stats

# 检查系统资源
htop
iotop
nethogs

# 查看监控面板
# 访问 Grafana: http://localhost:3001
```

### 备份和恢复

#### 数据库备份
```bash
# 创建备份
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U chatsphere chatsphere_prod > backup.sql

# 恢复备份
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U chatsphere chatsphere_prod < backup.sql
```

#### 文件备份
```bash
# 备份上传文件
docker cp chatsphere-backend-prod:/app/uploads ./uploads-backup

# 恢复上传文件
docker cp ./uploads-backup chatsphere-backend-prod:/app/uploads
```

## 📞 支持

如果遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查 GitHub Issues
3. 联系开发团队

---

**注意**: 本文档会随着项目发展持续更新，请定期查看最新版本。
