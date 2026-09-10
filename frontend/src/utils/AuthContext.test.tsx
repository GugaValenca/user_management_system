import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthContext";
import { authAPI } from "../services/api";
import { authStorage } from "./authStorage";
import { User } from "../types";

jest.mock("../services/api", () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    getProfile: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

const TEST_USER = { id: 1, email: "test@example.com", full_name: "Test User" } as User;
const TEST_TOKENS = { access: "access-token", refresh: "refresh-token" };

const TestConsumer: React.FC = () => {
  const { user, isAuthenticated, login, logout } = useAuth();

  return (
    <div>
      <div data-testid="status">{isAuthenticated ? "authenticated" : "anonymous"}</div>
      <div data-testid="user-email">{user?.email ?? "none"}</div>
      <button onClick={() => login({ identifier: "test@example.com", password: "pw" })}>
        Login
      </button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

const renderWithProvider = () =>
  render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );

beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
});

describe("AuthContext", () => {
  it("starts unauthenticated when there is no stored token", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(mockedAuthAPI.getProfile).not.toHaveBeenCalled();
  });

  it("logs in, stores tokens, and exposes the returned user", async () => {
    mockedAuthAPI.login.mockResolvedValue({
      message: "Login successful",
      user: TEST_USER,
      tokens: TEST_TOKENS,
    });
    renderWithProvider();

    userEvent.click(screen.getByText("Login"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("test@example.com");
    expect(authStorage.getAccessToken()).toBe("access-token");
    expect(authStorage.getRefreshToken()).toBe("refresh-token");
  });

  it("clears the session and stored tokens on logout", async () => {
    mockedAuthAPI.login.mockResolvedValue({
      message: "Login successful",
      user: TEST_USER,
      tokens: TEST_TOKENS,
    });
    mockedAuthAPI.logout.mockResolvedValue(undefined);
    renderWithProvider();

    userEvent.click(screen.getByText("Login"));
    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    userEvent.click(screen.getByText("Logout"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(authStorage.getAccessToken()).toBeNull();
    expect(mockedAuthAPI.logout).toHaveBeenCalledWith("refresh-token");
  });

  it("restores the session from a stored access token on mount", async () => {
    authStorage.setTokens(TEST_TOKENS);
    mockedAuthAPI.getProfile.mockResolvedValue(TEST_USER);

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("test@example.com");
  });

  it("clears a stale token when the stored session can't be restored", async () => {
    authStorage.setTokens(TEST_TOKENS);
    mockedAuthAPI.getProfile.mockRejectedValue(new Error("unauthorized"));

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(authStorage.getAccessToken()).toBeNull();
  });
});
