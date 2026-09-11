import axios, { AxiosError, AxiosRequestConfig } from "axios";
import {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  ActivityLog,
  UserStats,
  PaginatedResponse,
  PasswordResetConfirmData,
  EmailVerificationConfirmData,
  AdminUserUpdateData,
  AdminUserListParams,
} from "../types";
import { authStorage } from "../utils/authStorage";

type RetryableRequestConfig = AxiosRequestConfig & { _retry?: boolean };
type ListResponse<T> = T[] | PaginatedResponse<T>;

const defaultApiBaseUrl =
  window.location.hostname === "localhost" ? "http://localhost:8000/api" : "/api";

const configuredApiBaseUrl = (process.env.REACT_APP_API_BASE_URL || "").trim();
const shouldIgnoreConfiguredLocalhostUrl =
  window.location.hostname !== "localhost" && configuredApiBaseUrl.includes("localhost");

const API_BASE_URL = (
  shouldIgnoreConfiguredLocalhostUrl || !configuredApiBaseUrl
    ? defaultApiBaseUrl
    : configuredApiBaseUrl
).replace(/\/+$/, "");

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

const redirectToLogin = () => {
  authStorage.clearTokens();
  window.location.href = "/login";
};

const getResponseData = <T>(config: Promise<{ data: T }>): Promise<T> =>
  config.then((res) => res.data);

const getPaginatedData = <T>(
  config: Promise<{ data: ListResponse<T> }>
): Promise<PaginatedResponse<T>> =>
  config.then((res) =>
    "results" in res.data
      ? res.data
      : { count: res.data.length, next: null, previous: null, results: res.data }
  );

api.interceptors.request.use(
  (config) => {
    const requestUrl = String(config.url ?? "");
    const isPublicAuthEndpoint =
      requestUrl.includes("/auth/login/") ||
      requestUrl.includes("/auth/register/") ||
      requestUrl.includes("/auth/refresh/") ||
      requestUrl.includes("/auth/password-reset/") ||
      requestUrl.includes("/auth/verify-email/confirm/");
    const token = authStorage.getAccessToken();
    if (token && !isPublicAuthEndpoint) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Concurrent requests that all 401 at once share a single refresh call
// instead of each firing their own (which would race to rotate the
// refresh token and blacklist each other).
let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async (): Promise<string | null> => {
  const refreshToken = authStorage.getRefreshToken();
  if (!refreshToken) return null;

  try {
    const { data } = await axios.post<{ access: string }>(
      `${API_BASE_URL}/auth/refresh/`,
      {
        refresh: refreshToken,
      }
    );
    authStorage.setAccessToken(data.access);
    return data.access;
  } catch {
    return null;
  }
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;
    const requestUrl = String(originalRequest?.url ?? "");
    const isRefreshEndpoint = requestUrl.includes("/auth/refresh/");

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isRefreshEndpoint
    ) {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newAccessToken = await refreshPromise;

      if (newAccessToken) {
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      }

      redirectToLogin();
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data: RegisterData): Promise<AuthResponse> =>
    getResponseData(api.post("/auth/register/", data)),

  login: (credentials: LoginCredentials): Promise<AuthResponse> => {
    // Avoid stale-token auth failures on login endpoints.
    authStorage.clearTokens();
    const normalizedIdentifier = credentials.identifier.trim();
    return getResponseData(
      api.post("/auth/login/", {
        identifier: normalizedIdentifier,
        // Backward compatibility: older backend versions expect `email`.
        email: normalizedIdentifier,
        password: credentials.password,
      })
    );
  },

  logout: (refreshToken: string): Promise<void> =>
    getResponseData(api.post("/auth/logout/", { refresh_token: refreshToken })),

  getProfile: (): Promise<User> => getResponseData(api.get("/auth/profile/")),

  updateProfile: (data: Partial<User>): Promise<User> =>
    getResponseData(api.patch("/auth/profile/", data)),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> => getResponseData(api.post("/auth/change-password/", data)),

  requestPasswordReset: (email: string): Promise<{ message: string }> =>
    getResponseData(api.post("/auth/password-reset/", { email })),

  confirmPasswordReset: (data: PasswordResetConfirmData): Promise<{ message: string }> =>
    getResponseData(api.post("/auth/password-reset/confirm/", data)),

  confirmEmailVerification: (
    data: EmailVerificationConfirmData
  ): Promise<{ message: string }> =>
    getResponseData(api.post("/auth/verify-email/confirm/", data)),

  resendEmailVerification: (): Promise<{ message: string }> =>
    getResponseData(api.post("/auth/verify-email/resend/")),

  getActivityLogs: (page = 1): Promise<PaginatedResponse<ActivityLog>> =>
    getPaginatedData(api.get("/auth/activity-logs/", { params: { page } })),

  getUserStats: (): Promise<UserStats> => getResponseData(api.get("/auth/stats/")),

  getAllUsers: (params: AdminUserListParams = {}): Promise<PaginatedResponse<User>> =>
    getPaginatedData(api.get("/auth/users/", { params })),

  updateUser: (userId: number, data: AdminUserUpdateData): Promise<User> =>
    getResponseData(api.patch(`/auth/users/${userId}/`, data)),
};

export default api;
