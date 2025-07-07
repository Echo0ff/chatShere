import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Input,
  Button,
  Flex,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';

interface MessageItemProps {
  message: any;
  isOwn: boolean;
  currentUser: any;
}

function MessageItem({ message, isOwn, currentUser }: MessageItemProps) {
  const formattedTime = new Date(message.created_at).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <Flex justify={isOwn ? 'flex-end' : 'flex-start'} mb={4}>
      <Box maxW="70%">
        {!isOwn && (
          <Text fontSize="xs" color="gray.500" mb={1}>
            用户 {message.from_user_id}
          </Text>
        )}
        <Box
          bg={isOwn ? 'blue.500' : 'gray.100'}
          color={isOwn ? 'white' : 'black'}
          px={3}
          py={2}
          borderRadius="lg"
          borderBottomRightRadius={isOwn ? 'sm' : 'lg'}
          borderBottomLeftRadius={isOwn ? 'lg' : 'sm'}
        >
          <Text fontSize="sm">{message.content}</Text>
        </Box>
        <Text fontSize="xs" color="gray.400" mt={1} textAlign={isOwn ? 'right' : 'left'}>
          {formattedTime}
        </Text>
      </Box>
    </Flex>
  );
}

export function ChatArea() {
  const { state: authState } = useAuth();
  const { state: chatState, sendMessage, sendTyping, setCurrentChat } = useChat();
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<number>();

  // 自动滚动到底部
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView();
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  // 处理打字状态
  const handleTyping = (value: string) => {
    setInputMessage(value);
    
    if (!isTyping && value.length > 0) {
      setIsTyping(true);
      sendTyping(true);
    }

    // 清除之前的超时
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // 设置新的超时
    typingTimeoutRef.current = setTimeout(() => {
      if (isTyping) {
        setIsTyping(false);
        sendTyping(false);
      }
    }, 2000);
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || !chatState.currentChat) {
      return;
    }

    sendMessage(inputMessage.trim());
    setInputMessage('');
    
    // 停止打字状态
    if (isTyping) {
      setIsTyping(false);
      sendTyping(false);
    }
    
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
  };

  const handleBackToList = () => {
    setCurrentChat(null);
  };

  if (!chatState.currentChat) {
    return (
      <Flex h="100%" align="center" justify="center" bg="gray.50">
        <VStack gap={4}>
          <Text fontSize="lg" color="gray.500">
            请选择一个对话开始聊天
          </Text>
          <Text fontSize="sm" color="gray.400">
            从左侧选择对话、房间或用户
          </Text>
        </VStack>
      </Flex>
    );
  }

  const currentTypingUsers = chatState.typingUsers.filter(
    user => user.chatId === chatState.currentChat?.id && 
            user.chatType === chatState.currentChat?.type &&
            user.userId !== authState.user?.id
  );

  return (
    <VStack h="100%" gap={0}>
      {/* 聊天头部 */}
      <Box w="full" p={4} borderBottom="1px" borderColor="gray.200" bg="white">
        <HStack justify="space-between">
          <HStack gap={3}>
            <Button
              size="sm"
              variant="ghost"
              display={{ base: 'block', md: 'none' }}
              onClick={handleBackToList}
            >
              ← 返回
            </Button>
            <VStack align="start" gap={0}>
              <Text fontWeight="semibold">
                {chatState.currentChat.name}
              </Text>
              <HStack gap={1}>
                <Box w={2} h={2} bg="green.400" borderRadius="full" />
                <Text fontSize="xs" color="gray.500">
                  {chatState.currentChat.type === 'room' ? '房间' : 
                   chatState.currentChat.type === 'group' ? '群组' : '私聊'}
                </Text>
              </HStack>
            </VStack>
          </HStack>
          <HStack gap={1}>
            <Box
              w={2}
              h={2}
              bg={chatState.isConnected ? 'green.400' : 'red.400'}
              borderRadius="full"
            />
            <Text fontSize="xs" color="gray.500">
              {chatState.isConnected ? '已连接' : '未连接'}
            </Text>
          </HStack>
        </HStack>
      </Box>

      {/* 消息列表 */}
      <Box flex="1" w="full" overflow="auto" p={4}>
        <VStack gap={0} align="stretch">
          {chatState.messages.map((message) => (
            <MessageItem
              key={message.id}
              message={message}
              isOwn={message.from_user_id === authState.user?.id}
              currentUser={authState.user}
            />
          ))}
          
          {/* 打字指示器 */}
          {currentTypingUsers.length > 0 && (
            <Box mb={4}>
              <Text fontSize="xs" color="gray.500" fontStyle="italic">
                {currentTypingUsers.length === 1 
                  ? `用户 ${currentTypingUsers[0].userId} 正在输入...`
                  : `${currentTypingUsers.length} 人正在输入...`
                }
              </Text>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </VStack>
      </Box>

      {/* 输入区域 */}
      <Box w="full" p={4} borderTop="1px" borderColor="gray.200" bg="white">
        <form onSubmit={handleSendMessage}>
          <HStack gap={2}>
            <Input
              placeholder="输入消息..."
              value={inputMessage}
              onChange={(e) => handleTyping(e.target.value)}
              disabled={!chatState.isConnected}
              size="md"
            />
            <Button
              type="submit"
              colorScheme="blue"
              disabled={!inputMessage.trim() || !chatState.isConnected}
              size="md"
            >
              发送
            </Button>
          </HStack>
        </form>
        
        {!chatState.isConnected && (
          <Text fontSize="xs" color="red.500" mt={2}>
            连接已断开，请检查网络连接
          </Text>
        )}
      </Box>
    </VStack>
  );
} 