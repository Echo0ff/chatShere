# 🚀 ChatSphere 公网服务器部署指南

本指南详细介绍如何在公网服务器 `49.232.202.209` 上部署 ChatSphere，并设置完整的 CI/CD 流程。

## 📋 部署概览

### 🎯 部署策略

我们采用**三环境架构**：

1. **Development** - 本地开发环境
2. **Staging** - 公网预发布环境 (49.232.202.209)
3. **Production** - 生产环境 (有域名时使用)

### 🔧 技术栈

- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Prometheus + Grafana + Portainer
- **CI/CD**: GitHub Actions
- **数据库**: PostgreSQL + Redis

## 🛠️ 一、服务器环境初始化

### 1.1 自动初始化（推荐）

在服务器上运行初始化脚本：

```bash
# 登录服务器
ssh root@49.232.202.209

# 下载并运行初始化脚本
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/chatSphere/main/backend/scripts/server-setup.sh | bash
```

### 1.2 手动初始化

如果需要手动设置，请按以下步骤：

```bash
# 更新系统
apt update && apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 配置防火墙
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp  # Grafana
ufw allow 9000/tcp  # Portainer
ufw --force enable
```

## 🔐 二、配置 GitHub Actions CI/CD

### 2.1 配置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

```
Settings > Secrets and variables > Actions > New repository secret
```

**必需的 Secrets：**

- `SSH_PRIVATE_KEY`: 服务器 SSH 私钥
- `SERVER_HOST`: 49.232.202.209
- `SERVER_USER`: root

### 2.2 生成 SSH 密钥

在本地生成 SSH 密钥对：

```bash
# 生成密钥对
ssh-keygen -t ed25519 -C "github-actions@chatsphere" -f ~/.ssh/chatsphere_deploy

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/chatsphere_deploy.pub root@49.232.202.209

# 将私钥内容复制到 GitHub Secrets
cat ~/.ssh/chatsphere_deploy
```

### 2.3 CI/CD 工作流说明

GitHub Actions 工作流 (`.github/workflows/deploy-staging.yml`) 包含：

1. **测试阶段**: 运行单元测试和集成测试
2. **构建阶段**: 构建 Docker 镜像并推送到 GitHub Container Registry
3. **部署阶段**: 自动部署到预发布服务器
4. **通知阶段**: 发送部署状态通知

**触发条件：**
- 推送到 `main` 或 `develop` 分支
- 创建针对 `main` 分支的 Pull Request

## 🚀 三、部署方式

### 3.1 自动部署（推荐）

推送代码到 GitHub 自动触发部署：

```bash
# 推送到主分支触发部署
git add .
git commit -m "feat: 新功能"
git push origin main
```

### 3.2 手动部署

使用部署脚本进行手动部署：

```bash
# 本地部署到远程服务器
./scripts/manual-deploy.sh local

# 在远程服务器上直接部署
./scripts/manual-deploy.sh remote

# 部署指定分支
./scripts/manual-deploy.sh remote develop
```

### 3.3 首次部署步骤

1. **修改配置文件**：
   ```bash
   # 编辑预发布环境配置
   nano backend/.env.staging
   
   # 重要：修改以下配置
   SECRET_KEY=staging-strong-secret-key-change-this
   POSTGRES_PASSWORD=staging-db-password-2024
   REDIS_PASSWORD=staging-redis-password-2024
   ```

2. **推送代码**：
   ```bash
   git add .
   git commit -m "initial: 配置预发布环境"
   git push origin main
   ```

3. **监控部署**：
   - GitHub Actions: `https://github.com/YOUR_USERNAME/chatSphere/actions`
   - 部署日志: 实时查看部署进度

## 🖥️ 四、访问和监控

### 4.1 应用访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 主应用 | `http://49.232.202.209` | ChatSphere 应用 |
| API 文档 | `http://49.232.202.209/docs` | FastAPI 自动生成文档 |
| 健康检查 | `http://49.232.202.209/health` | 应用健康状态 |

### 4.2 监控面板

