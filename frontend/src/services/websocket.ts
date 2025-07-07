import type { Message, User } from './api';

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'message' | 'user_join' | 'user_leave' | 'typing' | 'error';
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
  private reconnectDelay = 1000;
  private messageHandlers: Array<(message: WebSocketMessage) => void> = [];
  private connectionHandlers: Array<(connected: boolean) => void> = [];

  constructor() {
    this.connect();
  }

  // 连接WebSocket
  connect(): void {
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('No access token found, cannot connect to WebSocket');
      return;
    }

    try {
      const wsUrl = `ws://localhost:8000/ws?token=${token}`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立');
        this.reconnectAttempts = 0;
        this.notifyConnectionHandlers(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyMessageHandlers(message);
        } catch (error) {
          console.error('解析WebSocket消息失败:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason);
        this.notifyConnectionHandlers(false);
        this.handleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        this.notifyConnectionHandlers(false);
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      this.handleReconnect();
    }
  }

  // 处理重连
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('WebSocket重连失败，已达最大重试次数');
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
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const websocketService = new WebSocketService(); 