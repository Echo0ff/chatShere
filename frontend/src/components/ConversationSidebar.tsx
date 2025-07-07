import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';

export function ConversationSidebar() {
  const { state: authState, logout } = useAuth();
  const { state: chatState, setCurrentChat, joinRoom } = useChat();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState<'conversations' | 'rooms' | 'users'>('conversations');

  const handleLogout = async () => {
    await logout();
  };

  const handleConversationClick = (conversation: any) => {
    setCurrentChat({
      id: conversation.id,
      type: conversation.type,
      name: conversation.name,
    });
  };

  const handleRoomClick = (room: any) => {
    joinRoom(room.id);
    setCurrentChat({
      id: room.id,
      type: 'room',
      name: room.name,
    });
  };

  const handleUserClick = (user: any) => {
    if (user.id === authState.user?.id) return; // 不能和自己聊天
    
    setCurrentChat({
      id: user.id,
      type: 'private',
      name: user.display_name || user.username,
    });
  };

  const filteredConversations = chatState.conversations.filter(conv =>
    conv.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredRooms = chatState.rooms.filter(room =>
    room.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredUsers = chatState.onlineUsers.filter(user =>
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
            对话
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
                    chatState.currentChat?.id === conversation.id
                      ? 'blue.50'
                      : 'transparent'
                  }
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => handleConversationClick(conversation)}
                >
                  <VStack align="start" gap={1}>
                    <Text fontWeight="medium" fontSize="sm">
                      {conversation.name}
                    </Text>
                    {conversation.last_message && (
                      <Text fontSize="xs" color="gray.500">
                        {conversation.last_message.content}
                      </Text>
                    )}
                  </VStack>
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
                  <VStack align="start" gap={1}>
                    <HStack justify="space-between" w="full">
                      <Text fontWeight="medium" fontSize="sm">
                        {room.name}
                      </Text>
                      <Text fontSize="xs" color="green.500">
                        {room.online_count} 人
                      </Text>
                    </HStack>
                    {room.description && (
                      <Text fontSize="xs" color="gray.500">
                        {room.description}
                      </Text>
                    )}
                  </VStack>
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
                  <VStack align="start" gap={1}>
                    <Text fontWeight="medium" fontSize="sm">
                      {user.display_name || user.username}
                    </Text>
                    <HStack gap={1}>
                      <Box w={2} h={2} bg="green.400" borderRadius="full" />
                      <Text fontSize="xs" color="gray.500">在线</Text>
                    </HStack>
                  </VStack>
                </Box>
              ))
            )}
          </VStack>
        )}
      </Box>
    </VStack>
  );
} 