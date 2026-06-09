/**
 * @file logs.service.ts
 * @description API calls for activity log CRUD and Cloudinary upload signing.
 *
 * Upload flow:
 *   1. getUploadSign()  → get Cloudinary signed params
 *   2. Upload file directly to Cloudinary using those params
 *   3. createLog({ ..., media_url: <cloudinary_url> })
 *
 * PATCH constraint: if any time field (start_time, end_time) is sent, timezone is required.
 * Search tags: getLogs | createLog | updateLog | deleteLog | getUploadSign | Cloudinary
 */

import apiClient from "./axiosClient";
import type { LogCreate, LogUpdate, LogResponse, CloudinaryUploadSign } from "./types";

export const logsService = {
  getUploadSign: async (): Promise<CloudinaryUploadSign> => {
    const { data } = await apiClient.get<CloudinaryUploadSign>("/logs/upload-sign");
    return data;
  },

  getLogs: async (date: string, timezone?: string): Promise<LogResponse[]> => {
    const { data } = await apiClient.get<LogResponse[]>("/logs", {
      params: { date, ...(timezone && { timezone }) },
    });
    return data;
  },

  createLog: async (payload: LogCreate): Promise<LogResponse> => {
    const { data } = await apiClient.post<LogResponse>("/logs", payload);
    return data;
  },

  updateLog: async (logId: string, payload: LogUpdate): Promise<LogResponse> => {
    const { data } = await apiClient.patch<LogResponse>(`/logs/${logId}`, payload);
    return data;
  },

  deleteLog: async (logId: string): Promise<void> => {
    await apiClient.delete(`/logs/${logId}`);
  },
};