/**
 * @file AuthProvider.tsx
 * @description Provider quản lý và phân phối trạng thái xác thực hệ thống.
 * * Search tags: AuthProvider | checkUserAuth | checkAppState | tokenStorage
 */

import React, { useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';
import axios from 'axios';
import { tokenStorage } from '@/services/axiosClient';
import { authService } from '@/services/auth.service';
import { AuthContext } from '@/hooks/useAuth';
import type { UserResponse } from '@/services/types';
import type { AuthError } from '@/hooks/useAuth';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  const [isLoadingAuth, setIsLoadingAuth] = useState<boolean>(() => !!tokenStorage.getAccess());
  const [authChecked, setAuthChecked] = useState<boolean>(() => !tokenStorage.getAccess());
  
  const [isLoadingPublicSettings] = useState<boolean>(false);
  const [appPublicSettings] = useState<unknown>(null);  
  const [authError, setAuthError] = useState<AuthError | null>(null);

  const checkUserAuth = useCallback(async () => {
    setIsLoadingAuth(true);
    try {
      const currentUser = await authService.me();
      setUser(currentUser);
      setIsAuthenticated(true);
    } catch (error: unknown) {
      console.error('User auth check failed:', error);
      setIsAuthenticated(false);
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (status === 401 || status === 403) {
          setAuthError({
            type: 'auth_required',
            message: 'Authentication required'
          });
        } else {
          setAuthError({
            type: 'unknown',
            message: error.message || 'Authentication failed'
          });
        }
      }
    } finally {
      setIsLoadingAuth(false);
      setAuthChecked(true);
    }
  }, []);

  const checkAppState = useCallback(async () => {
    const token = tokenStorage.getAccess();
    if (token) {
      await checkUserAuth();
    } else {
      setIsLoadingAuth(false);
      setAuthChecked(true);
    }
  }, [checkUserAuth]);
  
  useEffect(() => {
    const handleExternalLogout = () => {
      setUser(null);
      setIsAuthenticated(false);
    };

    window.addEventListener('auth:logout', handleExternalLogout);
    return () => {
      window.removeEventListener('auth:logout', handleExternalLogout);
    };
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      checkAppState();
    }, 0);

    return () => clearTimeout(timer);
  }, [checkAppState]);

  const logout = (shouldRedirect: boolean = true) => {
    setUser(null);
    setIsAuthenticated(false);
    authService.logout();
    if (shouldRedirect) {
      window.location.href = window.location.origin;
    }
  };

  const navigateToLogin = () => {
    authService.redirectToGoogle();
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated, 
      isLoadingAuth,
      isLoadingPublicSettings,
      authError,
      appPublicSettings,
      authChecked,
      logout,
      navigateToLogin,
      checkUserAuth,
      checkAppState
    }}>
      {children}
    </AuthContext.Provider>
  );
};