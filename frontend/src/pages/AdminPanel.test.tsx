import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import AdminPanel from "./AdminPanel";
import { authAPI } from "../services/api";
import { useAuth } from "../utils/AuthContext";
import { User } from "../types";

jest.mock("../services/api", () => ({
  authAPI: {
    getUserStats: jest.fn(),
    getAllUsers: jest.fn(),
    updateUser: jest.fn(),
  },
}));

jest.mock("../utils/AuthContext", () => ({
  useAuth: jest.fn(),
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;
const mockUseAuth = useAuth as jest.Mock;

const ADMIN_USER = { id: 1, role: "admin" } as User;

const OTHER_USER: User = {
  id: 2,
  email: "target@example.com",
  username: "target",
  first_name: "Target",
  last_name: "User",
  full_name: "Target User",
  role: "user",
  is_email_verified: true,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const paginatedResponse = (results: User[]) => ({
  count: results.length,
  next: null,
  previous: null,
  results,
});

beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({ user: ADMIN_USER });
  mockedAuthAPI.getUserStats.mockResolvedValue({
    total_users: 2,
    active_users: 2,
    admin_users: 1,
    inactive_users: 0,
  });
  mockedAuthAPI.getAllUsers.mockResolvedValue(paginatedResponse([OTHER_USER]));
});

describe("AdminPanel", () => {
  it("renders the user list and stats once loaded", async () => {
    render(<AdminPanel />);

    await waitFor(() => {
      expect(screen.getByText("target@example.com")).toBeInTheDocument();
    });
    expect(screen.getByText("Total Users")).toBeInTheDocument();
  });

  it("changes a user's role and reflects it in the table", async () => {
    mockedAuthAPI.updateUser.mockResolvedValue({ ...OTHER_USER, role: "moderator" });
    render(<AdminPanel />);

    await screen.findByText("target@example.com");

    const roleSelect = screen.getByLabelText(/role for target@example.com/i);
    userEvent.selectOptions(roleSelect, "moderator");

    await waitFor(() => {
      expect(mockedAuthAPI.updateUser).toHaveBeenCalledWith(2, { role: "moderator" });
    });
  });

  it("deactivates a user and updates the badge", async () => {
    mockedAuthAPI.updateUser.mockResolvedValue({ ...OTHER_USER, is_active: false });
    render(<AdminPanel />);

    await screen.findByText("target@example.com");

    userEvent.click(screen.getByRole("button", { name: /deactivate/i }));

    await waitFor(() => {
      expect(mockedAuthAPI.updateUser).toHaveBeenCalledWith(2, { is_active: false });
    });
    await waitFor(() => {
      expect(screen.getByText("Deactivated")).toBeInTheDocument();
    });
  });

  it("disables role and status controls for the admin's own row", async () => {
    mockedAuthAPI.getAllUsers.mockResolvedValue(
      paginatedResponse([{ ...OTHER_USER, id: 1, email: "self@example.com" }])
    );

    render(<AdminPanel />);

    await screen.findByText("self@example.com");

    expect(screen.getByLabelText(/role for self@example.com/i)).toBeDisabled();
    expect(screen.getByRole("button", { name: /deactivate/i })).toBeDisabled();
  });

  it("shows an error message when a role update fails", async () => {
    mockedAuthAPI.updateUser.mockRejectedValue(new Error("network error"));
    render(<AdminPanel />);

    await screen.findByText("target@example.com");

    userEvent.selectOptions(
      screen.getByLabelText(/role for target@example.com/i),
      "admin"
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to update role/i)).toBeInTheDocument();
    });
  });
});
