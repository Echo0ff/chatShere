import { useState } from 'react';
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

interface FormData {
  email: string;
  username: string;
  displayName: string;
  password: string;
  confirmPassword: string;
}

export default function RegisterPage() {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    username: '',
    displayName: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<{[key: string]: string}>({});
  const { state, register } = useAuth();

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

  const validateForm = (): {[key: string]: string} => {
    const newErrors: {[key: string]: string} = {};
    
    if (!formData.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '请输入有效的邮箱地址';
    }
    
    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    } else if (formData.username.length < 3) {
      newErrors.username = '用户名至少需要3个字符';
    }
    
    if (!formData.displayName.trim()) {
      newErrors.displayName = '显示名称不能为空';
    }
    
    if (!formData.password) {
      newErrors.password = '密码不能为空';
    } else if (formData.password.length < 6) {
      newErrors.password = '密码至少需要6个字符';
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '请确认密码';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '两次输入的密码不一致';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    try {
      await register(formData.email, formData.username, formData.displayName, formData.password);
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
              加入 ChatSphere
            </Heading>
            <Text color="gray.600" fontSize={{ base: "sm", md: "md" }}>
              创建账户开始与朋友聊天
            </Text>
          </VStack>

          {/* 注册表单 */}
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

                  {/* 邮箱字段 */}
                  <Field.Root invalid={!!errors.email}>
                    <Field.Label>邮箱地址</Field.Label>
                    <Input
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="请输入邮箱地址"
                      size={{ base: "md", md: "lg" }}
                      borderRadius="md"
                      borderColor={errors.email ? "red.300" : "gray.300"}
                      _hover={{
                        borderColor: errors.email ? "red.400" : "gray.400"
                      }}
                      _focus={{
                        borderColor: errors.email ? "red.500" : "blue.500",
                        boxShadow: `0 0 0 1px ${errors.email ? 'red.500' : 'blue.500'}`
                      }}
                    />
                    {errors.email && (
                      <Field.ErrorText>{errors.email}</Field.ErrorText>
                    )}
                  </Field.Root>

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

                  {/* 显示名称字段 */}
                  <Field.Root invalid={!!errors.displayName}>
                    <Field.Label>显示名称</Field.Label>
                    <Input
                      name="displayName"
                      type="text"
                      value={formData.displayName}
                      onChange={handleChange}
                      placeholder="请输入显示名称"
                      size={{ base: "md", md: "lg" }}
                      borderRadius="md"
                      borderColor={errors.displayName ? "red.300" : "gray.300"}
                      _hover={{
                        borderColor: errors.displayName ? "red.400" : "gray.400"
                      }}
                      _focus={{
                        borderColor: errors.displayName ? "red.500" : "blue.500",
                        boxShadow: `0 0 0 1px ${errors.displayName ? 'red.500' : 'blue.500'}`
                      }}
                    />
                    {errors.displayName && (
                      <Field.ErrorText>{errors.displayName}</Field.ErrorText>
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

                  {/* 确认密码字段 */}
                  <Field.Root invalid={!!errors.confirmPassword}>
                    <Field.Label>确认密码</Field.Label>
                    <Input
                      name="confirmPassword"
                      type="password"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                      placeholder="请再次输入密码"
                      size={{ base: "md", md: "lg" }}
                      borderRadius="md"
                      borderColor={errors.confirmPassword ? "red.300" : "gray.300"}
                      _hover={{
                        borderColor: errors.confirmPassword ? "red.400" : "gray.400"
                      }}
                      _focus={{
                        borderColor: errors.confirmPassword ? "red.500" : "blue.500",
                        boxShadow: `0 0 0 1px ${errors.confirmPassword ? 'red.500' : 'blue.500'}`
                      }}
                    />
                    {errors.confirmPassword && (
                      <Field.ErrorText>{errors.confirmPassword}</Field.ErrorText>
                    )}
                  </Field.Root>

                  {/* 注册按钮 */}
                  <Button
                    type="submit"
                    colorScheme="blue"
                    size={{ base: "md", md: "lg" }}
                    loading={state.isLoading}
                    loadingText="注册中..."
                    borderRadius="md"
                    fontWeight="semibold"
                    _hover={{
                      transform: "translateY(-1px)",
                      boxShadow: "lg"
                    }}
                    transition="all 0.2s"
                  >
                    创建账户
                  </Button>
                </Stack>
              </form>
            </Card.Body>
          </Card.Root>

          {/* 登录链接 */}
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
              已有账户？
            </Text>
            <RouterLink
              to="/login"
              style={{
                color: "var(--chakra-colors-blue-500)",
                fontWeight: "500",
                fontSize: "14px",
                textDecoration: "none",
                transition: "color 0.2s"
              }}
            >
              立即登录
            </RouterLink>
          </Flex>
        </VStack>
      </Container>
    </Box>
  );
} 