/**
 * @file auth.service.ts
 * @description API calls for authentication endpoints.
 * Google OAuth flow: initiate via redirectToGoogle() → backend redirects back
 * to /auth/callback?code=... → call exchangeGoogleCode(code) to get JWT tokens.
 * Search tags: register | login | refresh | Google OAuth | me
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

  // Redirect browser to Google login page (no fetch — full redirect)
  redirectToGoogle: () => {
    window.location.href = "/api/auth/google";
  },

  // Called after Google redirects back to /auth/callback?code=...
  exchangeGoogleCode: async (code: string): Promise<TokenResponse> => {
    const { data } = await apiClient.post<TokenResponse>("/auth/google/token", { code });
    tokenStorage.set(data.access_token, data.refresh_token);
    return data;
  },

  me: async (): Promise<UserResponse> => {
    const { data } = await apiClient.get<UserResponse>("/auth/me");
    return data;
  },

  logout: () => {
    tokenStorage.clear();
    window.dispatchEvent(new Event("auth:logout"));
  },
};