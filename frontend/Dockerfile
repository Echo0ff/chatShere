# ChatSphere 前端 Dockerfile
# 支持多阶段构建和多环境部署

# 基础镜像
FROM node:18-alpine AS base

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 开发环境阶段
FROM base AS development

# 安装所有依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 5173

# 开发环境启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 构建阶段
FROM base AS builder

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 测试环境阶段 - 使用 Nginx 服务静态文件
FROM nginx:alpine AS testing

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx/testing.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]

# 生产环境阶段 - 使用 Nginx 服务静态文件
FROM nginx:alpine AS production

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx/production.conf /etc/nginx/conf.d/default.conf

# 创建非root用户
RUN addgroup -g 1001 -S appuser && \
    adduser -S appuser -u 1001

# 设置权限
RUN chown -R appuser:appuser /usr/share/nginx/html && \
    chown -R appuser:appuser /var/cache/nginx && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /etc/nginx/conf.d

# 创建 nginx.pid 文件目录并设置权限
RUN touch /var/run/nginx.pid && \
    chown -R appuser:appuser /var/run/nginx.pid

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/ || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
