# ChatSphere API 测试指南 🧪

## 🏁 快速开始

系统已启动在: `http://localhost:8000`

### 📖 API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

---

## 🔑 1. 认证系统测试

### 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "display_name": "测试用户",
    "password": "123456"
  }'
```

### 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "123456"
  }'
```

**响应示例:**
```json
{
  "user": {
    "id": "uuid-string",
    "email": "test@example.com",
    "username": "testuser",
    "display_name": "测试用户"
  },
  "access_token": "eyJ0eXAiOiJKV1Q...",
  "refresh_token": "eyJ0eXAiOiJKV1Q...",
  "token_type": "bearer"
}
```

### 获取当前用户信息
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔌 2. WebSocket 测试

WebSocket端点: `ws://localhost:8000/ws?token=YOUR_JWT_TOKEN`

### 使用浏览器测试工具

#### 方法1: 浏览器开发者工具
```javascript
// 1. 先登录获取token
// 2. 在浏览器控制台执行:

const token = "YOUR_ACCESS_TOKEN";
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = function(event) {
    console.log("✅ WebSocket连接已建立");
};

ws.onmessage = function(event) {
    console.log("📨 收到消息:", JSON.parse(event.data));
};

ws.onerror = function(error) {
    console.log("❌ WebSocket错误:", error);
};

// 发送消息
ws.send(JSON.stringify({
    type: "message",
    content: "Hello ChatSphere!",
    chat_type: "private",
    recipient_id: "other_user_id"
}));
```

#### 方法2: 使用Postman
1. 创建新的WebSocket请求
2. URL: `ws://localhost:8000/ws?token=YOUR_JWT_TOKEN`
3. 连接并发送JSON消息

#### 方法3: 使用Python客户端
```python
import asyncio
import websockets
import json

async def test_websocket():
    token = "YOUR_ACCESS_TOKEN"
    uri = f"ws://localhost:8000/ws?token={token}"

    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket连接已建立")

        # 发送消息
        message = {
            "type": "message",
            "content": "Hello from Python!",
            "chat_type": "private",
            "recipient_id": "user_id"
        }
        await websocket.send(json.dumps(message))

        # 接收消息
        response = await websocket.recv()
        print("📨 收到响应:", json.loads(response))

# 运行测试
asyncio.run(test_websocket())
```

---

## 🧪 3. 系统功能测试流程

### 完整测试流程
```bash
# 1. 检查系统健康状态
curl http://localhost:8000/health

# 2. 注册用户A
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "username": "alice",
    "display_name": "Alice",
    "password": "123456"
  }'

# 3. 注册用户B
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "username": "bob",
    "display_name": "Bob",
    "password": "123456"
  }'

# 4. 用户A登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "123456"
  }'

# 5. 用户B登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "123456"
  }'
```

### WebSocket 聊天测试
1. **两个浏览器标签页**: 分别使用Alice和Bob的token连接WebSocket
2. **发送消息**: Alice向Bob发送私聊消息
3. **验证实时性**: 确认Bob能实时收到消息

---

## 🛠️ 4. 测试工具推荐

### REST API测试
- **Postman**: 图形化接口，支持环境变量
- **Insomnia**: 轻量级替代品
- **VS Code REST Client**: 使用.http文件
- **curl**: 命令行工具

### WebSocket测试
- **Postman**: 支持WebSocket测试
- **WebSocket King**: Chrome扩展
- **wscat**: 命令行工具 `npm install -g wscat`
- **Python websockets**: 编程方式测试

### 示例：使用wscat测试
```bash
# 安装wscat
npm install -g wscat

# 连接WebSocket (需要先获取token)
wscat -c "ws://localhost:8000/ws?token=YOUR_JWT_TOKEN"

# 发送消息
{"type": "message", "content": "Hello!", "chat_type": "private", "recipient_id": "user_id"}
```

---

## 📊 5. 监控和调试

### 查看日志
```bash
# 查看应用日志
tail -f logs/chatsphere.log

# 查看Docker容器日志
docker-compose logs -f chatsphere_backend
```

### Redis 调试
```bash
# 连接Redis查看缓存
docker exec -it chatsphere_redis redis-cli

# 查看所有键
KEYS *

# 查看用户会话
GET user_session:USER_ID

# 查看速率限制
GET rate_limit:ip:127.0.0.1
```

### 数据库调试
```bash
# 连接PostgreSQL
docker exec -it chatsphere_postgres psql -U postgres -d chatsphere_dev

# 查看用户表
SELECT * FROM users;

# 查看消息表
SELECT * FROM messages;
```

---

## 🔍 6. 常见问题解决

### WebSocket连接失败
1. **检查token有效性**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/auth/validate-token" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **检查WebSocket URL格式**:
   - 正确: `ws://localhost:8000/ws?token=YOUR_TOKEN`
   - 错误: `wss://` (本地开发使用ws)

3. **查看浏览器网络选项卡**: 检查WebSocket连接状态

### API请求失败
1. **检查Content-Type**: 确保是 `application/json`
2. **检查Authorization**: Bearer token格式
3. **查看控制台错误**: 检查CORS或CSP问题

### 性能测试
```bash
# 使用ab进行压力测试
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/auth/me

# 使用wrk进行性能测试
wrk -t12 -c400 -d30s --header "Authorization: Bearer TOKEN" http://localhost:8000/api/v1/auth/me
```

---

## 🎯 7. 下一步扩展

准备好后，你可以测试：
1. **消息持久化**: 发送消息后重启服务器，检查消息是否保存
2. **离线消息**: 用户离线时发送消息，上线后检查是否收到
3. **群聊功能**: 创建群组并测试群聊
4. **文件上传**: 测试图片和文件分享
5. **OAuth2登录**: 集成Google/GitHub登录

现在你可以开始全面测试你的ChatSphere系统了！🚀
