# 🚀 ChatSphere - 企业级实时聊天系统

一个基于 FastAPI 的现代化企业级聊天应用，集成了 JWT 认证、OAuth2 登录、WebSocket 实时通信、Redis 缓存、PostgreSQL 数据库和自定义中间件技术。

## ✨ 核心功能

### 🔐 认证系统
- **JWT Token 认证**：安全的访问令牌和刷新令牌机制
- **OAuth2 集成**：支持 Google 和 GitHub 第三方登录
- **用户管理**：注册、登录、资料更新、密码修改
- **Token 管理**：撤销、黑名单、自动过期

### 💬 聊天功能
- **实时通信**：基于 WebSocket 的即时消息传输
- **多种聊天类型**：私聊、群聊、公开房间
- **消息状态**：已发送、已送达、已读状态跟踪
- **在线状态**：实时显示用户在线/离线状态

### 🗄️ 数据持久化
- **PostgreSQL**：关系型数据库存储用户、消息、会话数据
- **Redis 缓存**：高性能缓存用户会话、在线状态、消息缓存
- **事务支持**：自动事务管理确保数据一致性

### 🛡️ 安全与性能
- **自定义中间件**：速率限制、安全头部、请求日志、错误处理
- **用户活动跟踪**：监控用户行为和连接状态
- **缓存策略**：智能缓存提升应用性能

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   Mobile App    │    │  Third Party    │
│   (React/Vue)   │    │   (Flutter)     │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
              ┌─────────────────────────────────────────┐
              │             Nginx (Optional)            │
              │          Load Balancer/Proxy            │
              └─────────────────────────────────────────┘
                                 │
              ┌─────────────────────────────────────────┐
              │              FastAPI App                │
              │  ┌─────────────┬─────────────────────┐  │
              │  │   REST API  │   WebSocket API     │  │
              │  │             │                     │  │
              │  │ JWT/OAuth2  │  Real-time Chat     │  │
              │  │ CRUD Ops    │  Connection Mgmt    │  │
              │  └─────────────┴─────────────────────┘  │
              │  ┌─────────────────────────────────────┐ │
              │  │          Middleware Stack           │ │
              │  │ Rate Limit │ Security │ Logging    │ │
              │  └─────────────────────────────────────┘ │
              └─────────────────────────────────────────┘
                         │              │
              ┌─────────────────┐    ┌──────────────┐
              │   PostgreSQL    │    │    Redis     │
              │   Primary DB    │    │    Cache     │
              │                 │    │              │
              │ • Users         │    │ • Sessions   │
              │ • Messages      │    │ • Online     │
              │ • Rooms/Groups  │    │ • Rate Limit │
              │ • Read Status   │    │ • Messages   │
              └─────────────────┘    └──────────────┘
```

## 📁 项目结构

```
backend/
├── main.py                 # 🚀 应用入口点
├── config.py              # ⚙️ 应用配置
├── models.py              # 📊 数据库模型
├── database.py            # 🗄️ 数据库连接管理
├── cache.py               # 🚀 Redis 缓存管理
├── auth.py                # 🔐 JWT/OAuth2 认证
├── middleware.py          # 🛡️ 自定义中间件
├── websocket_manager.py   # 💬 WebSocket 连接管理
├── routes/
│   ├── __init__.py
│   └── auth.py           # 🔑 认证相关路由
├── pyproject.toml         # 📦 项目依赖
├── docker-compose.yml     # 🐳 Docker 编排
├── Dockerfile            # 🐳 Docker 镜像
└── README.md             # 📖 项目文档
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (可选)

### 1. 克隆项目
```bash
git clone <repository-url>
cd chatsphere/backend
```

### 2. 配置环境变量
```bash
# 复制环境配置模板
cp .env.example .env

# 编辑环境变量
vim .env
```

### 3. 方式一：本地开发
```bash
# 安装依赖
pip install -e .

# 启动 PostgreSQL 和 Redis (macOS)
brew services start postgresql
brew services start redis

# 运行应用
uvicorn main:app --reload
```

