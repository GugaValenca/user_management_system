import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { User, LoginCredentials, RegisterData } from "../types";
import { authAPI } from "../services/api";
import { authStorage } from "./authStorage";

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
    authStorage.clearTokens();
    setUser(null);
  };

  const applyAuthResponse = (response: {
    user: User;
    tokens: { access: string; refresh: string };
  }) => {
    authStorage.setTokens(response.tokens);
    setUser(response.user);
  };

  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = authStorage.getAccessToken();
      if (accessToken) {
        try {
          const userData = await authAPI.getProfile();
          setUser(userData);
        } catch {
          clearSession();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
    // clearSession is stable enough here for one-time initialization.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const authenticate = async (
    request: () => Promise<{ user: User; tokens: { access: string; refresh: string } }>
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
      const refreshToken = authStorage.getRefreshToken();
      if (refreshToken) {
        await authAPI.logout(refreshToken);
      }
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
