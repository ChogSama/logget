/**
 * @file axiosClient.ts
 * @description Native mock service replacing legacy @base44/sdk entirely.
 */

import { format } from "date-fns";

// --- MOCK DATABASE DATA STORE ---
const mockUser = {
  id: "usr_mock_999",
  email: "developer@hanoi.gov.vn",
  role: "admin",
  name: "Mock Administrator"
};

const generateMockVlogs = () => {
  const entries = [];
  for (let i = 0; i < 10; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    entries.push({
      id: `vlog_${i}`,
      title: `Vlog entry day -${i}`,
      content: `This is a mock description for vlog entry number ${i}.`,
      created_date: format(date, "yyyy-MM-dd HH:mm:ss")
    });
  }
  return entries;
};

const generateMockHealth = () => {
  const entries = [];
  for (let i = 0; i < 10; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    entries.push({
      id: `health_${i}`,
      date: format(date, "yyyy-MM-dd"),
      status: "Excellent",
      steps: 8000 + (i * 200),
      sleep_hours: 7.5,
      created_date: format(date, "yyyy-MM-dd HH:mm:ss")
    });
  }
  return entries;
};

const mockVlogEntries = generateMockVlogs();
const mockHealthEntries = generateMockHealth();

// --- REPLACEMENT FOR createAxiosClient ---
// Simulates the client returned by @base44/sdk/dist/utils/axios-client
export const createAxiosClient = (_config?: any) => {
  return {
    get: async (url: string) => {
      console.log(`Mock Axios GET request to: ${url}`);
      if (url.includes("/api/apps/public")) {
        return {
          data: {
            id: "mock_app_id_001",
            public_settings: {
              auth_required: false,
              maintenance_mode: false,
              theme: "dark"
            }
          }
        };
      }
      return { data: {} };
    },
    post: async (url: string, data: any) => {
      console.log(`Mock Axios POST request to: ${url}`, data);
      return { data: { success: true } };
    }
  };
};

// --- MOCK CORE SDK SERVICE ---
export const axiosClient = {
  auth: {
    me: async (): Promise<typeof mockUser> => {
      return new Promise((resolve) => setTimeout(() => resolve(mockUser), 200));
    },
    loginViaEmailPassword: async (email: string, _: string): Promise<{ success: boolean }> => {
      console.log(`Mock login execution for: ${email}`);
      return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
    },
    loginWithProvider: (provider: string, redirectUrl: string): void => {
      console.log(`Redirecting to mock OAuth provider: ${provider}`);
      window.location.href = redirectUrl;
    },
    register: async (payload: any): Promise<{ success: boolean }> => {
      console.log("Mock registration payload processing:", payload);
      return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
    },
    verifyOtp: async (payload: { email: string; otpCode: string }): Promise<{ access_token: string }> => {
      console.log("Mock OTP confirmation:", payload);
      return new Promise((resolve) => resolve({ access_token: "mock_jwt_access_token_xyz" }));
    },
    resendOtp: async (email: string): Promise<{ success: boolean }> => {
      console.log(`Mock resending verification code to: ${email}`);
      return new Promise((resolve) => resolve({ success: true }));
    },
    resetPasswordRequest: async (email: string): Promise<{ success: boolean }> => {
      console.log(`Mock system password recovery request for: ${email}`);
      return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 200));
    },
    resetPassword: async (payload: any): Promise<{ success: boolean }> => {
      console.log("Mock executing ultimate password mutation:", payload);
      return new Promise((resolve) => setTimeout(() => resolve({ success: true }), 300));
    },
    logout: (redirectUrl?: string): void => {
      console.log("Mock clearing context session state.");
      if (redirectUrl) window.location.href = redirectUrl;
    },
    redirectToLogin: (redirectUrl: string): void => {
      window.location.href = `/login?redirect=${encodeURIComponent(redirectUrl)}`;
    },
    setToken: (token: string): void => {
      console.log(`Mock system token assignment: ${token}`);
    }
  },

  entities: {
    VlogEntry: {
      list: async (_orderBy: string, _limit: number): Promise<typeof mockVlogEntries> => {
        return new Promise((resolve) => resolve(mockVlogEntries));
      }
    },
    DailyHealth: {
      list: async (_orderBy: string, _limit: number): Promise<typeof mockHealthEntries> => {
        return new Promise((resolve) => resolve(mockHealthEntries));
      }
    }
  }
};

// Fallback compatibility naming
export const base44 = axiosClient;