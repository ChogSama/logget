/**
 * @file auth.service.ts
 * @description API calls for authentication endpoints.
 * Google OAuth flow: initiate via redirectToGoogle() → backend redirects back
 * to /auth/callback?code=... → call exchangeGoogleCode(code) to get JWT tokens.
 *
 * forgotPassword / resetPassword: STUB — backend endpoints not yet implemented.
 * Remove stub comment and wire real endpoint when backend adds them.
 * Search tags: register | login | refresh | Google OAuth | me | forgotPassword | resetPassword
 */

import apiClient, { tokenStorage } from "./axiosClient";
import type { UserCreate, UserLogin, TokenResponse, UserResponse } from "./types";

export const authService = {
  register: async (payload: UserCreate): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>("/auth/register", payload);
    tokenStorage.set(data.access_token, data.refresh_token);
    return data;
  },

  login: async (payload: UserLogin): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
    tokenStorage.set(data.access_token, data.refresh_token);
    return data;
  },

  redirectToGoogle: () => {
    window.location.href = "/api/auth/google";
  },

  exchangeGoogleCode: async (code: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>("/auth/google/token", { code });
    tokenStorage.set(data.access_token, data.refresh_token);
    return data;
  },

  me: async (): Promise<UserResponse> => {
    const { data } = await apiClient.get<UserResponse>("/auth/me");
    return data;
  },

  // STUB: POST /auth/forgot-password not yet in backend
  forgotPassword: async (_email: string): Promise<void> => {
    return Promise.resolve();
  },

  // STUB: POST /auth/reset-password not yet in backend
  resetPassword: async (_token: string, _newPassword: string): Promise<void> => {
    return Promise.resolve();
  },

  logout: () => {
    tokenStorage.clear();
    window.dispatchEvent(new Event("auth:logout"));
  },
};