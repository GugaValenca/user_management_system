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
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
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
