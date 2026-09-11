export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: "admin" | "user" | "moderator";
  profile_picture?: string;
  phone_number?: string;
  date_of_birth?: string;
  bio?: string;
  is_email_verified: boolean;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  identifier: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

export interface ActivityLog {
  id: number;
  user_email: string;
  activity_type: string;
  description: string;
  ip_address?: string;
  timestamp: string;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  inactive_users: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PasswordResetConfirmData {
  uid: string;
  token: string;
  new_password: string;
  new_password_confirm: string;
}

export interface EmailVerificationConfirmData {
  uid: string;
  token: string;
}

export interface AdminUserUpdateData {
  role?: User["role"];
  is_active?: boolean;
}

export interface AdminUserListParams {
  page?: number;
  search?: string;
  role?: User["role"] | "";
  is_active?: "true" | "false" | "";
}