### 4. 方式二：Docker 部署
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f chatsphere
```

## 📡 API 接口

### 认证接口
```http
POST /api/v1/auth/register      # 用户注册
POST /api/v1/auth/login         # 用户登录
POST /api/v1/auth/oauth2/login  # OAuth2 登录
POST /api/v1/auth/token/refresh # 刷新 Token
POST /api/v1/auth/logout        # 用户登出
GET  /api/v1/auth/me           # 获取用户信息
PUT  /api/v1/auth/me           # 更新用户资料
```

### 聊天接口
```http
GET  /api/v1/conversations           # 获取会话列表
GET  /api/v1/messages/{type}/{id}    # 获取聊天记录
GET  /api/v1/users/online           # 获取在线用户
GET  /api/v1/rooms                  # 获取公开房间
```

### WebSocket 连接
```javascript
// 连接 WebSocket
const ws = new WebSocket('ws://localhost:8000/ws?token=YOUR_JWT_TOKEN');

// 发送消息
ws.send(JSON.stringify({
    type: 'chat',
    content: 'Hello, World!',
    room_id: 'general'
}));
```

## 🔧 核心组件详解

### 1. 认证系统 (`auth.py`)
```python
# JWT Token 生成和验证
auth_manager = AuthManager()
token = auth_manager.create_access_token(user_data)

# OAuth2 第三方登录
oauth_manager = OAuth2Manager()
user_info = await oauth_manager.get_google_user_info(access_token)
```

### 2. WebSocket 管理 (`websocket_manager.py`)
```python
# 连接管理
connection_manager = ConnectionManager()
await connection_manager.connect(websocket, user, session)

# 消息广播
await connection_manager.handle_message(user_id, message_data, session)
```

### 3. 缓存系统 (`cache.py`)
```python
# 用户会话缓存
await cache_manager.cache_user_session(user_id, session_data)

# 在线状态管理
await cache_manager.cache_user_online_status(user_id, True)
```

### 4. 自定义中间件 (`middleware.py`)
```python
# 速率限制
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 安全头部
app.add_middleware(SecurityHeadersMiddleware)

# 请求日志
app.add_middleware(RequestLoggingMiddleware)
```

## 🛡️ 安全特性

- **JWT 黑名单**：支持 Token 撤销和黑名单机制
- **速率限制**：防止 API 滥用和 DDoS 攻击
- **CORS 配置**：精确控制跨域访问权限
- **安全头部**：自动添加安全相关 HTTP 头部
- **密码加密**：使用 bcrypt 安全存储用户密码
- **输入验证**：Pydantic 模型验证所有输入数据

## 📊 性能优化

- **连接池**：数据库和 Redis 连接池管理
- **异步处理**：全异步架构提升并发性能
- **智能缓存**：多层缓存策略减少数据库压力
- **消息队列**：Redis 实现高效消息传递
- **WebSocket 优化**：连接复用和自动重连

## 🔍 监控与日志

- **结构化日志**：详细的请求和错误日志记录
- **健康检查**：内置健康检查端点
- **性能监控**：请求处理时间和资源使用监控
- **用户活动跟踪**：实时用户行为分析

## 🧪 测试

```bash
# 运行测试
pytest

# 覆盖率测试
pytest --cov=.

# 压力测试
locust -f tests/load_test.py
```

## 🚀 部署

### 生产环境建议
1. 使用 HTTPS/WSS 加密传输
2. 配置 Nginx 反向代理和负载均衡
3. 使用 PostgreSQL 主从复制
4. Redis 集群部署
5. 容器编排 (Kubernetes)
6. 日志聚合和监控 (ELK Stack)

### 环境变量配置
```bash
# 生产环境必须修改
SECRET_KEY=your-super-secure-secret-key
POSTGRES_PASSWORD=strong-database-password
REDIS_PASSWORD=strong-redis-password

# OAuth2 配置
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [SQLAlchemy](https://sqlalchemy.org/) - 强大的 ORM 工具
- [Redis](https://redis.io/) - 高性能内存数据库
- [PostgreSQL](https://postgresql.org/) - 可靠的关系型数据库

---

**🎉 ChatSphere - 让沟通更简单，让连接更紧密！**
