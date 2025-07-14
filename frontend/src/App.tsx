import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from './components/ui/provider';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';
import { Box } from '@chakra-ui/react';

function App() {
  return (
    <Provider>
      <AuthProvider>
        <ChatProvider>
          <Router>
            <Box minH="100vh" w="100%" position="relative">
              <Routes>
                {/* 默认重定向到聊天页面 */}
                <Route path="/" element={<Navigate to="/chat" replace />} />

                {/* 认证相关路由 */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* 聊天页面 */}
                <Route path="/chat" element={<ChatPage />} />

                {/* 404 页面 */}
                <Route path="*" element={<Navigate to="/chat" replace />} />
              </Routes>
            </Box>
          </Router>
        </ChatProvider>
      </AuthProvider>
    </Provider>
  );
}

export default App;
