import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';

// API基础配置
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 定义接口类型
export interface User {
  id: string;
  email: string;
  username: string;
  display_name: string;
  avatar_url?: string;
  oauth_provider: string;
  created_at: string;
  last_seen?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  display_name: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  code?: string;
}

export interface Message {
  id: string;
  from_user_id: string;
  content: string;
  message_type: string;
  created_at: string;
  is_edited: boolean;
  reply_to_id?: string;
}

export interface Room {
  id: string;
  name: string;
  description?: string;
  max_members: number;
  online_count: number;
  created_at: string;
}

export interface Conversation {
  id: string;
  name: string;
  type: 'private' | 'group' | 'room';
  last_message?: Message;
  unread_count: number;
}

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器 - 添加认证token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 处理token过期
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // token过期，清除本地存储
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // 认证相关API
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response: AxiosResponse<ApiResponse<AuthResponse>> = await this.api.post('/auth/login', data);
    return response.data.data!;
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response: AxiosResponse<ApiResponse<AuthResponse>> = await this.api.post('/auth/register', data);
    return response.data.data!;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
  }

  async getCurrentUser(): Promise<User> {
    const response: AxiosResponse<ApiResponse<User>> = await this.api.get('/me');
    return response.data.data!;
  }

  // 用户相关API
  async getOnlineUsers(): Promise<User[]> {
    const response = await this.api.get('/users/online');
    return response.data.users;
  }

  // 房间相关API
  async getRooms(): Promise<Room[]> {
    const response = await this.api.get('/rooms');
    return response.data.rooms;
  }

  // 消息相关API
  async getMessages(chatType: string, chatId: string, limit = 50, offset = 0): Promise<{messages: Message[], total: number, has_more: boolean}> {
    const response = await this.api.get(`/messages/${chatType}/${chatId}`, {
      params: { limit, offset }
    });
    return response.data;
  }

  // 对话相关API
  async getConversations(): Promise<Conversation[]> {
    const response = await this.api.get('/conversations');
    return response.data.conversations;
  }

  // 系统统计API
  async getSystemStats(): Promise<any> {
    const response = await this.api.get('/stats');
    return response.data;
  }
}

export const apiService = new ApiService(); 