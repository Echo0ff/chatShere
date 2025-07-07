import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { Message, Conversation, Room, User } from '../services/api';
import type { WebSocketMessage } from '../services/websocket';
import { apiService } from '../services/api';
import { websocketService } from '../services/websocket';
import { useAuth } from './AuthContext';

// 聊天状态接口
export interface ChatState {
  conversations: Conversation[];
  currentChat: {
    id: string;
    type: 'private' | 'group' | 'room';
    name: string;
  } | null;
  messages: Message[];
  rooms: Room[];
  onlineUsers: User[];
  typingUsers: Array<{ userId: string; chatId: string; chatType: string }>;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

// 聊天操作类型
export type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONVERSATIONS'; payload: Conversation[] }
  | { type: 'SET_CURRENT_CHAT'; payload: { id: string; type: 'private' | 'group' | 'room'; name: string } | null }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'UPDATE_MESSAGE'; payload: Message }
  | { type: 'SET_ROOMS'; payload: Room[] }
  | { type: 'SET_ONLINE_USERS'; payload: User[] }
  | { type: 'SET_CONNECTION_STATUS'; payload: boolean }
  | { type: 'ADD_TYPING_USER'; payload: { userId: string; chatId: string; chatType: string } }
  | { type: 'REMOVE_TYPING_USER'; payload: { userId: string; chatId: string; chatType: string } }
  | { type: 'CLEAR_TYPING_USERS' }
  | { type: 'RESET_CHAT' };

// 初始状态
const initialState: ChatState = {
  conversations: [],
  currentChat: null,
  messages: [],
  rooms: [],
  onlineUsers: [],
  typingUsers: [],
  isConnected: false,
  isLoading: false,
  error: null,
};

// Reducer函数
export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };
    case 'SET_CURRENT_CHAT':
      return { ...state, currentChat: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    case 'UPDATE_MESSAGE':
      return {
        ...state,
        messages: state.messages.map(msg =>
          msg.id === action.payload.id ? action.payload : msg
        ),
      };
    case 'SET_ROOMS':
      return { ...state, rooms: action.payload };
    case 'SET_ONLINE_USERS':
      return { ...state, onlineUsers: action.payload };
    case 'SET_CONNECTION_STATUS':
      return { ...state, isConnected: action.payload };
    case 'ADD_TYPING_USER':
      const existingTyping = state.typingUsers.find(
        user => user.userId === action.payload.userId && 
                user.chatId === action.payload.chatId
      );
      if (existingTyping) return state;
      return {
        ...state,
        typingUsers: [...state.typingUsers, action.payload],
      };
    case 'REMOVE_TYPING_USER':
      return {
        ...state,
        typingUsers: state.typingUsers.filter(
          user => !(user.userId === action.payload.userId && 
                   user.chatId === action.payload.chatId)
        ),
      };
    case 'CLEAR_TYPING_USERS':
      return { ...state, typingUsers: [] };
    case 'RESET_CHAT':
      return initialState;
    default:
      return state;
  }
}

// Context接口
interface ChatContextType {
  state: ChatState;
  loadConversations: () => Promise<void>;
  loadMessages: (chatType: string, chatId: string) => Promise<void>;
  loadRooms: () => Promise<void>;
  loadOnlineUsers: () => Promise<void>;
  sendMessage: (content: string, messageType?: string, replyToId?: string) => void;
  setCurrentChat: (chat: { id: string; type: 'private' | 'group' | 'room'; name: string } | null) => void;
  sendTyping: (isTyping: boolean) => void;
  joinRoom: (roomId: string) => void;
  leaveRoom: (roomId: string) => void;
  clearError: () => void;
}

// 创建Context
const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Context Provider组件
interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const { state: authState } = useAuth();

  // WebSocket消息处理器
  useEffect(() => {
    if (!authState.isAuthenticated) {
      dispatch({ type: 'RESET_CHAT' });
      return;
    }

    const handleMessage = (message: WebSocketMessage) => {
      switch (message.type) {
        case 'message':
          dispatch({ type: 'ADD_MESSAGE', payload: message.data });
          break;
        case 'user_join':
          // 处理用户加入
          break;
        case 'user_leave':
          // 处理用户离开
          break;
        case 'typing':
          if (message.data.is_typing) {
            dispatch({
              type: 'ADD_TYPING_USER',
              payload: {
                userId: message.data.user_id,
                chatId: message.data.chat_id,
                chatType: message.data.chat_type,
              },
            });
          } else {
            dispatch({
              type: 'REMOVE_TYPING_USER',
              payload: {
                userId: message.data.user_id,
                chatId: message.data.chat_id,
                chatType: message.data.chat_type,
              },
            });
          }
          break;
        case 'error':
          dispatch({ type: 'SET_ERROR', payload: message.data.message });
          break;
      }
    };

    const handleConnection = (connected: boolean) => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: connected });
    };

    const unsubscribeMessage = websocketService.onMessage(handleMessage);
    const unsubscribeConnection = websocketService.onConnection(handleConnection);

    return () => {
      unsubscribeMessage();
      unsubscribeConnection();
    };
  }, [authState.isAuthenticated]);

  // 加载对话列表
  const loadConversations = async (): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const conversations = await apiService.getConversations();
      dispatch({ type: 'SET_CONVERSATIONS', payload: conversations });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || '加载对话失败' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // 加载消息
  const loadMessages = async (chatType: string, chatId: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const result = await apiService.getMessages(chatType, chatId);
      dispatch({ type: 'SET_MESSAGES', payload: result.messages });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || '加载消息失败' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // 加载房间列表
  const loadRooms = async (): Promise<void> => {
    try {
      const rooms = await apiService.getRooms();
      dispatch({ type: 'SET_ROOMS', payload: rooms });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || '加载房间失败' });
    }
  };

  // 加载在线用户
  const loadOnlineUsers = async (): Promise<void> => {
    try {
      const users = await apiService.getOnlineUsers();
      dispatch({ type: 'SET_ONLINE_USERS', payload: users });
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.message || '加载在线用户失败' });
    }
  };

  // 发送消息
  const sendMessage = (content: string, messageType = 'text', replyToId?: string): void => {
    if (!state.currentChat) return;

    websocketService.sendMessage({
      chat_type: state.currentChat.type,
      chat_id: state.currentChat.id,
      content,
      message_type: messageType as any,
      reply_to_id: replyToId,
    });
  };

  // 设置当前聊天
  const setCurrentChat = (chat: { id: string; type: 'private' | 'group' | 'room'; name: string } | null): void => {
    dispatch({ type: 'SET_CURRENT_CHAT', payload: chat });
    if (chat) {
      loadMessages(chat.type, chat.id);
    }
  };

  // 发送打字状态
  const sendTyping = (isTyping: boolean): void => {
    if (!state.currentChat) return;
    websocketService.sendTyping(state.currentChat.type, state.currentChat.id, isTyping);
  };

  // 加入房间
  const joinRoom = (roomId: string): void => {
    websocketService.joinRoom(roomId);
  };

  // 离开房间
  const leaveRoom = (roomId: string): void => {
    websocketService.leaveRoom(roomId);
  };

  // 清除错误
  const clearError = (): void => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  const value: ChatContextType = {
    state,
    loadConversations,
    loadMessages,
    loadRooms,
    loadOnlineUsers,
    sendMessage,
    setCurrentChat,
    sendTyping,
    joinRoom,
    leaveRoom,
    clearError,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

// 自定义Hook
export function useChat(): ChatContextType {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat必须在ChatProvider内部使用');
  }
  return context;
} 