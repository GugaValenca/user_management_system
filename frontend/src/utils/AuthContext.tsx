import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { User, LoginCredentials, RegisterData } from "../types";
import { authAPI } from "../services/api";
import { tokenStore } from "./tokenStore";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const clearSession = () => {
    tokenStore.clear();
    setUser(null);
  };

  const applyAuthResponse = (response: {
    user: User;
    tokens: { access: string; csrf_token: string };
  }) => {
    tokenStore.setAccessToken(response.tokens.access);
    tokenStore.setRefreshCsrfToken(response.tokens.csrf_token);
    setUser(response.user);
  };

  useEffect(() => {
    // Neither token is ever persisted (see tokenStore.ts), so every fresh
    // page load starts from zero here - the only thing that can restore a
    // session is a still-valid httpOnly refresh cookie, which this
    // exchanges for a new access token before fetching the profile.
    const initializeAuth = async () => {
      try {
        const { access, csrf_token } = await authAPI.refreshSession();
        tokenStore.setAccessToken(access);
        tokenStore.setRefreshCsrfToken(csrf_token);
        const userData = await authAPI.getProfile();
        setUser(userData);
      } catch {
        clearSession();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
    // clearSession is stable enough here for one-time initialization.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const authenticate = async (
    request: () => Promise<{ user: User; tokens: { access: string; csrf_token: string } }>
  ) => {
    const response = await request();
    applyAuthResponse(response);
  };

  const login = async (credentials: LoginCredentials) => {
    await authenticate(() => authAPI.login(credentials));
  };

  const register = async (data: RegisterData) => {
    await authenticate(() => authAPI.register(data));
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      clearSession();
    }
  };

  const updateUser = (userData: Partial<User>) => {
    if (user) {
      setUser({ ...user, ...userData });
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
