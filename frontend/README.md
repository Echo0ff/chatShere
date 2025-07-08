# ChatSphere 前端

> 现代化React实时聊天应用前端

## 🚀 项目概述

ChatSphere 前端是一个基于 React + TypeScript 的现代化实时聊天应用，提供直观的用户界面和流畅的聊天体验。

### 主要特性

- ⚡ **React 19** - 最新的React框架和特性
- 🎨 **Chakra UI** - 现代化的组件库和设计系统
- 🌓 **主题切换** - 支持亮色/暗色主题自由切换
- 💬 **实时通信** - WebSocket实时消息传输
- 🏠 **多房间聊天** - 支持大厅、技术讨论等多个房间
- 👥 **私聊功能** - 一对一私人聊天
- 📱 **响应式设计** - 完美适配桌面和移动设备
- 🔐 **用户认证** - 完整的登录注册流程
- ⚡ **自动滚动** - 新消息自动滚动到底部
- 🔔 **实时状态** - 在线用户、打字状态等实时更新
- 📬 **未读消息数** - 红色徽章显示每个聊天的未读数量
- 🕒 **最近聊天** - 按最后消息时间智能排序会话列表
- ✅ **一键已读** - 点击聊天自动标记为已读状态

## 🛠️ 技术栈

- **框架**: React 19.1.0
- **语言**: TypeScript 5.8+
- **构建工具**: Vite 7.0+
- **UI库**: Chakra UI 3.21+
- **路由**: React Router 7.6+
- **HTTP客户端**: Axios 1.10+
- **WebSocket**: 原生WebSocket API
- **主题**: next-themes 0.4+
- **代码检查**: ESLint 9.29+

## 📋 系统要求

- Node.js 18+
- npm 9+ 或 yarn 1.22+
- 现代浏览器 (Chrome 90+, Firefox 88+, Safari 14+)
- 2GB+ RAM
- 支持WebSocket的网络环境

## ⚡ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd chatSphere/frontend

# 安装依赖
npm install

# 或使用yarn
yarn install
```

### 2. 环境配置

创建 `.env.local` 文件：

```env
# API服务器地址
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# 应用配置
VITE_APP_NAME=ChatSphere
VITE_APP_VERSION=2.0.0

# 调试配置
VITE_DEBUG=true
```

### 3. 启动开发服务器

```bash
# 开发模式
npm run dev

# 或使用yarn
yarn dev
```

访问 http://localhost:5173 查看应用

### 4. 构建生产版本

```bash
# 构建
npm run build

# 预览构建结果
npm run preview
```

## 📁 项目结构

```
frontend/
├── public/                  # 静态资源
│   ├── vite.svg            # 图标文件
│   └── ...                 
├── src/                     # 源代码
│   ├── components/          # React组件
│   │   ├── ui/             # 基础UI组件
│   │   ├── ChatArea.tsx    # 聊天区域组件
│   │   └── ConversationSidebar.tsx  # 对话侧边栏
│   ├── contexts/            # React Context
│   │   ├── AuthContext.tsx # 认证状态管理
│   │   └── ChatContext.tsx # 聊天状态管理
│   ├── pages/               # 页面组件
│   │   ├── LoginPage.tsx   # 登录页面
│   │   ├── RegisterPage.tsx # 注册页面
│   │   └── ChatPage.tsx    # 聊天主页面
│   ├── services/            # API服务
│   │   ├── api.ts          # HTTP API客户端
│   │   └── websocket.ts    # WebSocket客户端
│   ├── App.tsx              # 根组件
│   ├── main.tsx             # 应用入口
│   ├── theme.ts             # Chakra UI主题配置
│   └── index.css            # 全局样式
├── package.json             # 项目配置
├── tsconfig.json            # TypeScript配置
├── vite.config.ts           # Vite配置
└── README.md                # 项目文档
```

## 🎨 设计系统

### 主题配置

应用支持亮色和暗色两种主题：

```typescript
// 主题配置 (theme.ts)
export const theme = extendTheme({
  colors: {
    brand: {
      50: '#e3f2fd',
      500: '#2196f3',
      900: '#0d47a1',
    }
  },
  components: {
    Button: { /* 按钮样式 */ },
    Input: { /* 输入框样式 */ },
  }
});
```

### 响应式断点

```typescript
// Chakra UI断点
const breakpoints = {
  base: '0px',    // 手机
  sm: '30em',     // 480px
  md: '48em',     # 768px
  lg: '62em',     # 992px
  xl: '80em',     # 1280px
}
```

## 🔌 API 集成

### HTTP API客户端

```typescript
// services/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
});

// 自动添加认证头
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### WebSocket客户端

