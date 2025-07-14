# ChatSphere 简化部署指南

## 🎯 方案概述

**方案 1：保持当前架构，但简化**
- 服务器只保留最小文件：`docker-compose.prod.yml` + 配置文件
- 不需要完整源码
- 通过 Docker Registry 拉取镜像
- 部署脚本只负责拉取镜像和重启服务

## 📋 部署流程

### 1. 服务器初始化（仅需执行一次）

在服务器上运行：

```bash
# 1. 上传初始化脚本到服务器
scp scripts/server-setup.sh user@49.232.202.209:~/

# 2. 在服务器上执行初始化
ssh user@49.232.202.209
sudo ./server-setup.sh your-docker-username
```

### 2. 配置密钥文件

```bash
# 在服务器上编辑密钥文件
cd /opt/chatsphere/secrets

# 编辑各个密钥文件
sudo nano postgres_password.txt    # PostgreSQL 密码
sudo nano redis_password.txt       # Redis 密码
sudo nano database_url.txt         # 数据库连接字符串
sudo nano redis_url.txt           # Redis 连接字符串
sudo nano secret_key.txt          # JWT 密钥
```

示例内容：
```bash
# postgres_password.txt
your_secure_postgres_password_123

# redis_password.txt
your_secure_redis_password_456

# database_url.txt
postgresql://chatsphere:your_secure_postgres_password_123@postgres:5432/chatsphere_prod

# redis_url.txt
redis://:your_secure_redis_password_456@redis:6379/0

# secret_key.txt
your_very_long_jwt_secret_key_at_least_32_characters_long
```

### 3. 上传部署脚本

```bash
# 上传部署脚本到服务器
scp scripts/deploy-simple.sh user@49.232.202.209:/opt/chatsphere/
ssh user@49.232.202.209
sudo chmod +x /opt/chatsphere/deploy-simple.sh
```

### 4. 首次部署

```bash
# 在服务器上执行首次部署
cd /opt/chatsphere
sudo ./deploy-simple.sh
```

## 🔄 CI/CD 自动部署

配置完成后，每次推送到 `main` 分支时，GitHub Actions 会自动：

1. 构建 Docker 镜像
2. 推送到 Docker Registry
3. 在服务器上执行 `deploy-simple.sh`
4. 完成滚动更新

## 📁 服务器文件结构

```
/opt/chatsphere/
├── docker-compose.prod.yml     # Docker Compose 配置
├── deploy-simple.sh           # 部署脚本
├── secrets/                   # 密钥文件目录
│   ├── README.md
│   ├── postgres_password.txt
│   ├── redis_password.txt
│   ├── database_url.txt
│   ├── redis_url.txt
│   └── secret_key.txt
├── nginx/                     # Nginx 配置
│   ├── prod.conf
│   └── nginx.conf
├── ssl/                       # SSL 证书（可选）
└── logs/                      # 日志目录
```

## 🛠️ 常用运维命令

```bash
# 查看服务状态
cd /opt/chatsphere
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 重启特定服务
docker-compose -f docker-compose.prod.yml restart backend

# 停止所有服务
docker-compose -f docker-compose.prod.yml down

# 手动部署
sudo ./deploy-simple.sh

# 查看镜像
docker images | grep chatsphere
```

## 🔧 故障排除

### 1. 部署脚本不存在
```bash
# 重新上传部署脚本
scp scripts/deploy-simple.sh user@49.232.202.209:/opt/chatsphere/
sudo chmod +x /opt/chatsphere/deploy-simple.sh
```

### 2. 密钥文件问题
```bash
# 检查密钥文件
cd /opt/chatsphere/secrets
ls -la
cat postgres_password.txt  # 确保文件不为空
```

### 3. Docker 登录问题
```bash
# 手动登录 Docker Registry
docker login -u your-username
```

### 4. 健康检查失败
```bash
# 查看具体服务日志
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs nginx
```

## 🔐 安全建议

1. **密钥管理**：
   - 使用强密码
   - 定期更换密钥
   - 限制密钥文件权限：`chmod 600 secrets/*`

2. **网络安全**：
   - 配置防火墙
   - 使用 HTTPS（配置 SSL 证书）
   - 限制 SSH 访问

3. **监控**：
   - 设置日志监控
   - 配置健康检查告警
   - 定期备份数据

## 📊 优势

✅ **简化维护**：服务器不需要源码和构建环境
✅ **快速部署**：只需拉取镜像，部署速度快
✅ **版本控制**：镜像版本化，易于回滚
✅ **环境一致**：开发、测试、生产环境完全一致
✅ **安全性**：减少服务器上的敏感文件
