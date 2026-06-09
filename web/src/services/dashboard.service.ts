/**
 * @file dashboard.service.ts
 * @description API calls for dashboard endpoints (LBS scoring, streak, overview).
 * All endpoints accept an optional IANA timezone string defaulting to Asia/Ho_Chi_Minh on backend.
 * Pass the local timezone for accurate day boundary calculations (see NOTES.md — _local_today).
 * Search tags: getOverview | getLBSTrend | getStreak | OverviewResponse | LBSTrendResponse
 */

import apiClient from "./axiosClient";
import type { OverviewResponse, LBSTrendResponse, StreakResponse } from "./types";

export const dashboardService = {
  getOverview: async (timezone?: string): Promise<OverviewResponse> => {
    const { data } = await apiClient.get<OverviewResponse>("/dashboard/overview", {
      params: { ...(timezone && { timezone }) },
    });
    return data;
  },

  getLBSTrend: async (range?: "7d" | "30d", timezone?: string): Promise<LBSTrendResponse> => {
    const { data } = await apiClient.get<LBSTrendResponse>("/dashboard/lbs", {
      params: {
        ...(range && { range }),
        ...(timezone && { timezone }),
      },
    });
    return data;
  },

  getStreak: async (timezone?: string): Promise<StreakResponse> => {
    const { data } = await apiClient.get<StreakResponse>("/dashboard/streak", {
      params: { ...(timezone && { timezone }) },
    });
    return data;
  },
};