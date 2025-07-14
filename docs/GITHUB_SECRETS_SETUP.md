# GitHub Secrets 配置指南

## 🔐 需要配置的 GitHub Secrets

在你的 GitHub 仓库中，进入 `Settings` → `Secrets and variables` → `Actions`，添加以下 Repository secrets：

### 1. 服务器连接相关
```
SERVER_USERNAME=ubuntu
SERVER_SSH_KEY=<你的私钥内容>
```

### 2. Docker Registry 相关
```
DOCKER_USERNAME=<你的Docker Hub用户名>
DOCKER_PASSWORD=<你的Docker Hub密码或Token>
```

### 3. 数据库相关
```
POSTGRES_PASSWORD=<PostgreSQL数据库密码>
```
示例：`your_secure_postgres_password_123`

### 4. Redis 相关
```
REDIS_PASSWORD=<Redis密码>
```
示例：`your_secure_redis_password_456`

### 5. JWT 密钥
```
JWT_SECRET_KEY=<JWT密钥>
```
示例：`your_very_long_jwt_secret_key_at_least_32_characters_long`

## 🛠️ 快速生成密钥命令

你可以使用以下命令生成安全的密钥：

```bash
# 生成 PostgreSQL 密码
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25

# 生成 Redis 密码
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25

# 生成 JWT 密钥
openssl rand -base64 64 | tr -d "=+/" | cut -c1-64
```

## 📋 配置步骤

1. **进入 GitHub 仓库设置**
   - 打开你的 GitHub 仓库
   - 点击 `Settings` 标签
   - 在左侧菜单中选择 `Secrets and variables` → `Actions`

2. **添加 Repository secrets**
   - 点击 `New repository secret`
   - 输入 Secret 名称和值
   - 点击 `Add secret`

3. **验证配置**
   - 确保所有必需的 secrets 都已添加
   - 检查 secret 名称是否与 workflow 文件中的引用一致

## 🔍 Secrets 列表检查

确保你已经添加了以下所有 secrets：

- [ ] `SERVER_USERNAME`
- [ ] `SERVER_SSH_KEY`
- [ ] `DOCKER_USERNAME`
- [ ] `DOCKER_PASSWORD`
- [ ] `POSTGRES_PASSWORD`
- [ ] `REDIS_PASSWORD`
- [ ] `JWT_SECRET_KEY`

## 🚀 部署流程

配置完成后，每次推送到 `main` 分支时，GitHub Actions 会自动：

1. 构建 Docker 镜像
2. 推送镜像到 Docker Hub
3. 连接到服务器
4. 创建/更新 docker-compose.prod.yml
5. 拉取最新镜像
6. 滚动更新服务
7. 进行健康检查

## ⚠️ 安全注意事项

1. **SSH 密钥安全**
   - 使用专用的部署密钥
   - 定期轮换密钥
   - 限制密钥权限

2. **密码强度**
   - 使用强密码
   - 避免使用默认密码
   - 定期更换密码

3. **访问控制**
   - 限制仓库访问权限
   - 定期审查协作者权限
   - 使用分支保护规则

## 🔧 故障排除

### 1. SSH 连接失败
- 检查 `SERVER_SSH_KEY` 格式是否正确
- 确保服务器允许密钥认证
- 验证用户名是否正确

### 2. Docker 登录失败
- 检查 `DOCKER_USERNAME` 和 `DOCKER_PASSWORD`
- 确认 Docker Hub 账户状态
- 考虑使用 Access Token 而不是密码

### 3. 服务启动失败
- 检查数据库和 Redis 密码
- 验证 JWT 密钥长度
- 查看 GitHub Actions 日志

## 📞 获取帮助

如果遇到问题，请检查：
1. GitHub Actions 运行日志
2. 服务器上的 Docker 日志
3. 确认所有 secrets 都已正确配置
