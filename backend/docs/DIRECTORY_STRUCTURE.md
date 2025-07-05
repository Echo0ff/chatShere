# ChatSphere 后端目录结构

## 项目结构

```
backend/
├── src/                          # 源代码目录
│   └── chatSphere/              # 主包
│       ├── core/                # 核心模块
│       │   ├── __init__.py
│       │   ├── models.py        # 数据模型
│       │   ├── database.py      # 数据库管理
│       │   ├── auth.py          # 认证系统
│       │   ├── cache.py         # Redis缓存
│       │   ├── middleware.py    # 中间件
│       │   └── websocket_manager.py # WebSocket管理
│       ├── api/                 # API路由
│       │   ├── __init__.py
│       │   └── routes/          # 路由模块
│       │       ├── __init__.py
│       │       └── auth.py      # 认证路由
│       ├── services/            # 服务层
│       │   ├── __init__.py
│       │   ├── responses.py     # 统一响应格式
│       │   └── services.py      # 业务服务
│       └── __init__.py
├── docs/                        # 文档目录
│   ├── DIRECTORY_STRUCTURE.md   # 目录结构说明
│   ├── README.md                # 后端说明文档
│   ├── test_guide.md            # 测试指南
│   ├── DEPLOYMENT.md            # 部署文档
│   └── PRODUCTION_DEPLOYMENT.md # 生产环境部署
├── deployment/                  # 部署相关文件
│   ├── docker/                  # Docker配置
│   │   ├── Dockerfile           # 开发环境Docker文件
│   │   ├── Dockerfile.staging   # 预发布环境
│   │   ├── Dockerfile.prod      # 生产环境
│   │   ├── docker-compose.yml   # 开发环境组合
│   │   ├── docker-compose.staging.yml # 预发布环境
│   │   └── docker-compose.prod.yml    # 生产环境
│   └── nginx/                   # Nginx配置
│       ├── staging.conf         # 预发布配置
│       └── prod.conf            # 生产配置
├── scripts/                     # 脚本目录
│   ├── switch_env.sh            # 环境切换脚本
│   ├── deploy.py                # 自动部署脚本
│   ├── server-setup.sh          # 服务器初始化
│   ├── manual-deploy.sh         # 手动部署脚本
│   └── setup.py                 # 项目初始化脚本
├── tests/                       # 测试目录
├── .github/                     # GitHub Actions
│   └── workflows/
│       └── deploy-staging.yml   # CI/CD配置
├── config.py                    # 配置文件
├── main.py                      # 应用入口
├── run.py                       # 快速启动脚本
├── test_client.py               # 测试客户端
├── pyproject.toml               # 项目配置
├── uv.lock                      # 依赖锁定文件
├── .gitignore                   # Git忽略文件
├── .python-version              # Python版本
└── .venv/                       # 虚拟环境
```

## 主要组件说明

### 1. 核心模块 (src/chatSphere/core/)

- **models.py**: 数据模型定义，包含用户、消息、房间等实体
- **database.py**: 数据库连接管理、事务装饰器、基础仓库类
- **auth.py**: JWT认证、OAuth2登录、用户管理
- **cache.py**: Redis缓存管理、会话存储、速率限制
- **middleware.py**: 自定义中间件（日志、安全、限流等）
- **websocket_manager.py**: WebSocket连接管理、实时通信

### 2. API路由 (src/chatSphere/api/)

- **routes/auth.py**: 认证相关API（注册、登录、Token管理）
- 将来可扩展：用户管理、聊天消息、房间管理等路由

### 3. 服务层 (src/chatSphere/services/)

- **responses.py**: 统一的API响应格式、状态码定义
- **services.py**: 业务逻辑服务类

### 4. 部署配置 (deployment/)

- **docker/**: 多环境Docker配置文件
- **nginx/**: Nginx反向代理配置

### 5. 脚本工具 (scripts/)

- 环境管理、部署自动化、服务器配置等实用脚本

## 设计原则

1. **分层架构**: 明确的核心层、API层、服务层划分
2. **模块化**: 功能模块独立，依赖关系清晰
3. **可扩展性**: 易于添加新的路由、服务和功能
4. **环境隔离**: 开发、预发布、生产环境配置分离
5. **文档完整**: 每个目录和组件都有明确的职责说明

## 开发工作流

1. **添加新功能**: 在 `src/chatSphere/core/` 添加核心逻辑
2. **创建API**: 在 `src/chatSphere/api/routes/` 添加路由
3. **业务服务**: 在 `src/chatSphere/services/` 添加服务类
4. **测试**: 在 `tests/` 添加单元测试和集成测试
5. **文档**: 更新相关文档

## 注意事项

- 所有模块使用相对导入，确保包结构清晰
- 配置文件统一管理，支持多环境配置
- 统一的错误处理和响应格式
- 完整的日志记录和监控 