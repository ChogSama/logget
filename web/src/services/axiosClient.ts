/**
 * @file axiosClient.ts
 * @description Axios instance for all API calls to the FastAPI backend.
 *
 * Responsibilities:
 *   - Base URL: Vite dev proxy maps /api/* → FastAPI, production uses same origin.
 *   - Request interceptor: injects Authorization: Bearer <access_token>.
 *   - Response interceptor: on 401, attempts silent token refresh via POST /auth/refresh.
 *     Concurrent 401s are queued and replayed after refresh resolves.
 *     On refresh failure, tokens are cleared and window dispatches "auth:logout".
 *
 * Token storage keys: TOKEN_KEY, REFRESH_KEY (localStorage).
 * Other modules must use tokenStorage helpers — do not access localStorage directly.
 *
 * Search tags: tokenStorage | refreshTokens | auth:logout | request interceptor
 */

import axios from "axios";

import type {
  AxiosError,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";

const TOKEN_KEY = "logget_access";
const REFRESH_KEY = "logget_refresh";

// --- Token storage ---

export const tokenStorage = {
  getAccess: () => localStorage.getItem(TOKEN_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(TOKEN_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// --- Axios instance ---

const axiosClient = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// --- Request interceptor: attach Bearer token ---

axiosClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- Response interceptor: silent refresh on 401 ---

type PendingResolver = (token: string) => void;
type PendingRejector = (error: unknown) => void;

let isRefreshing = false;
let pendingQueue: { resolve: PendingResolver; reject: PendingRejector }[] = [];

const flushQueue = (token: string) => {
  pendingQueue.forEach(({ resolve }) => resolve(token));
  pendingQueue = [];
};

const rejectQueue = (error: unknown) => {
  pendingQueue.forEach(({ reject }) => reject(error));
  pendingQueue = [];
};

const refreshTokens = async (): Promise<string> => {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) throw new Error("No refresh token");

  // Direct axios call — bypasses interceptor to avoid infinite loop
  const { data } = await axios.post("/api/auth/refresh", { refresh_token: refresh });
  tokenStorage.set(data.access_token, data.refresh_token);
  return data.access_token;
};

axiosClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    // Skip refresh loop for the refresh endpoint itself
    if (original.url === "/auth/refresh") {
      tokenStorage.clear();
      window.dispatchEvent(new Event("auth:logout"));
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({
          resolve: (token) => {
            original._retry = true;
            original.headers = { ...original.headers, Authorization: `Bearer ${token}` };
            resolve(axiosClient(original));
          },
          reject,
        });
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const newToken = await refreshTokens();
      flushQueue(newToken);
      original.headers = { ...original.headers, Authorization: `Bearer ${newToken}` };
      return axiosClient(original);
    } catch (refreshError) {
      rejectQueue(refreshError);
      tokenStorage.clear();
      window.dispatchEvent(new Event("auth:logout"));
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default axiosClient;