/**
 * @file useAuth.ts
 * @description Authentication context definition and custom hook.
 * Provides the shared state and auth methods across the application.
 */

import { createContext, useContext } from 'react';
import type { UserResponse } from '@/services/types';

export interface AuthError {
  type: string;
  message: string;
}

export interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoadingAuth: boolean;
  isLoadingPublicSettings: boolean;
  authError: AuthError | null;
  appPublicSettings: unknown;
  authChecked: boolean;
  logout: (shouldRedirect?: boolean) => void;
  navigateToLogin: () => void;
  checkUserAuth: () => Promise<void>;
  checkAppState: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};