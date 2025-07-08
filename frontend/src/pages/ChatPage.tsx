import React, { useState, useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Box,
  Grid,
  GridItem,
  Flex,
  Heading,
  Text,
  Input,
  Button,
  VStack,
  HStack,
  useBreakpointValue,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { websocketService } from '../services/websocket';
import { ColorModeButton } from '../components/ui/color-mode';

// 对话侧边栏组件
const ConversationSidebar = ({ onChatSelect, selectedChatId, selectedChatType }: any) => {
  const { state, loadConversations, loadRooms, loadOnlineUsers } = useChat();
  const { state: authState } = useAuth();

  useEffect(() => {
    // 加载聊天数据
    loadConversations();
    loadRooms();
    loadOnlineUsers();
  }, []);

  // 过滤掉当前用户自己
  const otherOnlineUsers = state.onlineUsers.filter(user => user.id !== authState.user?.id);

  return (
    <Box p={4} h="100%" bg="bg.subtle" borderRight="1px" borderColor="border" overflow="auto">
      <VStack gap={4} align="stretch">
        {/* 连接状态 */}
        <HStack justify="space-between">
          <Heading size="md" color="fg">聊天</Heading>
          <VStack gap={1} align="end">
            <Text fontSize="xs" color={state.isConnected ? 'green.500' : 'red.500'}>
              {state.isConnected ? '已连接' : '未连接'}
            </Text>
            {!state.isConnected && (
              <Button
                size="xs"
                variant="outline"
                colorScheme="blue"
                onClick={() => {
                  console.log('手动重连WebSocket');
                  websocketService.reconnect();
                }}
              >
                重连
              </Button>
            )}
          </VStack>
        </HStack>

        <Box h="1px" bg="border" />

        {/* 在线用户 */}
        <Box>
          <Text fontSize="sm" fontWeight="semibold" color="fg.muted" mb={2}>
            在线用户 ({otherOnlineUsers.length})
          </Text>
          {otherOnlineUsers.length > 0 ? (
            <VStack gap={2} align="stretch">
              {otherOnlineUsers.slice(0, 5).map((user) => (
                <HStack
                  key={user.id}
                  p={2}
                  borderRadius="md"
                  cursor="pointer"
                  _hover={{ bg: 'bg.muted' }}
                  onClick={() => onChatSelect(user.id, 'private', user.display_name || user.username)}
                  bg={selectedChatId === user.id && selectedChatType === 'private' ? 'blue.100' : 'transparent'}
                >
                  <Box
                    w={6}
                    h={6}
                    bg="blue.500"
                    borderRadius="full"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                    position="relative"
                  >
                    {(user.display_name || user.username).charAt(0).toUpperCase()}
                    <Box
                      position="absolute"
                      bottom={-1}
                      right={-1}
                      w={2}
                      h={2}
                      bg="green.500"
                      borderRadius="full"
                      border="1px solid"
                      borderColor="bg.subtle"
                    />
                  </Box>
                  <VStack align="start" gap={0} flex="1">
                    <Text fontSize="sm" fontWeight="medium" color="fg">{user.display_name || user.username}</Text>
                    <Text fontSize="xs" color="green.500">在线</Text>
                  </VStack>
                </HStack>
              ))}
            </VStack>
          ) : (
            <Text fontSize="sm" color="fg.subtle">暂无其他在线用户</Text>
          )}
        </Box>

        <Box h="1px" bg="border" />

        {/* 聊天房间 */}
        <Box>
          <Text fontSize="sm" fontWeight="semibold" color="fg.muted" mb={2}>
            聊天房间 ({state.rooms.length})
          </Text>
          {state.rooms.length > 0 ? (
            <VStack gap={2} align="stretch">
              {state.rooms.slice(0, 5).map((room) => (
                <HStack
                  key={room.id}
                  p={2}
                  borderRadius="md"
                  cursor="pointer"
                  _hover={{ bg: 'bg.muted' }}
                  onClick={() => onChatSelect(room.id, 'room', room.name)}
                  bg={selectedChatId === room.id && selectedChatType === 'room' ? 'blue.100' : 'transparent'}
                >
                  <Box
                    w={6}
                    h={6}
                    bg="green.500"
                    borderRadius="md"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    color="white"
                    fontSize="xs"
                    fontWeight="bold"
                  >
                    #
                  </Box>
                  <VStack align="start" gap={0} flex="1">
                    <Text fontSize="sm" fontWeight="medium" color="fg">{room.name}</Text>
                    <Text fontSize="xs" color="blue.500">{room.online_count} 人在线</Text>
                  </VStack>
                </HStack>
              ))}
            </VStack>
          ) : (
            <Text fontSize="sm" color="fg.subtle">暂无房间</Text>
          )}
        </Box>

        {/* 对话列表 */}
        <Box>
          <Text fontSize="sm" fontWeight="semibold" color="fg.muted" mb={2}>
            最近对话 ({state.conversations.length})
          </Text>
          {state.conversations.length > 0 ? (
            <VStack gap={2} align="stretch">
              {state.conversations.slice(0, 5).map((conversation) => (
                <Box
                  key={conversation.id}
                  p={2}
                  borderRadius="md"
                  cursor="pointer"
                  _hover={{ bg: 'bg.muted' }}
                  onClick={() => onChatSelect(conversation.id, conversation.type)}
                >
                  <Text fontSize="sm" fontWeight="medium" color="fg">{conversation.name}</Text>
                  {conversation.last_message && (
                    <Text fontSize="xs" color="fg.subtle" overflow="hidden" textOverflow="ellipsis" whiteSpace="nowrap">
                      {conversation.last_message.content}
                    </Text>
                  )}
                </Box>
              ))}
            </VStack>
          ) : (
            <Text fontSize="sm" color="fg.subtle">暂无对话</Text>
          )}
        </Box>
      </VStack>
    </Box>
  );
};

const MessageBubble = ({ message, isOwn }: { message: any; isOwn: boolean }) => {
  const { state } = useChat();
  
  // 从在线用户列表中获取用户信息
  const sender = state.onlineUsers.find(user => user.id === message.from_user_id);
  const senderName = sender?.display_name || sender?.username || '未知用户';

  // 格式化时间
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else {
      return date.toLocaleDateString('zh-CN', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  return (
    <Flex
      justify={isOwn ? 'flex-end' : 'flex-start'}
      align="flex-start"
      gap={2}
      mb={3}
    >
      {!isOwn && (
        <Box
          w={8}
          h={8}
          bg="blue.500"
          borderRadius="full"
          display="flex"
          alignItems="center"
          justifyContent="center"
          color="white"
          fontSize="sm"
          fontWeight="bold"
          flexShrink={0}
        >
          {senderName.charAt(0).toUpperCase()}
        </Box>
      )}
      
      <Box maxW="70%" minW="120px">
        {!isOwn && (
          <Text fontSize="xs" color="fg.muted" mb={1}>
            {senderName}
          </Text>
        )}
        
        <Box
          bg={isOwn ? 'blue.500' : 'bg.muted'}
          color={isOwn ? 'white' : 'fg'}
          p={3}
          borderRadius="lg"
          borderTopLeftRadius={isOwn ? 'lg' : 'sm'}
          borderTopRightRadius={isOwn ? 'sm' : 'lg'}
          position="relative"
          border="1px solid"
          borderColor={isOwn ? 'blue.500' : 'border'}
          shadow="sm"
        >
          <Text>{message.content}</Text>
          
          <HStack justify="space-between" align="center" mt={2} gap={2}>
            <Text 
              fontSize="xs" 
              color={isOwn ? 'blue.100' : 'fg.subtle'}
              opacity={0.8}
            >
              {formatTime(message.created_at)}
            </Text>
            
            {isOwn && (
              <HStack gap={1}>
                {message.is_edited && (
                  <Text fontSize="xs" color="blue.100" opacity={0.7}>
                    已编辑
                  </Text>
                )}
                <Box
                  w={2}
                  h={2}
                  borderRadius="full"
                  bg="green.400"
                  title="已发送"
                />
              </HStack>
            )}
          </HStack>
        </Box>
      </Box>
      
      {isOwn && (
        <Box
          w={8}
          h={8}
          bg="blue.500"
          borderRadius="full"
          display="flex"
          alignItems="center"
          justifyContent="center"
          color="white"
          fontSize="sm"
          fontWeight="bold"
          flexShrink={0}
        >
          你
        </Box>
      )}
    </Flex>
  );
};

const ChatArea = ({ chatId, chatType }: any) => {
  const { state, setCurrentChat, loadMessages, sendMessage, sendTyping } = useChat();
  const { state: authState } = useAuth();
  const [messageInput, setMessageInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const typingTimeoutRef = useRef<number | null>(null);
  
  // 添加消息容器引用
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部的函数
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  };

  // 当消息列表变化时自动滚动到底部
  useEffect(() => {
    if (state.messages.length > 0) {
      // 使用setTimeout确保DOM已更新
      setTimeout(scrollToBottom, 100);
    }
  }, [state.messages.length]);

  // 当选择新聊天时也滚动到底部
  useEffect(() => {
    if (chatId && state.messages.length > 0) {
      setTimeout(scrollToBottom, 200);
    }
  }, [chatId]);

  const handleStartChat = () => {
    console.log('开始聊天按钮被点击');
    
    // 检查是否有可用的房间
    if (state.rooms.length > 0) {
      // 选择第一个房间作为默认房间
      const defaultRoom = state.rooms[0];
      setCurrentChat({
        id: defaultRoom.id,
        type: 'room',
        name: defaultRoom.name
      });
      loadMessages('room', defaultRoom.id);
      console.log('已进入房间:', defaultRoom.name);
          } else {
        // 如果没有房间，创建默认大厅
        const defaultRoomId = 'general';
        setCurrentChat({
          id: defaultRoomId,
          type: 'room',
          name: '公共大厅'
        });
        // 尝试加载消息（可能为空）
        loadMessages('room', defaultRoomId);
        console.log('已创建并进入默认房间: 公共大厅');
      }
  };

  const handleSendMessage = () => {
    if (!messageInput.trim()) return;
    
    console.log('发送消息:', messageInput);
    sendMessage(messageInput.trim());
    setMessageInput('');
    
    // 发送消息后停止打字状态
    handleStopTyping();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setMessageInput(value);
    
    // 如果有内容且WebSocket连接正常，开始打字
    if (value.trim() && state.isConnected && state.currentChat) {
      handleStartTyping();
    } else {
      handleStopTyping();
    }
  };

  // 开始打字
  const handleStartTyping = () => {
    if (!isTyping && state.currentChat) {
      setIsTyping(true);
      sendTyping(true);
    }
    
    // 清除之前的定时器
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    // 设置新的定时器，2秒后停止打字状态
    typingTimeoutRef.current = window.setTimeout(() => {
      handleStopTyping();
    }, 2000);
  };

  // 停止打字
  const handleStopTyping = () => {
    if (isTyping) {
      setIsTyping(false);
      sendTyping(false);
    }
    
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  };

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  if (!chatId) {
    return (
      <Flex
        h="100%"
        direction="column"
        align="center"
        justify="center"
        bg="bg"
        p={8}
      >
        <VStack gap={4} textAlign="center">
          <Heading size="lg" color="fg.muted">欢迎使用 ChatSphere</Heading>
          <Text color="fg.subtle" maxW="md">
            选择一个聊天开始对话，或者点击下方按钮加入公共聊天室。
          </Text>
          <VStack gap={2}>
            <Button 
              colorScheme="blue" 
              size="lg"
              onClick={handleStartChat}
              loading={state.isLoading}
            >
              开始聊天
            </Button>
            <Text fontSize="sm" color={state.isConnected ? 'green.500' : 'red.500'}>
              {state.isConnected ? 'WebSocket已连接' : 'WebSocket未连接'}
            </Text>
          </VStack>
        </VStack>
      </Flex>
    );
  }

  return (
    <Flex direction="column" h="100%" bg="bg">
      {/* 聊天头部 */}
      <Box
        p={4}
        borderBottom="1px"
        borderColor="border"
        bg="bg.subtle"
      >
        <Heading size="md" color="fg">
          {state.currentChat?.name || '聊天'}
        </Heading>
      </Box>

      {/* 消息区域 */}
      <Box flex="1" p={4} overflow="auto" bg="bg" ref={messagesContainerRef}>
        {state.messages.length > 0 ? (
          <VStack gap={4} align="stretch">
            {state.messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.from_user_id === authState.user?.id}
              />
            ))}
            <div ref={messagesEndRef} />
          </VStack>
        ) : (
          <Flex align="center" justify="center" h="100%">
            <VStack gap={2}>
              <Text color="fg.muted" fontSize="lg">💬</Text>
              <Text color="fg.muted">开始对话吧！</Text>
            </VStack>
          </Flex>
        )}
      </Box>

      {/* 输入区域 */}
      <Box
        p={4}
        borderTop="1px"
        borderColor="border"
        bg="bg.subtle"
      >
        <VStack gap={2}>
          {/* 连接状态指示器 */}
          {!state.isConnected && (
            <HStack justify="center" gap={2}>
              <Box w={2} h={2} bg="red.500" borderRadius="full" />
              <Text fontSize="sm" color="red.500">
                连接已断开，无法发送消息
              </Text>
            </HStack>
          )}
          
          {/* 打字状态指示器 */}
          {state.typingUsers.length > 0 && (
            <HStack gap={2} align="center">
              <Box
                w={3}
                h={3}
                bg="blue.500"
                borderRadius="full"
                animation="pulse 1.5s infinite"
              />
              <Text fontSize="sm" color="fg.muted">
                {state.typingUsers.map(user => 
                  state.onlineUsers.find(u => u.id === user.userId)?.display_name || '用户'
                ).join(', ')} 正在输入...
              </Text>
            </HStack>
          )}
          
          {/* 输入框和发送按钮 */}
          <HStack gap={2} w="100%">
            <Input
              placeholder={state.isConnected ? "输入消息..." : "连接断开，无法输入"}
              value={messageInput}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              disabled={!state.isConnected}
              flex="1"
              bg="bg"
              borderColor="border"
              color="fg"
              _placeholder={{ color: "fg.subtle" }}
            />
            <Button
              colorScheme="blue"
              onClick={handleSendMessage}
              disabled={!state.isConnected || !messageInput.trim()}
              size="md"
              px={6}
            >
              发送
            </Button>
          </HStack>
          
          {/* 状态信息 */}
          <HStack justify="space-between" w="100%" fontSize="xs" color="fg.subtle">
            <Text>
              在线用户: {state.onlineUsers.length}
            </Text>
            <Text>
              {state.isConnected ? '✓ 已连接' : '✗ 未连接'}
            </Text>
          </HStack>
        </VStack>
      </Box>
    </Flex>
  );
};

