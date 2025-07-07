import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Box,
  Grid,
  GridItem,
  Flex,
  Button,
  useBreakpointValue,
  Heading,
  Text,
  VStack,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';

// 临时的简单组件，稍后会更新
const ConversationSidebar = (_props: any) => (
  <Box p={4} h="100%" bg="white" borderRight="1px" borderColor="gray.200">
    <VStack gap={4} align="stretch">
      <Heading size="md" color="gray.800">聊天列表</Heading>
      <Text fontSize="sm" color="gray.500">暂无聊天记录</Text>
    </VStack>
  </Box>
);

const ChatArea = (_props: any) => (
  <Flex
    h="100%"
    direction="column"
    align="center"
    justify="center"
    bg="gray.50"
    p={8}
  >
    <VStack gap={4} textAlign="center">
      <Heading size="lg" color="gray.600">欢迎使用 ChatSphere</Heading>
      <Text color="gray.500" maxW="md">
        选择一个聊天开始对话，或者创建新的聊天房间与朋友交流。
      </Text>
      <Button colorScheme="blue" size="lg">
        开始聊天
      </Button>
    </VStack>
  </Flex>
);

export default function ChatPage() {
  const { state } = useAuth();
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [selectedChatType, setSelectedChatType] = useState<'private' | 'group' | 'room'>('private');
  const [showSidebar, setShowSidebar] = useState(false);
  
  // 响应式断点
  const isMobile = useBreakpointValue({ base: true, lg: false });

  // 如果未登录，重定向到登录页
  if (!state.isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // 处理聊天选择
  const handleChatSelect = (chatId: string, chatType: 'private' | 'group' | 'room') => {
    setSelectedChatId(chatId);
    setSelectedChatType(chatType);
    // 在移动端选择聊天后关闭侧边栏
    if (isMobile) {
      setShowSidebar(false);
    }
  };

  // 桌面端布局
  if (!isMobile) {
    return (
      <Grid
        templateColumns="350px 1fr"
        h="100vh"
        bg="gray.50"
      >
        {/* 侧边栏 */}
        <GridItem bg="white" borderRight="1px" borderColor="gray.200">
          <ConversationSidebar
            onChatSelect={handleChatSelect}
            selectedChatId={selectedChatId}
            selectedChatType={selectedChatType}
          />
        </GridItem>

        {/* 聊天区域 */}
        <GridItem>
          <ChatArea
            chatId={selectedChatId}
            chatType={selectedChatType}
          />
        </GridItem>
      </Grid>
    );
  }

  // 移动端布局
  return (
    <Flex direction="column" h="100vh" bg="gray.50">
      {/* 顶部导航栏 */}
      <Flex
        as="header"
        align="center"
        justify="space-between"
        px={4}
        py={3}
        bg="white"
        borderBottom="1px"
        borderColor="gray.200"
        boxShadow="sm"
      >
        <Button
          variant="ghost"
          onClick={() => setShowSidebar(!showSidebar)}
          size="sm"
        >
          ☰
        </Button>
        <Heading size="md" color="gray.800">
          ChatSphere
        </Heading>
        <Box w={10} /> {/* 占位符，保持标题居中 */}
      </Flex>

      {/* 内容区域 */}
      <Flex flex="1" overflow="hidden">
        {/* 侧边栏 (移动端可隐藏) */}
        {showSidebar && (
          <Box
            w="280px"
            bg="white"
            borderRight="1px"
            borderColor="gray.200"
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
        <Box flex="1">
          <ChatArea
            chatId={selectedChatId}
            chatType={selectedChatType}
          />
        </Box>
      </Flex>
    </Flex>
  );
} 