import axios from "axios";
import {
  LoginCredentials,
  RegisterData,
  AuthResponse,
  User,
  ActivityLog,
  UserStats,
} from "../types";

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

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          // Here you would implement token refresh logic
          // For now, we'll redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        } catch (refreshError) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data: RegisterData): Promise<AuthResponse> =>
    api.post("/auth/register/", data).then((res) => res.data),

  login: (credentials: LoginCredentials): Promise<AuthResponse> =>
    api.post("/auth/login/", credentials).then((res) => res.data),

  logout: (refreshToken: string): Promise<void> =>
    api
      .post("/auth/logout/", { refresh_token: refreshToken })
      .then((res) => res.data),

  getProfile: (): Promise<User> =>
    api.get("/auth/profile/").then((res) => res.data),

  updateProfile: (data: Partial<User>): Promise<User> =>
    api.patch("/auth/profile/", data).then((res) => res.data),

  changePassword: (data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Promise<void> =>
    api.post("/auth/change-password/", data).then((res) => res.data),

  getActivityLogs: (): Promise<ActivityLog[]> =>
    api.get("/auth/activity-logs/").then((res) => res.data.results || res.data),

  getUserStats: (): Promise<UserStats> =>
    api.get("/auth/stats/").then((res) => res.data),

  getAllUsers: (): Promise<User[]> =>
    api.get("/auth/users/").then((res) => res.data.results || res.data),
};

export default api;
