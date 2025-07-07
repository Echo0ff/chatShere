import { useState, useContext } from 'react';
import { Navigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  Container,
  Flex,
  Heading,
  Input,
  Stack,
  Text,
  VStack,
  Alert,
  Link,
} from '@chakra-ui/react';
import { useAuth } from '../contexts/AuthContext';

// Field组件 (Chakra UI v3需要自定义)
const Field = {
  Root: ({ children, invalid, ...props }: any) => (
    <Box {...props} aria-invalid={invalid}>
      {children}
    </Box>
  ),
  Label: ({ children, ...props }: any) => (
    <Text as="label" fontSize="sm" fontWeight="medium" mb={1} {...props}>
      {children}
    </Text>
  ),
  ErrorText: ({ children, ...props }: any) => (
    <Text color="red.500" fontSize="sm" mt={1} {...props}>
      {children}
    </Text>
  ),
};

export default function LoginPage() {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const { state, login } = useAuth();

  if (state.isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 表单验证
    const newErrors: {[key: string]: string} = {};
    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    }
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await login(formData.username, formData.password);
    } catch (error) {
      // 错误在AuthContext中处理
    }
  };

  return (
    <Box
      minH="100vh"
      w="100%"
      bg={{ base: "gray.50", md: "gray.100" }}
      display="flex"
      alignItems="center"
      justifyContent="center"
      p={4}
      position="relative"
    >
      <Container maxW="md" w="full">
        <VStack gap={8} align="stretch">
          {/* 标题区域 */}
          <VStack gap={2} textAlign="center">
            <Heading
              size={{ base: "lg", md: "xl" }}
              color="gray.800"
              fontWeight="bold"
            >
              欢迎回到 ChatSphere
            </Heading>
            <Text color="gray.600" fontSize={{ base: "sm", md: "md" }}>
              登录您的账户开始聊天
            </Text>
          </VStack>

          {/* 登录表单 */}
          <Card.Root
            boxShadow={{ base: "md", md: "lg" }}
            borderRadius="xl"
            overflow="hidden"
          >
            <Card.Body p={{ base: 6, md: 8 }}>
              <form onSubmit={handleSubmit}>
                <Stack gap={6}>
                  {/* 错误提示 */}
                  {state.error && (
                    <Alert.Root status="error" borderRadius="md">
                      <Alert.Indicator />
                      <Alert.Description>{state.error}</Alert.Description>
                    </Alert.Root>
                  )}

                  {/* 用户名字段 */}
                  <Field.Root invalid={!!errors.username}>
                    <Field.Label>用户名</Field.Label>
                    <Input
                      name="username"
                      type="text"
                      value={formData.username}
                      onChange={handleChange}
                      placeholder="请输入用户名"
                      size={{ base: "md", md: "lg" }}
                      borderRadius="md"
                      borderColor={errors.username ? "red.300" : "gray.300"}
                      _hover={{
                        borderColor: errors.username ? "red.400" : "gray.400"
                      }}
                      _focus={{
                        borderColor: errors.username ? "red.500" : "blue.500",
                        boxShadow: `0 0 0 1px ${errors.username ? 'red.500' : 'blue.500'}`
                      }}
                    />
                    {errors.username && (
                      <Field.ErrorText>{errors.username}</Field.ErrorText>
                    )}
                  </Field.Root>

                  {/* 密码字段 */}
                  <Field.Root invalid={!!errors.password}>
                    <Field.Label>密码</Field.Label>
                    <Input
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="请输入密码"
                      size={{ base: "md", md: "lg" }}
                      borderRadius="md"
                      borderColor={errors.password ? "red.300" : "gray.300"}
                      _hover={{
                        borderColor: errors.password ? "red.400" : "gray.400"
                      }}
                      _focus={{
                        borderColor: errors.password ? "red.500" : "blue.500",
                        boxShadow: `0 0 0 1px ${errors.password ? 'red.500' : 'blue.500'}`
                      }}
                    />
                    {errors.password && (
                      <Field.ErrorText>{errors.password}</Field.ErrorText>
                    )}
                  </Field.Root>

                  {/* 登录按钮 */}
                  <Button
                    type="submit"
                    colorScheme="blue"
                    size={{ base: "md", md: "lg" }}
                    loading={state.isLoading}
                    loadingText="登录中..."
                    borderRadius="md"
                    fontWeight="semibold"
                    _hover={{
                      transform: "translateY(-1px)",
                      boxShadow: "lg"
                    }}
                    transition="all 0.2s"
                  >
                    登录
                  </Button>
                </Stack>
              </form>
            </Card.Body>
          </Card.Root>

          {/* 注册链接 */}
          <Flex
            justify="center"
            align="center"
            gap={2}
            p={4}
            bg="white"
            borderRadius="lg"
            boxShadow="sm"
          >
            <Text color="gray.600" fontSize="sm">
              还没有账户？
            </Text>
            <RouterLink
              to="/register"
              style={{
                color: "var(--chakra-colors-blue-500)",
                fontWeight: "500",
                fontSize: "14px",
                textDecoration: "none",
                transition: "color 0.2s"
              }}
            >
              立即注册
            </RouterLink>
          </Flex>
        </VStack>
      </Container>
    </Box>
  );
} 