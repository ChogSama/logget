/**
 * @file types.ts
 * @description TypeScript types generated from OpenAPI schema (openapi.json).
 * Single source of truth for all API request/response shapes on the frontend.
 * Do NOT manually diverge from backend schema — regenerate when backend changes.
 *
 * Search tags: ActivityType | IntensityType | InsightType
 *              LogCreate | LogUpdate | LogResponse
 *              DailyInsightResponse | AIInsightResponse | LBSTrendResponse
 *              OverviewResponse | StreakResponse
 *              TokenResponse | UserResponse | UserCreate | UserLogin
 */

// --- Enums ---

export type ActivityType = "work" | "sleep" | "exercise" | "social" | "recovery";
export type IntensityType = "moderate" | "vigorous";
export type InsightType = "daily" | "pattern";

// --- Auth ---

export interface UserCreate {
  email: string;
  password: string;
  name?: string | null;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface OAuthCodeRequest {
  code: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  created_at: string;
}

// --- Logs ---

export interface LogCreate {
  activity_type: ActivityType;
  start_time: string;   // ISO 8601 datetime
  end_time: string;     // ISO 8601 datetime
  timezone: string;     // IANA timezone string
  intensity?: IntensityType | null;
  note?: string | null;
  media_url?: string | null;
}

export interface LogUpdate {
  activity_type?: ActivityType | null;
  start_time?: string | null;
  end_time?: string | null;
  timezone?: string | null;
  intensity?: IntensityType | null;
  note?: string | null;
  media_url?: string | null;
}

export interface LogResponse {
  id: string;
  user_id: string;
  activity_type: ActivityType;
  duration_hours: number | null;
  intensity: IntensityType | null;
  note: string | null;
  media_url: string | null;
  logged_at: string;
  created_at: string;
}

// --- Insights ---

export interface AnalyzeRequest {
  date: string;         // ISO date: "YYYY-MM-DD"
  timezone?: string;
}

export interface DailyInsightResponse {
  date: string;
  status: string | null;
  lbs_score: number | null;
  work_score: number | null;
  sleep_score: number | null;
  exercise_score: number | null;
  social_score: number | null;
  recovery_score: number | null;
  imbalance_risk: boolean | null;
  ai_summary: string | null;
}

export interface AIInsightResponse {
  id: string;
  insight_type: InsightType;
  content: string;
  reference_date: string | null;
  created_at: string;
}

// --- Dashboard ---

export interface LBSTrendPoint {
  date: string;
  lbs_score: number | null;
  work_score: number | null;
  sleep_score: number | null;
  exercise_score: number | null;
  social_score: number | null;
  recovery_score: number | null;
}

export interface LBSTrendResponse {
  range: "week" | "month";
  data: LBSTrendPoint[];
}

export interface OverviewResponse {
  date: string;
  lbs_score: number | null;
  imbalance_risk: boolean | null;
  burnout_alert: string | null;
  current_streak: number;
  balance_ratio: number;
  total_logged_days: number;
}

export interface StreakResponse {
  current_streak: number;
  balance_ratio: number;
  total_logged_days: number;
}

// --- Cloudinary upload signature (GET /logs/upload-sign) ---
// Backend returns Cloudinary signed upload params. Shape is not in OpenAPI,
// defined here based on Cloudinary's signed upload API.
export interface CloudinaryUploadSign {
  signature: string;
  timestamp: number;
  cloud_name: string;
  api_key: string;
  folder?: string;
}