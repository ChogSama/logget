import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';

import { queryClientInstance } from '@/services/queryClient';
import { AuthProvider } from '@/context/AuthProvider';

import ScrollToTop from '@/components/ScrollToTop';
import { Toaster } from '@/components/ui/toaster';
import PageNotFound from '@/components/PageNotFound';
import ProtectedRoute from '@/components/ProtectedRoute';

import Login from '@/screens/Login';
import Register from '@/screens/Register';
import ForgotPassword from '@/screens/ForgotPassword';
import ResetPassword from '@/screens/ResetPassword';
import AuthCallback from '@/screens/AuthCallback';
import Home from '@/screens/Home';

function App() {
  return (
    <Router>
      {/* AuthProvider inside Router — required for useNavigate in AuthProvider */}
      <AuthProvider>
        <QueryClientProvider client={queryClientInstance}>
          <ScrollToTop />
          <Routes>
            {/* Public auth routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* Protected routes */}
            <Route element={<ProtectedRoute unauthenticatedElement={<Navigate to="/login" replace />} />}>
              <Route path="/" element={<Home />} />
            </Route>

            <Route path="*" element={<PageNotFound />} />
          </Routes>
          <Toaster />
        </QueryClientProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;