| 服务 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| Grafana | `http://49.232.202.209:3000` | admin | staging-grafana-admin-2024 |
| Portainer | `http://49.232.202.209:9000` | 首次访问设置 | - |
| Prometheus | `http://49.232.202.209:9090` | - | - |

### 4.3 服务管理命令

在服务器上可以使用以下命令管理服务：

```bash
# 启动服务
chatsphere start

# 停止服务
chatsphere stop

# 重启服务
chatsphere restart

# 查看状态
chatsphere status

# 查看日志
chatsphere logs
chatsphere logs nginx  # 查看特定服务日志
```

## 🔧 五、运维和维护

### 5.1 日志管理

```bash
# 查看应用日志
docker-compose -f docker-compose.staging.yml logs -f chatsphere

# 查看所有服务日志
docker-compose -f docker-compose.staging.yml logs -f

# 查看系统日志
journalctl -fu docker
```

### 5.2 数据备份

```bash
# 手动备份
/opt/chatsphere/backup.sh

# 查看备份文件
ls -la /opt/chatsphere/backups/

# 恢复数据库
docker-compose -f docker-compose.staging.yml exec postgres psql -U postgres -d chatsphere_staging < backup_file.sql
```

### 5.3 更新部署

```bash
# 拉取最新代码
cd /opt/chatsphere/current
git pull origin main

# 重新构建和部署
cd backend
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml up -d
```

### 5.4 故障排除

**常见问题：**

1. **服务无法启动**
   ```bash
   # 检查容器状态
   docker ps -a
   
   # 查看错误日志
   docker-compose -f docker-compose.staging.yml logs
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库服务
   docker-compose -f docker-compose.staging.yml exec postgres pg_isready
   
   # 检查网络连接
   docker network ls
   ```

3. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tulpn | grep :80
   
   # 停止冲突服务
   systemctl stop apache2  # 如果有其他web服务
   ```

## 🔐 六、安全配置

### 6.1 防火墙规则

```bash
# 查看当前规则
ufw status

# 只允许必要端口
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp
ufw allow 9000/tcp
```

### 6.2 SSL 证书（可选）

如果后续有域名，可以配置 SSL：

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d yourdomain.com

# 自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

## 📊 七、性能优化

### 7.1 Docker 优化

```bash
# 清理未使用的镜像
docker system prune -f

# 配置日志轮转
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
```

### 7.2 系统优化

```bash
# 调整内核参数
echo 'vm.max_map_count=262144' >> /etc/sysctl.conf
sysctl -p

# 增加文件描述符限制
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

## 🔄 八、CI/CD 最佳实践

### 8.1 分支策略

- **main**: 生产就绪代码，自动部署到预发布环境
- **develop**: 开发分支，功能开发完成后合并到 main
- **feature/***: 功能分支，开发完成后合并到 develop

### 8.2 版本管理

```bash
# 创建标签发布
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### 8.3 回滚策略

```bash
# 快速回滚到备份版本
cd /opt/chatsphere
rm -rf current
mv backup current
chatsphere restart
```

## 📝 九、部署检查清单

### 9.1 部署前检查

- [ ] 服务器环境已初始化
- [ ] GitHub Secrets 已配置
- [ ] 环境配置文件已修改
- [ ] 代码已推送到 GitHub

### 9.2 部署后验证

- [ ] 应用可以正常访问
- [ ] API 文档可以查看
- [ ] 健康检查通过
- [ ] 监控面板正常
- [ ] 日志输出正常

### 9.3 上线前测试

- [ ] 用户注册登录功能
- [ ] WebSocket 连接正常
- [ ] 数据库读写正常
- [ ] 缓存功能正常
- [ ] 文件上传功能

## 🆘 十、联系和支持

如果在部署过程中遇到问题：

1. 查看 GitHub Actions 构建日志
2. 检查服务器错误日志
3. 查看监控面板状态
4. 参考故障排除指南

## 🎉 恭喜！

你已经成功配置了 ChatSphere 的完整部署体系！

**访问地址：** `http://49.232.202.209`

现在你可以：
- 自动化部署新功能
- 监控应用性能
- 管理服务状态
- 备份重要数据 