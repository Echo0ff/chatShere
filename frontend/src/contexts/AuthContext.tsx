import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, AuthResponse } from '../services/api';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';

// 认证状态接口
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// 认证操作类型
export type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: User }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_LOADING'; payload: boolean };

// 初始状态
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Reducer函数
export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
}

// Context接口
interface AuthContextType {
  state: AuthState;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, displayName: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

// 创建Context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Context Provider组件
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 检查用户是否已登录
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      console.log('🔐 检查认证状态...');
      console.log('🔐 本地存储token:', token ? '存在' : '不存在');
      
      if (token) {
        try {
          console.log('🔐 开始验证用户...');
          dispatch({ type: 'AUTH_START' });
          
          const user = await apiService.getCurrentUser();
          console.log('🔐 获取到用户信息:', user);
          
          if (user && user.id) {
            dispatch({ type: 'AUTH_SUCCESS', payload: user });
            console.log('✅ 用户认证成功');
          } else {
            console.log('❌ 用户信息无效:', user);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            dispatch({ type: 'AUTH_FAILURE', payload: '用户信息无效' });
          }
        } catch (error) {
          console.error('❌ 验证用户失败:', error);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          dispatch({ type: 'AUTH_FAILURE', payload: '认证已过期，请重新登录' });
        }
      } else {
        console.log('🔐 无token，设置为未认证状态');
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkAuth();
  }, []);

  // 登录函数
  const login = async (email: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      const authResponse: AuthResponse = await apiService.login({ email, password });
      
      // 保存token到localStorage
      localStorage.setItem('access_token', authResponse.access_token);
      localStorage.setItem('refresh_token', authResponse.refresh_token);
      
      dispatch({ type: 'AUTH_SUCCESS', payload: authResponse.user });
      
      // 重新连接WebSocket
      websocketService.connect();
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '登录失败，请检查用户名和密码';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // 注册函数
  const register = async (email: string, username: string, displayName: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'AUTH_START' });
      const authResponse: AuthResponse = await apiService.register({
        email,
        username,
        display_name: displayName,
        password,
      });
      
      // 保存token到localStorage
      localStorage.setItem('access_token', authResponse.access_token);
      localStorage.setItem('refresh_token', authResponse.refresh_token);
      
      dispatch({ type: 'AUTH_SUCCESS', payload: authResponse.user });
      
      // 连接WebSocket
      websocketService.connect();
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || '注册失败，请重试';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // 登出函数
  const logout = async (): Promise<void> => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('登出失败:', error);
    } finally {
      // 清除本地存储
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // 断开WebSocket连接
      websocketService.disconnect();
      
      dispatch({ type: 'LOGOUT' });
    }
  };

  // 清除错误
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    state,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 自定义Hook
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth必须在AuthProvider内部使用');
  }
  return context;
} 