export default function ChatPage() {
  const { state: authState } = useAuth();
  const { state: chatState, setCurrentChat, loadMessages } = useChat();
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedChatType, setSelectedChatType] = useState<'private' | 'group' | 'room'>('private');
  const [showSidebar, setShowSidebar] = useState(false);
  
  // 响应式断点
  const isMobile = useBreakpointValue({ base: true, lg: false });

  // 如果未登录，重定向到登录页
  if (!authState.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // 处理聊天选择
  const handleChatSelect = (chatId: string, chatType: 'private' | 'group' | 'room', chatName?: string) => {
    setSelectedChatId(chatId);
    setSelectedChatType(chatType);
    
    // 设置当前聊天并加载消息
    let displayName = chatName;
    
    if (chatType === 'private') {
      displayName = chatName ? `与 ${chatName} 的私聊` : '私聊';
    } else if (chatType === 'room') {
      // 从房间列表中查找房间名
      const room = chatState.rooms.find((r: any) => r.id === chatId);
      displayName = room?.name || chatId;
    }
    
    setCurrentChat({
      id: chatId,
      type: chatType,
      name: displayName || chatId
    });
    
    loadMessages(chatType, chatId);
    
    // 在移动端选择聊天后关闭侧边栏
    if (isMobile) {
      setShowSidebar(false);
    }
  };

  // 桌面端布局
  if (!isMobile) {
    return (
      <Box h="100vh" bg="bg">
        {/* 顶部导航栏 */}
        <Flex
          as="header"
          align="center"
          justify="space-between"
          px={4}
          py={3}
          bg="bg.subtle"
          borderBottom="1px"
          borderColor="border"
          boxShadow="sm"
        >
          <Heading size="md" color="fg">
            ChatSphere
          </Heading>
          
          {/* 右侧用户信息和设置 */}
          <HStack gap={4}>
            {/* 当前用户信息 */}
            <VStack align="end" gap={0} display={{ base: 'none', md: 'flex' }}>
              <Text fontSize="sm" fontWeight="medium" color="fg">
                {authState.user?.display_name || authState.user?.username || '用户'}
              </Text>
              <Text fontSize="xs" color="fg.muted">
                @{authState.user?.username}
              </Text>
            </VStack>
            
            {/* 用户头像 */}
            <Box
              w={8}
              h={8}
              bg="blue.500"
              borderRadius="full"
              display="flex"
              alignItems="center"
              justifyContent="center"
              color="white"
              fontSize="sm"
              fontWeight="bold"
            >
              {(authState.user?.display_name || authState.user?.username || 'U').charAt(0).toUpperCase()}
            </Box>
            
            <ColorModeButton />
          </HStack>
        </Flex>
        
        <Grid
          templateColumns="350px 1fr"
          h="calc(100vh - 60px)"
        >
          {/* 侧边栏 */}
          <GridItem bg="bg.subtle" borderRight="1px" borderColor="border">
            <ConversationSidebar
              onChatSelect={handleChatSelect}
              selectedChatId={selectedChatId}
              selectedChatType={selectedChatType}
            />
          </GridItem>

          {/* 聊天区域 */}
          <GridItem bg="bg">
            <ChatArea
              chatId={selectedChatId}
              chatType={selectedChatType}
            />
          </GridItem>
        </Grid>
      </Box>
    );
  }

  // 移动端布局
  return (
    <Flex direction="column" h="100vh" bg="bg">
      {/* 顶部导航栏 */}
      <Flex
        as="header"
        align="center"
        justify="space-between"
        px={4}
        py={3}
        bg="bg.subtle"
        borderBottom="1px"
        borderColor="border"
        boxShadow="sm"
      >
        <Button
          variant="ghost"
          onClick={() => setShowSidebar(!showSidebar)}
          size="sm"
          color="fg"
        >
          ☰
        </Button>
        <Heading size="md" color="fg">
          ChatSphere
        </Heading>
        
        {/* 移动端右侧：只显示用户头像和色彩模式按钮 */}
        <HStack gap={2}>
          {/* 用户头像 */}
          <Box
            w={8}
            h={8}
            bg="blue.500"
            borderRadius="full"
            display="flex"
            alignItems="center"
            justifyContent="center"
            color="white"
            fontSize="sm"
            fontWeight="bold"
          >
            {(authState.user?.display_name || authState.user?.username || 'U').charAt(0).toUpperCase()}
          </Box>
          
          <ColorModeButton />
        </HStack>
      </Flex>

      {/* 内容区域 */}
      <Flex flex="1" overflow="hidden">
        {/* 侧边栏 (移动端可隐藏) */}
        {showSidebar && (
          <Box
            w="280px"
            bg="bg.subtle"
            borderRight="1px"
            borderColor="border"
            overflow="auto"
          >
            <ConversationSidebar
              onChatSelect={handleChatSelect}
              selectedChatId={selectedChatId}
              selectedChatType={selectedChatType}
            />
          </Box>
        )}

        {/* 聊天区域 */}
        <Box flex="1" bg="bg">
          <ChatArea
            chatId={selectedChatId}
            chatType={selectedChatType}
          />
        </Box>
      </Flex>
    </Flex>
  );
} 