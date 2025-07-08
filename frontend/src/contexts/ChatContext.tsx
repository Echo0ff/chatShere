import React, { createContext, useContext, useReducer, useEffect, useRef, useCallback } from 'react';
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
      console.log('🔄 处理ADD_MESSAGE:', action.payload);
      console.log('📋 当前消息列表长度:', state.messages.length);
      
      // 检查是否是重复消息（更严格的检测）
      const existingMessage = state.messages.find(msg => 
        String(msg.id) === String(action.payload.id) || 
        (msg.content === action.payload.content && 
         msg.from_user_id === action.payload.from_user_id &&
         Math.abs(new Date(msg.created_at).getTime() - new Date(action.payload.created_at).getTime()) < 3000)
      );
      
      if (existingMessage) {
        console.log('⚠️ 检测到重复消息，跳过添加:', action.payload.id);
        return state;
      }
      
      // 如果是服务器返回的真实消息，移除对应的临时消息
      let filteredMessages = state.messages;
      if (!String(action.payload.id).startsWith('temp_')) {
        const removedCount = filteredMessages.length;
        filteredMessages = filteredMessages.filter(msg => 
          !(String(msg.id).startsWith('temp_') && 
            msg.content === action.payload.content && 
            msg.from_user_id === action.payload.from_user_id)
        );
        const finalCount = filteredMessages.length;
        if (removedCount !== finalCount) {
          console.log('🗑️ 移除了临时消息，数量变化:', removedCount, '->', finalCount);
        }
      }
      
      const newMessages = [...filteredMessages, action.payload];
      console.log('✅ 成功添加消息，新消息列表长度:', newMessages.length);
      
      return {
        ...state,
        messages: newMessages,
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
  
  // 使用ref保存当前聊天状态，避免useEffect依赖问题
  const currentChatRef = useRef(state.currentChat);
  const authUserRef = useRef(authState.user);
  
  // 确保ref在初始化时就有正确的值
  currentChatRef.current = state.currentChat;
  authUserRef.current = authState.user;
  
  // 更新ref当状态变化时
  useEffect(() => {
    currentChatRef.current = state.currentChat;
    console.log('🔄 currentChatRef更新:', currentChatRef.current);
  }, [state.currentChat]);
  
  useEffect(() => {
    console.log('🔄 authState.user变化:', authState.user);
    console.log('🔄 authState.isAuthenticated:', authState.isAuthenticated);
    authUserRef.current = authState.user;
    console.log('🔄 authUserRef更新为:', authUserRef.current);
  }, [authState.user, authState.isAuthenticated]);

  // 消息处理函数，使用useCallback确保获取最新状态
  const handleMessage = useCallback((message: WebSocketMessage) => {
    console.log('📨 ChatContext收到消息:', message);
    
    switch (message.type) {
      case 'connection_established':
        console.log('🔗 连接建立成功:', message.data);
        break;
        
      case 'message':
        console.log('💬 收到聊天消息:', message.data);
        console.log('📍 当前聊天:', currentChatRef.current);
        
        const newMessage: Message = {
          id: String(message.data.id), // 确保ID是字符串类型
          from_user_id: message.data.from_user_id,
          content: message.data.content,
          message_type: message.data.message_type || 'text',
          created_at: message.data.created_at,
          is_edited: message.data.is_edited || false,
        };
        
        const currentChat = currentChatRef.current;
        
        // 消息过滤逻辑：只显示当前聊天的消息
        let shouldAddMessage = false;
        
        if (currentChat) {
          console.log('🔍 消息过滤检查:');
          console.log('- 当前聊天类型:', currentChat.type);
          console.log('- 当前聊天ID:', currentChat.id);
          console.log('- 消息chat_type:', message.data.chat_type);
          console.log('- 消息chat_id:', message.data.chat_id);
          console.log('- 消息room_id:', message.data.room_id);
          
          // 根据聊天类型和ID匹配消息
          if (currentChat.type === 'room' && message.data.chat_type === 'room') {
            shouldAddMessage = currentChat.id === message.data.room_id || currentChat.id === message.data.chat_id;
          } else if (currentChat.type === 'private' && message.data.chat_type === 'private') {
            // 私聊消息匹配：当前聊天ID应该等于消息的接收者ID或发送者ID
            shouldAddMessage = currentChat.id === message.data.to_user_id || 
                             currentChat.id === message.data.from_user_id ||
                             currentChat.id === message.data.chat_id;
          } else if (currentChat.type === 'group' && message.data.chat_type === 'group') {
            shouldAddMessage = currentChat.id === message.data.group_id || currentChat.id === message.data.chat_id;
          }
          
          console.log('- 消息匹配结果:', shouldAddMessage);
        } else {
          // 没有选择聊天时，不显示任何消息
          console.log('🔍 没有当前聊天，忽略消息');
        }
        
        if (shouldAddMessage) {
          console.log('✅ 添加消息到状态:', newMessage);
          dispatch({ type: 'ADD_MESSAGE', payload: newMessage });
        } else {
          console.log('❌ 消息被过滤');
        }
        break;
        
      case 'online_users':
        console.log('👥 更新在线用户:', message.data);
        dispatch({ type: 'SET_ONLINE_USERS', payload: message.data });
        break;
        
      case 'user_joined':
        console.log('👋 用户加入:', message.data);
        break;
        
      case 'user_left':
        console.log('👋 用户离开:', message.data);
        break;
        
      case 'typing':
        if (message.data.is_typing) {
          dispatch({
            type: 'ADD_TYPING_USER',
            payload: {
              userId: message.data.user_id,
              chatId: message.data.chat_id,
              chatType: message.data.chat_type || 'room',
            },
          });
        } else {
          dispatch({
            type: 'REMOVE_TYPING_USER',
            payload: {
              userId: message.data.user_id,
              chatId: message.data.chat_id,
              chatType: message.data.chat_type || 'room',
            },
          });
        }
        break;
        
      case 'error':
        console.log('❌ WebSocket错误:', message.data.message);
        dispatch({ type: 'SET_ERROR', payload: message.data.message });
        break;
        
      default:
        console.log('❓ 未知消息类型:', message.type);
    }
  }, []);

  // WebSocket连接管理
  useEffect(() => {
    if (!authState.isAuthenticated) {
      console.log('🔐 用户未登录，重置聊天状态');
      dispatch({ type: 'RESET_CHAT' });
      websocketService.disconnect();
      return;
    }

    console.log('🔗 用户已登录，连接WebSocket');
    websocketService.connect();

    const handleConnection = (connected: boolean) => {
      console.log('📡 WebSocket连接状态变化:', connected);
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: connected });
    };

    const unsubscribeMessage = websocketService.onMessage(handleMessage);
    const unsubscribeConnection = websocketService.onConnection(handleConnection);

    return () => {
      console.log('🧹 清理WebSocket监听器');
      unsubscribeMessage();
      unsubscribeConnection();
    };
  }, [authState.isAuthenticated, handleMessage]);

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
    console.log('📤 sendMessage被调用');
    console.log('📤 authState完整信息:', authState);
    console.log('📤 authState.user:', authState.user);
    console.log('📤 authState.isAuthenticated:', authState.isAuthenticated);
    
    const currentChat = currentChatRef.current;
    // 使用fallback逻辑：优先使用ref，如果为空则使用authState.user
    const authUser = authUserRef.current || authState.user;
    
    console.log('📤 currentChatRef.current:', currentChat);
    console.log('📤 authUserRef.current:', authUserRef.current);
    console.log('📤 使用的authUser (with fallback):', authUser);
    
    if (!currentChat || !authUser) {
      console.log('❌ 无法发送消息:', { 
        currentChat, 
        authUser,
        'authUserRef.current': authUserRef.current,
        'authState.user': authState.user,
        'authState.isAuthenticated': authState.isAuthenticated 
      });
      return;
    }

    const messageData = {
      chat_type: currentChat.type,
      chat_id: currentChat.id,
      content,
      message_type: messageType as any,
      reply_to_id: replyToId,
    };
    
    console.log('📤 发送消息数据:', messageData);
    console.log('📍 当前聊天状态:', currentChat);
    console.log('👤 当前用户:', authUser);
    
    // 乐观更新：立即添加消息到本地状态
    const optimisticMessage: Message = {
      id: `temp_${Date.now()}_${Math.random()}`, // 临时ID
      from_user_id: authUser.id,
      content,
      message_type: messageType as any,
      created_at: new Date().toISOString(),
      is_edited: false,
    };
    
    console.log('🚀 乐观更新：立即添加消息到UI:', optimisticMessage);
    dispatch({ type: 'ADD_MESSAGE', payload: optimisticMessage });
    
    // 发送到服务器
    console.log('🌐 发送到WebSocket服务器...');
    websocketService.sendMessage(messageData);
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