```typescript
// services/websocket.ts
class WebSocketService {
  connect() {
    this.ws = new WebSocket(`${VITE_WS_URL}/ws`);
    this.ws.onmessage = this.handleMessage;
  }
  
  sendMessage(data: any) {
    this.ws?.send(JSON.stringify(data));
  }
}
```

### 主要API接口

- `POST /auth/login` - 用户登录
- `POST /auth/register` - 用户注册
- `GET /auth/me` - 获取当前用户
- `GET /chat/rooms` - 获取房间列表
- `GET /chat/messages/{type}/{id}` - 获取聊天消息
- `GET /chat/online-users` - 获取在线用户

## 📱 功能模块

### 1. 用户认证
- **登录**: 邮箱/用户名 + 密码
- **注册**: 用户名、邮箱、密码、确认密码
- **自动登录**: Token持久化存储
- **登出**: 清理本地状态

### 2. 聊天功能
- **房间聊天**: 大厅、技术讨论等公共房间
- **私聊**: 一对一私人聊天
- **实时消息**: WebSocket实时传输
- **消息历史**: 加载历史聊天记录
- **自动滚动**: 新消息自动滚动到底部

### 3. 用户状态
- **在线状态**: 实时显示在线用户列表
- **打字状态**: 显示正在输入的用户
- **用户信息**: 头像、昵称、用户名

### 4. 界面交互
- **响应式布局**: 适配不同屏幕尺寸
- **主题切换**: 亮色/暗色主题
- **消息气泡**: 区分自己和他人消息
- **时间显示**: 友好的时间格式

## 🧪 开发调试

### 开发工具

```bash
# 代码检查
npm run lint

# 类型检查
tsc --noEmit

# 格式化代码
npx prettier --write src/
```

### 调试技巧

1. **Browser DevTools**
   - Network面板监控API请求
   - WebSocket面板查看实时通信
   - Console查看调试日志

2. **React Developer Tools**
   - 组件树查看
   - Props和State检查
   - 性能分析

3. **Vite开发服务器**
   - 热模块替换(HMR)
   - 快速错误反馈
   - Source Map支持

## 🚀 部署指南

### 静态部署

```bash
# 构建生产版本
npm run build

# 构建文件位于 dist/ 目录
# 可以部署到任何静态文件服务器
```

### Nginx部署

```nginx
server {
    listen 80;
    server_name chatsphere.com;
    root /var/www/chatsphere/dist;
    index index.html;
    
    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 静态资源缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Docker部署

```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Vercel部署

```bash
# 安装Vercel CLI
npm i -g vercel

# 部署
vercel --prod
```

## 🔧 故障排除

### 常见问题

1. **WebSocket连接失败**
```javascript
// 检查WebSocket连接状态
if (ws.readyState === WebSocket.CLOSED) {
  console.log('WebSocket连接已关闭');
  // 重新连接逻辑
}
```

2. **API请求失败**
```javascript
// 检查网络连接
if (!navigator.onLine) {
  console.log('网络连接中断');
  // 显示离线提示
}
```

3. **认证Token过期**
```javascript
// 自动刷新Token
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // 重新登录
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 性能优化

1. **代码分割**
```typescript
// 懒加载页面组件
const ChatPage = lazy(() => import('./pages/ChatPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
```

2. **图片优化**
```typescript
// 使用WebP格式
<img 
  src="avatar.webp" 
  alt="用户头像"
  loading="lazy" 
/>
```

3. **缓存策略**
```typescript
// 缓存用户信息
const cachedUser = useMemo(() => user, [user.id]);
```

## 📊 监控和分析

### 性能监控

```typescript
// 性能指标收集
const observer = new PerformanceObserver((list) => {
  list.getEntries().forEach((entry) => {
    console.log('性能指标:', entry);
  });
});
observer.observe({entryTypes: ['measure', 'navigation']});
```

### 错误监控

```typescript
// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('JavaScript错误:', event.error);
  // 发送错误报告
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的Promise错误:', event.reason);
});
```

## 🔄 更新日志

### v2.0.0 (当前版本)
- ✨ 新增房间消息过滤功能
- ✨ 新增自动滚动到最新消息
- 🐛 修复WebSocket连接重连问题
- 🎨 优化用户界面和体验
- 📱 完善响应式设计

### v1.0.0
- 🎉 初始版本发布
- 💬 基础聊天功能
- 🔐 用户认证系统
- 🎨 Chakra UI设计系统

## 📞 技术支持

- **问题报告**: [GitHub Issues](https://github.com/your-org/chatsphere/issues)
- **功能请求**: [GitHub Discussions](https://github.com/your-org/chatsphere/discussions)
- **文档**: [项目文档](https://docs.chatsphere.com)
- **邮箱**: frontend@chatsphere.com

## 📄 许可证

MIT License - 详见 [LICENSE](../LICENSE) 文件

---

**ChatSphere Frontend v2.0.0** - 打造极致聊天体验 🚀
