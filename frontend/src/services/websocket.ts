// import type { Message, User } from './api'; // 暂时未直接使用

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'connection_established' | 'message' | 'online_users' | 'user_joined' | 'user_left' | 'typing' | 'error' | 'pong' | 'conversation_updated';
  data: any;
  timestamp: string;
}

// 发送消息的数据结构
export interface SendMessageData {
  chat_type: 'private' | 'group' | 'room';
  chat_id: string;
  content: string;
  message_type?: 'text' | 'image' | 'file';
  reply_to_id?: string;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000; // 增加重连延迟
  private messageHandlers: Array<(message: WebSocketMessage) => void> = [];
  private connectionHandlers: Array<(connected: boolean) => void> = [];
  private isManuallyDisconnected = false;
  private heartbeatInterval: number | null = null;
  private heartbeatTimeout: number | null = null;
  private connectionTimeout: number | null = null;
  private isConnecting = false;
  // private lastPongTime = 0; // 暂时未使用

  constructor() {
    // 不在构造函数中自动连接，等待手动调用
  }

  // 连接WebSocket
  connect(): void {
    // 防止重复连接
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket正在连接中，跳过重复连接');
      return;
    }

    // 如果已经连接，不需要重新连接
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接，无需重新连接');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('No access token found, cannot connect to WebSocket');
      this.notifyConnectionHandlers(false);
      return;
    }

    this.isConnecting = true;
    this.isManuallyDisconnected = false;

    // 清除现有连接
    this.cleanupConnection();

    try {
      const wsUrl = `ws://localhost:8000/ws?token=${token}`;
      console.log('尝试连接WebSocket:', wsUrl);
      this.ws = new WebSocket(wsUrl);

      // 设置连接超时
      this.connectionTimeout = window.setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.warn('WebSocket连接超时');
          this.ws.close();
          this.handleConnectionError();
        }
      }, 10000); // 10秒超时

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.clearConnectionTimeout();
        this.startHeartbeat();
        this.notifyConnectionHandlers(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          // 处理心跳响应
          if (message.type === 'pong') {
            // this.lastPongTime = Date.now(); // 暂时未使用
            this.resetHeartbeatTimeout();
            return;
          }

          console.log('收到WebSocket消息:', message);
          this.notifyMessageHandlers(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        this.clearConnectionTimeout();
        this.notifyConnectionHandlers(false);

        // 只有在非手动断开且非正常关闭时才重连
        if (!this.isManuallyDisconnected && event.code !== 1000) {
          this.handleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        this.isConnecting = false;
        this.handleConnectionError();
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.isConnecting = false;
      this.handleConnectionError();
    }
  }

  // 清理连接
  private cleanupConnection(): void {
    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close();
    }
    this.stopHeartbeat();
    this.clearConnectionTimeout();
  }

  // 处理连接错误
  private handleConnectionError(): void {
    this.stopHeartbeat();
    this.clearConnectionTimeout();
    this.notifyConnectionHandlers(false);
    if (!this.isManuallyDisconnected) {
      this.handleReconnect();
    }
  }

  // 清除连接超时
  private clearConnectionTimeout(): void {
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout);
      this.connectionTimeout = null;
    }
  }

  // 开始心跳包
  private startHeartbeat(): void {
    this.stopHeartbeat(); // 确保之前的心跳已停止
    // this.lastPongTime = Date.now(); // 暂时未使用

    // 每30秒发送一次心跳
    this.heartbeatInterval = window.setInterval(() => {
      this.sendHeartbeat();
    }, 30000);

    // 设置心跳超时检查
    this.resetHeartbeatTimeout();
  }

  // 停止心跳包
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  // 重置心跳超时
  private resetHeartbeatTimeout(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
    }

    // 如果45秒内没有收到pong，认为连接断开
    this.heartbeatTimeout = window.setTimeout(() => {
      console.warn('心跳超时，连接可能已断开');
      if (this.ws) {
        this.ws.close();
      }
    }, 45000);
  }

  // 发送心跳包
  private sendHeartbeat(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'ping',
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  // 处理重连
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      // 使用指数退避算法，但有最大延迟限制
      const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('WebSocket重连失败，已达最大重试次数');
      this.notifyConnectionHandlers(false);
    }
  }

  // 发送消息
  sendMessage(data: SendMessageData): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'send_message',
        data,
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket未连接，无法发送消息');
    }
  }

  // 发送打字状态
  sendTyping(chatType: string, chatId: string, isTyping: boolean): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'typing',
        data: {
          chat_type: chatType,
          chat_id: chatId,
          is_typing: isTyping
        },
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  // 加入房间
  joinRoom(roomId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'join_room',
        data: { room_id: roomId },
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  // 离开房间
  leaveRoom(roomId: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'leave_room',
        data: { room_id: roomId },
        timestamp: new Date().toISOString()
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  // 添加消息处理器
  onMessage(handler: (message: WebSocketMessage) => void): () => void {
    this.messageHandlers.push(handler);
    return () => {
      const index = this.messageHandlers.indexOf(handler);
      if (index > -1) {
        this.messageHandlers.splice(index, 1);
      }
    };
  }

  // 添加连接状态处理器
  onConnection(handler: (connected: boolean) => void): () => void {
    this.connectionHandlers.push(handler);
    return () => {
      const index = this.connectionHandlers.indexOf(handler);
      if (index > -1) {
        this.connectionHandlers.splice(index, 1);
      }
    };
  }

  // 通知消息处理器
  private notifyMessageHandlers(message: WebSocketMessage): void {
    this.messageHandlers.forEach(handler => {
      try {
        handler(message);
      } catch (error) {
        console.error('消息处理器执行失败:', error);
      }
    });
  }

  // 通知连接状态处理器
  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach(handler => {
      try {
        handler(connected);
      } catch (error) {
        console.error('连接状态处理器执行失败:', error);
      }
    });
  }

  // 获取连接状态
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  // 断开连接
  disconnect(): void {
    this.isManuallyDisconnected = true;
    this.cleanupConnection();
    if (this.ws) {
      this.ws = null;
    }
    this.notifyConnectionHandlers(false);
  }

  // 强制重连
  reconnect(): void {
    console.log('强制重连WebSocket');
    this.reconnectAttempts = 0; // 重置重连次数
    this.isManuallyDisconnected = false;
    this.cleanupConnection();
    if (this.ws) {
      this.ws = null;
    }

    setTimeout(() => {
      this.connect();
    }, 1000);
  }
}

export const websocketService = new WebSocketService();
