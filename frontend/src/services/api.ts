import axios, { AxiosError, AxiosRequestConfig } from "axios";
import {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  ActivityLog,
  UserStats,
} from "../types";
import { authStorage } from "../utils/authStorage";

type RetryableRequestConfig = AxiosRequestConfig & { _retry?: boolean };
type PaginatedResponse<T> = { results: T[] };

const defaultApiBaseUrl =
  window.location.hostname === "localhost" ? "http://localhost:8000/api" : "/api";

const API_BASE_URL = (
  process.env.REACT_APP_API_BASE_URL || defaultApiBaseUrl
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

const getListData = <T>(
  config: Promise<{ data: T[] | PaginatedResponse<T> }>
): Promise<T[]> =>
  config.then((res) => ("results" in res.data ? res.data.results : res.data));

api.interceptors.request.use(
  (config) => {
    const requestUrl = String(config.url ?? "");
    const isPublicAuthEndpoint =
      requestUrl.includes("/auth/login/") || requestUrl.includes("/auth/register/");
    const token = authStorage.getAccessToken();
    if (token && !isPublicAuthEndpoint) {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetryableRequestConfig | undefined;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      const refreshToken = authStorage.getRefreshToken();
      if (refreshToken) {
        // Token refresh is not implemented yet; keep behavior unchanged.
        redirectToLogin();
      }
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
    return getResponseData(api.post("/auth/login/", credentials));
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
  }): Promise<void> =>
    getResponseData(api.post("/auth/change-password/", data)),

  getActivityLogs: (): Promise<ActivityLog[]> =>
    getListData(api.get("/auth/activity-logs/")),

  getUserStats: (): Promise<UserStats> => getResponseData(api.get("/auth/stats/")),

  getAllUsers: (): Promise<User[]> => getListData(api.get("/auth/users/")),
};

export default api;
