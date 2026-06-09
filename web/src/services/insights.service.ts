/**
 * @file insights.service.ts
 * @description API calls for AI insight endpoints.
 *
 * getDaily: returns cached DailyInsightResponse if analysis already run for that date.
 * analyze: triggers Gemini analysis for the given date; creates or updates the summary.
 * getPatterns: returns a single AIInsightResponse for the requested range (7d | 30d).
 * Search tags: getDaily | analyze | getPatterns | DailyInsightResponse | AIInsightResponse
 */

import apiClient from "./axiosClient";
import type { AnalyzeRequest, DailyInsightResponse, AIInsightResponse } from "./types";

export const insightsService = {
  getDaily: async (date: string, timezone?: string): Promise<DailyInsightResponse> => {
    const { data } = await apiClient.get<DailyInsightResponse>("/insights/daily", {
      params: { date, ...(timezone && { timezone }) },
    });
    return data;
  },

  analyze: async (payload: AnalyzeRequest): Promise<DailyInsightResponse> => {
    const { data } = await apiClient.post<DailyInsightResponse>("/insights/analyze", payload);
    return data;
  },

  getPatterns: async (range?: "7d" | "30d"): Promise<AIInsightResponse> => {
    const { data } = await apiClient.get<AIInsightResponse>("/insights/patterns", {
      params: { ...(range && { range }) },
    });
    return data;
  },
};