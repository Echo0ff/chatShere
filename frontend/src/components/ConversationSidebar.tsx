import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  Badge,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';

// 未读消息数徽章组件
const UnreadBadge = ({ count }: { count: number }) => {
  if (count === 0) return null;
  
  return (
    <Badge
      colorScheme="red"
      variant="solid"
      borderRadius="full"
      minW={5}
      h={5}
      display="flex"
      alignItems="center"
      justifyContent="center"
      fontSize="xs"
      fontWeight="bold"
    >
      {count > 99 ? '99+' : count}
    </Badge>
  );
};

export function ConversationSidebar() {
  const { state: authState, logout } = useAuth();
  const { state: chatState, setCurrentChat, joinRoom, markConversationAsRead, loadConversations } = useChat();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'conversations' | 'rooms' | 'users'>('conversations');

  // 计算总未读数
  const totalUnreadCount = chatState.conversations.reduce((total, conv) => total + conv.unread_count, 0);

  // 根据会话列表为房间和用户添加未读数
  const roomsWithUnread = chatState.rooms.map(room => {
    const roomConversation = chatState.conversations.find(conv => 
      conv.chat_type === 'room' && conv.chat_id === room.id
    );
    return {
      ...room,
      unread_count: roomConversation?.unread_count || 0
    };
  });

  const usersWithUnread = chatState.onlineUsers.map(user => {
    const userConversation = chatState.conversations.find(conv => 
      conv.chat_type === 'private' && conv.chat_id === user.id
    );
    return {
      ...user,
      unread_count: userConversation?.unread_count || 0
    };
  });

  // 加载会话列表
  useEffect(() => {
    if (authState.isAuthenticated) {
      loadConversations();
    }
  }, [authState.isAuthenticated, loadConversations]);

  const handleLogout = async () => {
    await logout();
  };

  const handleConversationClick = async (conversation: any) => {
    // 设置当前聊天
    setCurrentChat({
      id: conversation.chat_id,
      type: conversation.chat_type,
      name: conversation.name,
    });
    
    // 标记会话为已读
    if (conversation.unread_count > 0) {
      await markConversationAsRead(conversation.chat_type, conversation.chat_id);
    }
  };

  const handleRoomClick = async (room: any) => {
    joinRoom(room.id);
    setCurrentChat({
      id: room.id,
      type: 'room',
      name: room.name,
    });
    
    // 标记房间为已读
    if (room.unread_count > 0) {
      await markConversationAsRead('room', room.id);
    }
  };

  const handleUserClick = async (user: any) => {
    if (user.id === authState.user?.id) return; // 不能和自己聊天
    
    setCurrentChat({
      id: user.id,
      type: 'private',
      name: user.display_name || user.username,
    });
    
    // 标记私聊为已读
    if (user.unread_count > 0) {
      await markConversationAsRead('private', user.id);
    }
  };

  const filteredConversations = chatState.conversations.filter(conv =>
    conv.name && conv.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredRooms = roomsWithUnread.filter(room =>
    room.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = usersWithUnread.filter(user =>
    user.id !== authState.user?.id &&
    (user.display_name || user.username).toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <VStack h="100%" gap={0}>
      {/* 用户信息头部 */}
      <Box w="full" p={4} borderBottom="1px" borderColor="gray.200">
        <HStack justify="space-between">
          <VStack align="start" gap={1}>
            <Text fontWeight="semibold" fontSize="sm">
              {authState.user?.display_name || authState.user?.username}
            </Text>
            <HStack gap={1}>
              <Box w={2} h={2} bg="green.400" borderRadius="full" />
              <Text fontSize="xs" color="gray.500">在线</Text>
            </HStack>
          </VStack>
          <Button size="sm" variant="ghost" onClick={handleLogout}>
            登出
          </Button>
        </HStack>
      </Box>

      {/* 搜索框 */}
      <Box w="full" p={4}>
        <Input
          placeholder="搜索..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          size="sm"
        />
      </Box>

      {/* 连接状态 */}
      <Box w="full" px={4}>
        <HStack gap={2}>
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
      </Box>

      {/* 标签按钮 */}
      <Box w="full" p={4}>
        <HStack gap={2}>
          <Button
            size="sm"
            variant={activeTab === 'conversations' ? 'solid' : 'ghost'}
            onClick={() => setActiveTab('conversations')}
          >
            <HStack gap={1}>
              <Text>对话</Text>
              {totalUnreadCount > 0 && <UnreadBadge count={totalUnreadCount} />}
            </HStack>
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'rooms' ? 'solid' : 'ghost'}
            onClick={() => setActiveTab('rooms')}
          >
            房间
          </Button>
          <Button
            size="sm"
            variant={activeTab === 'users' ? 'solid' : 'ghost'}
            onClick={() => setActiveTab('users')}
          >
            用户
          </Button>
        </HStack>
      </Box>

      {/* 内容区域 */}
      <Box w="full" flex="1" overflow="auto">
        {activeTab === 'conversations' && (
          <VStack gap={0} align="stretch">
            {filteredConversations.length === 0 ? (
              <Box p={4} textAlign="center">
                <Text fontSize="sm" color="gray.500">
                  暂无对话
                </Text>
              </Box>
            ) : (
              filteredConversations.map((conversation) => (
                <Box
                  key={conversation.id}
                  p={3}
                  cursor="pointer"
                  bg={
                    chatState.currentChat?.id === conversation.chat_id
                      ? 'blue.50'
                      : 'transparent'
                  }
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => handleConversationClick(conversation)}
                >
                  <HStack justify="space-between" align="start" w="full">
                    <VStack align="start" gap={1} flex="1">
                      <Text fontWeight="medium" fontSize="sm">
                        {conversation.name}
                      </Text>
                      {conversation.last_message && (
                        <Text 
                          fontSize="xs" 
                          color="gray.500"
                          overflow="hidden"
                          textOverflow="ellipsis"
                          whiteSpace="nowrap"
                        >
                          {conversation.last_message.content}
                        </Text>
                      )}
                    </VStack>
                    <VStack align="end" gap={1}>
                      <UnreadBadge count={conversation.unread_count} />
                      {conversation.last_message && (
                        <Text fontSize="xs" color="gray.400">
                          {new Date(conversation.last_message.created_at).toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </Text>
                      )}
                    </VStack>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        )}

        {activeTab === 'rooms' && (
          <VStack gap={0} align="stretch">
            {filteredRooms.length === 0 ? (
              <Box p={4} textAlign="center">
                <Text fontSize="sm" color="gray.500">
                  暂无房间
                </Text>
              </Box>
            ) : (
              filteredRooms.map((room) => (
                <Box
                  key={room.id}
                  p={3}
                  cursor="pointer"
                  bg={
                    chatState.currentChat?.id === room.id
                      ? 'blue.50'
                      : 'transparent'
                  }
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => handleRoomClick(room)}
                >
                  <HStack justify="space-between" align="start" w="full">
                    <VStack align="start" gap={1} flex="1">
                      <Text fontWeight="medium" fontSize="sm">
                        {room.name}
                      </Text>
                      {room.description && (
                        <Text 
                          fontSize="xs" 
                          color="gray.500"
                          overflow="hidden"
                          textOverflow="ellipsis"
                          whiteSpace="nowrap"
                        >
                          {room.description}
                        </Text>
                      )}
                      <Text fontSize="xs" color="green.500">
                        {room.online_count} 人在线
                      </Text>
                    </VStack>
                    <VStack align="end" gap={1}>
                      <UnreadBadge count={room.unread_count} />
                    </VStack>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        )}

        {activeTab === 'users' && (
          <VStack gap={0} align="stretch">
            {filteredUsers.length === 0 ? (
              <Box p={4} textAlign="center">
                <Text fontSize="sm" color="gray.500">
                  暂无在线用户
                </Text>
              </Box>
            ) : (
              filteredUsers.map((user) => (
                <Box
                  key={user.id}
                  p={3}
                  cursor="pointer"
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => handleUserClick(user)}
                >
                  <HStack justify="space-between" align="start" w="full">
                    <VStack align="start" gap={1} flex="1">
                      <Text fontWeight="medium" fontSize="sm">
                        {user.display_name || user.username}
                      </Text>
                      <HStack gap={1}>
                        <Box w={2} h={2} bg="green.400" borderRadius="full" />
                        <Text fontSize="xs" color="gray.500">在线</Text>
                      </HStack>
                    </VStack>
                    <VStack align="end" gap={1}>
                      <UnreadBadge count={user.unread_count} />
                    </VStack>
                  </HStack>
                </Box>
              ))
            )}
          </VStack>
        )}
      </Box>
    </VStack>
  );
} 