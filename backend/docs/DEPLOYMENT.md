# ChatSphere 部署指南

这个指南将帮助你在不同环境中部署ChatSphere应用。

## 环境说明

### 支持的环境

1. **Development (开发环境)**
   - 用于本地开发和调试
   - 启用调试模式和代码热重载
   - 使用本地数据库和缓存

2. **Testing (测试环境)**
   - 用于自动化测试
   - 使用独立的测试数据库
   - 严格的配置用于测试一致性

3. **Production (生产环境)**
   - 用于实际部署
   - 优化的性能和安全配置
   - 包含监控和负载均衡

## 快速开始

### 1. 环境切换

使用shell脚本快速切换环境：

```bash
# 切换到开发环境
./scripts/switch_env.sh development

# 切换到生产环境
./scripts/switch_env.sh production
```

### 2. 使用Python部署脚本

```bash
# 部署开发环境
python scripts/deploy.py development

# 部署生产环境
python scripts/deploy.py production

# 停止服务
python scripts/deploy.py production --action stop

# 备份数据库
python scripts/deploy.py production --action backup
```

## 详细部署步骤

### 开发环境部署

1. **环境准备**
   ```bash
   # 复制环境配置
   cp .env.development .env
   
   # 或使用脚本
   ./scripts/switch_env.sh development
   ```

2. **启动基础服务**
   ```bash
   # 启动PostgreSQL和Redis
   docker-compose up -d postgres redis
   ```

3. **初始化数据库**
   ```bash
   # 运行数据库迁移
   python scripts/setup.py
   ```

4. **启动应用**
   ```bash
   # 开发模式启动
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 测试环境部署

1. **环境设置**
   ```bash
   ./scripts/switch_env.sh testing
   ```

2. **运行测试**
   ```bash
   python scripts/deploy.py testing
   ```

### 生产环境部署

#### 前置要求

1. **服务器要求**
   - Linux系统 (推荐Ubuntu 20.04+)
   - Docker和Docker Compose
   - 至少2GB RAM
   - 20GB可用磁盘空间

2. **域名和SSL证书**
   - 已解析的域名
   - SSL证书文件 (cert.pem, key.pem)

#### 部署步骤

1. **克隆代码**
   ```bash
   git clone <your-repo>
   cd chatSphere/backend
   ```

2. **环境配置**
   ```bash
   # 复制生产环境配置
   cp .env.production .env
   
   # 编辑生产环境配置
   nano .env
   ```

   **重要配置项：**
   ```env
   # 必须修改的配置
   SECRET_KEY=your-super-strong-secret-key-at-least-32-characters
   POSTGRES_PASSWORD=your-strong-production-password
   REDIS_PASSWORD=your-redis-password
   
   # 域名配置
   ALLOWED_ORIGINS=["https://yourdomain.com"]
   
   # OAuth2配置 (可选)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

3. **SSL证书设置**
   ```bash
   # 创建SSL目录
   mkdir -p ssl
   
   # 复制你的SSL证书
   cp /path/to/your/cert.pem ssl/
   cp /path/to/your/key.pem ssl/
   ```

4. **Nginx配置**
   ```bash
   # 编辑Nginx配置，替换域名
   nano nginx/prod.conf
   ```

5. **部署应用**
   ```bash
   # 自动化部署
   python scripts/deploy.py production
   
   # 或手动部署
   docker-compose -f docker-compose.prod.yml build
   docker-compose -f docker-compose.prod.yml up -d
   ```

6. **验证部署**
   ```bash
   # 检查服务状态
   docker-compose -f docker-compose.prod.yml ps
   
   # 查看日志
   docker-compose -f docker-compose.prod.yml logs -f chatsphere
   
   # 健康检查
   curl -f https://yourdomain.com/health
   ```

## 环境配置说明

### 开发环境 (.env.development)
- DEBUG=true (启用调试模式)
- RELOAD=true (代码热重载)
- 宽松的速率限制
- 详细的日志输出

### 生产环境 (.env.production)
- DEBUG=false (关闭调试模式)
- 强密码和密钥
- 严格的CORS设置
- 优化的性能配置

## 监控和维护

### 查看日志
```bash
# 应用日志
docker-compose -f docker-compose.prod.yml logs -f chatsphere

# Nginx日志
docker-compose -f docker-compose.prod.yml logs -f nginx

# 数据库日志
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### 数据库备份
```bash
# 自动备份
python scripts/deploy.py production --action backup

# 手动备份
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres chatsphere > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 性能监控
访问以下地址查看监控信息：
- Prometheus: http://yourdomain.com:9090
- Grafana: http://yourdomain.com:3000

### 更新应用
```bash
# 拉取最新代码
git pull origin main

# 重新构建和部署
docker-compose -f docker-compose.prod.yml build chatsphere
docker-compose -f docker-compose.prod.yml up -d chatsphere
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查PostgreSQL服务状态
   - 验证数据库连接参数
   - 确保数据库已初始化

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证Redis密码配置

3. **WebSocket连接问题**
   - 检查Nginx WebSocket配置
   - 验证防火墙设置

4. **SSL证书问题**
   - 确保证书文件路径正确
   - 检查证书是否过期

### 获取帮助
```bash
# 查看部署脚本帮助
python scripts/deploy.py --help

# 查看环境切换帮助
./scripts/switch_env.sh
```

## 安全建议

1. **生产环境安全**
   - 使用强密码和密钥
   - 定期更新SSL证书
   - 配置防火墙规则
   - 定期备份数据

2. **访问控制**
   - 限制数据库访问
   - 使用非root用户运行服务
   - 配置适当的CORS策略

3. **监控和日志**
   - 启用应用监控
   - 定期检查日志
   - 设置异常告警

## 扩展性

### 水平扩展
```yaml
# 在docker-compose.prod.yml中增加实例
chatsphere:
  deploy:
    replicas: 4  # 运行4个实例
```

### 负载均衡
Nginx配置已包含负载均衡设置，可以轻松添加更多后端实例。

### 数据库优化
- 配置PostgreSQL连接池
- 设置适当的缓存策略
- 定期优化数据库查询 