/**
 * @file AuthProvider.tsx
 * @description Provider quản lý và phân phối trạng thái xác thực hệ thống.
 * Phải được render bên trong <Router> để dùng useNavigate.
 * Search tags: AuthProvider | checkUserAuth | checkAppState | tokenStorage | auth:logout
 */

import React, { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { tokenStorage } from '@/services/axiosClient';
import { authService } from '@/services/auth.service';
import { AuthContext } from '@/hooks/useAuth';
import type { AuthError } from '@/hooks/useAuth';
import type { UserResponse } from '@/services/types';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const navigate = useNavigate();

  const [user, setUser] = useState<UserResponse | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoadingAuth, setIsLoadingAuth] = useState(() => !!tokenStorage.getAccess());
  const [authChecked, setAuthChecked] = useState(() => !tokenStorage.getAccess());
  const [authError, setAuthError] = useState<AuthError | null>(null);

  const checkUserAuth = useCallback(async () => {
    setIsLoadingAuth(true);
    try {
      const currentUser = await authService.me();
      setUser(currentUser);
      setIsAuthenticated(true);
      setAuthError(null);
    } catch (error: unknown) {
      setUser(null);
      setIsAuthenticated(false);
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        setAuthError({
          type: status === 401 || status === 403 ? 'auth_required' : 'unknown',
          message: error.message || 'Authentication failed',
        });
      }
    } finally {
      setIsLoadingAuth(false);
      setAuthChecked(true);
    }
  }, []);

  const checkAppState = useCallback(async () => {
    if (tokenStorage.getAccess()) {
      await checkUserAuth();
    } else {
      setIsLoadingAuth(false);
      setAuthChecked(true);
    }
  }, [checkUserAuth]);

  useEffect(() => {
    const timer = setTimeout(checkAppState, 0);
    return () => clearTimeout(timer);
  }, [checkAppState]);

  useEffect(() => {
    const handleExternalLogout = () => {
      setUser(null);
      setIsAuthenticated(false);
    };
    window.addEventListener('auth:logout', handleExternalLogout);
    return () => window.removeEventListener('auth:logout', handleExternalLogout);
  }, []);

  const logout = useCallback((shouldRedirect = true) => {
    setUser(null);
    setIsAuthenticated(false);
    authService.logout();
    if (shouldRedirect) navigate('/login', { replace: true });
  }, [navigate]);

  const navigateToLogin = useCallback(() => {
    navigate('/login', { replace: true });
  }, [navigate]);

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated,
      isLoadingAuth,
      isLoadingPublicSettings: false,
      authError,
      appPublicSettings: null,
      authChecked,
      logout,
      navigateToLogin,
      checkUserAuth,
      checkAppState,
    }}>
      {children}
    </AuthContext.Provider>
  );
};