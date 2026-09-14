import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthProvider, useAuth } from "./AuthContext";
import { authAPI } from "../services/api";
import { tokenStore } from "./tokenStore";
import { User } from "../types";

jest.mock("../services/api", () => ({
  authAPI: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    getProfile: jest.fn(),
    refreshSession: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

const TEST_USER = { id: 1, email: "test@example.com", full_name: "Test User" } as User;
const TEST_TOKENS = { access: "access-token", csrf_token: "csrf-token" };

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
  jest.clearAllMocks();
  tokenStore.clear();
  // No httpOnly cookie exists in this test environment, so the silent
  // refresh AuthContext runs on mount fails unless a test opts in below -
  // matching a real first visit with no session.
  mockedAuthAPI.refreshSession.mockRejectedValue(new Error("no session"));
});

describe("AuthContext", () => {
  it("starts unauthenticated when there is no valid refresh cookie", async () => {
    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(mockedAuthAPI.getProfile).not.toHaveBeenCalled();
  });

  it("logs in, stores the access token in memory, and exposes the returned user", async () => {
    mockedAuthAPI.login.mockResolvedValue({
      message: "Login successful",
      user: TEST_USER,
      tokens: TEST_TOKENS,
    });
    renderWithProvider();
    await waitFor(() =>
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous")
    );

    userEvent.click(screen.getByText("Login"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("test@example.com");
    expect(tokenStore.getAccessToken()).toBe("access-token");
  });

  it("clears the session and the in-memory token on logout", async () => {
    mockedAuthAPI.login.mockResolvedValue({
      message: "Login successful",
      user: TEST_USER,
      tokens: TEST_TOKENS,
    });
    mockedAuthAPI.logout.mockResolvedValue(undefined);
    renderWithProvider();
    await waitFor(() =>
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous")
    );

    userEvent.click(screen.getByText("Login"));
    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    userEvent.click(screen.getByText("Logout"));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(tokenStore.getAccessToken()).toBeNull();
    expect(mockedAuthAPI.logout).toHaveBeenCalledWith();
  });

  it("restores the session via a silent refresh when a valid refresh cookie exists", async () => {
    mockedAuthAPI.refreshSession.mockResolvedValue(TEST_TOKENS);
    mockedAuthAPI.getProfile.mockResolvedValue(TEST_USER);

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("test@example.com");
    expect(tokenStore.getAccessToken()).toBe("access-token");
  });

  it("stays anonymous when the refresh succeeds but the profile fetch fails", async () => {
    mockedAuthAPI.refreshSession.mockResolvedValue(TEST_TOKENS);
    mockedAuthAPI.getProfile.mockRejectedValue(new Error("unauthorized"));

    renderWithProvider();

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("anonymous");
    });
    expect(tokenStore.getAccessToken()).toBeNull();
  });
});
