# ChatSphere 后端 API

> 企业级实时聊天系统后端服务

## 🚀 项目概述

ChatSphere 后端是一个基于 FastAPI 的现代化实时聊天系统，提供WebSocket实时通信、用户认证、消息管理等核心功能。

### 主要特性

- 🔐 **JWT身份认证** - 安全的用户登录和权限管理
- 💬 **实时通信** - 基于WebSocket的实时消息传输
- 🏠 **多房间支持** - 支持公共房间、私聊、群组聊天
- 📊 **Redis缓存** - 高性能的在线状态和会话管理
- 🗄️ **PostgreSQL数据库** - 可靠的数据持久化
- 🔄 **异步处理** - 基于asyncio的高并发处理
- 📝 **自动文档** - FastAPI自动生成的API文档

## 🛠️ 技术栈

- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+
- **缓存**: Redis 7+
- **ORM**: SQLAlchemy 2.0+ (异步)
- **认证**: JWT (python-jose)
- **实时通信**: WebSocket
- **部署**: Uvicorn + Gunicorn

## 📋 系统要求

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- 8GB+ RAM (推荐)
- 2+ CPU核心

## ⚡ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd chatSphere/backend

# 安装Python依赖（推荐使用uv）
uv sync

# 或使用pip
pip install -e .
```

### 2. 数据库配置

```bash
# 启动PostgreSQL和Redis（使用Docker）
docker-compose up -d postgres redis

# 或手动启动服务
sudo systemctl start postgresql redis
```

### 3. 环境变量配置

创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/chatsphere
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=chatsphere

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS配置
ALLOWED_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### 4. 数据库初始化

```bash
# 运行数据库迁移
alembic upgrade head

# 可选：创建测试数据
python scripts/create_sample_data.py
```

### 5. 启动服务

```bash
# 开发模式
python -m uvicorn src.chatSphere.main:app --host 0.0.0.0 --port 8000 --reload

# 或使用项目脚本
python run.py

# 生产模式
gunicorn src.chatSphere.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📁 项目结构

```
backend/
├── src/chatSphere/          # 核心代码
│   ├── api/                 # API路由
│   │   └── routes/          # 路由定义
│   ├── core/                # 核心模块
│   │   ├── models.py        # 数据模型
│   │   ├── database.py      # 数据库配置
│   │   ├── cache.py         # Redis缓存
│   │   ├── auth.py          # 认证逻辑
│   │   └── websocket_manager.py  # WebSocket管理
│   └── services/            # 业务逻辑
├── tests/                   # 测试代码
├── scripts/                 # 工具脚本
├── deployment/              # 部署配置
├── docs/                    # 文档
├── pyproject.toml           # 项目配置
└── main.py                  # 应用入口
```

## 🔌 API 接口文档

启动服务后访问：
- **交互式文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **OpenAPI规范**: http://localhost:8000/openapi.json

### 主要接口

#### 认证相关
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新令牌
- `GET /auth/me` - 获取当前用户信息

#### 聊天相关
- `GET /chat/rooms` - 获取房间列表
- `GET /chat/messages/{chat_type}/{chat_id}` - 获取聊天消息
- `GET /chat/conversations` - 获取对话列表
- `GET /chat/online-users` - 获取在线用户

#### WebSocket
- `WS /ws` - WebSocket连接端点

## 🔄 WebSocket 消息格式

### 客户端发送格式

```json
{
  "type": "send_message",
  "data": {
    "content": "消息内容",
    "chat_type": "room|private|group", 
    "chat_id": "房间ID或用户ID",
    "message_type": "text|image",
    "reply_to_id": "回复消息ID（可选）"
  }
}
```

### 服务端推送格式

```json
{
  "type": "message",
  "data": {
    "id": "消息ID",
    "from_user_id": "发送者ID",
    "content": "消息内容",
    "chat_type": "room",
    "room_id": "房间ID",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🗄️ 数据库模型

### 用户表 (users)
- `id` - 用户ID (UUID)
- `username` - 用户名
- `email` - 邮箱
- `display_name` - 显示名称
- `password_hash` - 密码哈希
- `avatar_url` - 头像URL
- `is_active` - 是否激活
- `created_at` - 创建时间
- `last_seen` - 最后在线时间

### 消息表 (messages)
- `id` - 消息ID (UUID)
- `from_user_id` - 发送者ID
- `to_user_id` - 接收者ID (私聊)
- `room_id` - 房间ID (房间聊天)
- `group_id` - 群组ID (群组聊天)
- `content` - 消息内容
- `message_type` - 消息类型 (TEXT/IMAGE)
- `chat_type` - 聊天类型 (PRIVATE/ROOM/GROUP)
- `reply_to_id` - 回复消息ID
- `is_edited` - 是否已编辑
- `created_at` - 创建时间

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 📊 监控和日志

### 日志配置
- 开发环境：控制台输出 (INFO级别)
- 生产环境：文件输出 (WARNING级别)

### 健康检查
- `GET /health` - 服务健康状态
- `GET /health/db` - 数据库连接状态
- `GET /health/redis` - Redis连接状态

## 🚀 部署指南

### Docker部署

```bash
# 构建镜像
docker build -t chatsphere-backend .

# 运行容器
docker run -d \
  --name chatsphere-backend \
  -p 8000:8000 \
  --env-file .env \
  chatsphere-backend
```

### 使用Docker Compose

```bash
# 启动完整服务栈
docker-compose up -d
```

### 生产环境优化

1. **使用Gunicorn + Uvicorn Worker**
```bash
gunicorn src.chatSphere.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/chatsphere/access.log \
  --error-logfile /var/log/chatsphere/error.log
```

2. **Nginx反向代理**
```nginx
upstream chatsphere_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.chatsphere.com;
    
    location / {
        proxy_pass http://chatsphere_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /ws {
        proxy_pass http://chatsphere_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 🔧 故障排除

### 常见问题

1. **数据库连接失败**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U postgres -d chatsphere
```

2. **Redis连接失败**
```bash
# 检查Redis状态
sudo systemctl status redis

# 测试连接
redis-cli ping
```

3. **WebSocket连接问题**
- 检查CORS配置
- 确认防火墙设置
- 验证Nginx配置（如果使用）

### 性能调优

1. **数据库优化**
- 添加适当的索引
- 调整连接池大小
- 启用查询缓存

2. **Redis优化**
- 调整内存配置
- 设置合适的过期策略
- 启用持久化

## 📞 技术支持

- **问题报告**: [GitHub Issues](https://github.com/your-org/chatsphere/issues)
- **文档**: [项目文档](https://docs.chatsphere.com)
- **邮箱**: support@chatsphere.com

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

---

**ChatSphere Backend v2.0.0** - 构建现代化实时聊天体验 🚀 