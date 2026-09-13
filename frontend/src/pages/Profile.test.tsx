import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Profile from "./Profile";
import { authAPI } from "../services/api";
import { useAuth } from "../utils/AuthContext";
import { User } from "../types";

jest.mock("../services/api", () => ({
  authAPI: {
    updateProfile: jest.fn(),
    changePassword: jest.fn(),
  },
}));

jest.mock("../utils/AuthContext", () => ({
  useAuth: jest.fn(),
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;
const mockUseAuth = useAuth as jest.Mock;

const BASE_USER: User = {
  id: 1,
  email: "user@example.com",
  username: "testuser",
  first_name: "Test",
  last_name: "User",
  full_name: "Test User",
  role: "user",
  phone_number: "",
  date_of_birth: null,
  bio: "",
  is_email_verified: true,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

beforeEach(() => {
  jest.clearAllMocks();
  mockUseAuth.mockReturnValue({ user: BASE_USER, updateUser: jest.fn() });
});

describe("Profile", () => {
  it("sends null (not an empty string) for an untouched date of birth", async () => {
    // DRF's DateField rejects "" outright - this is the exact bug that
    // broke profile updates in production for any user without a stored
    // date of birth, which is most of them.
    mockedAuthAPI.updateProfile.mockResolvedValue({ ...BASE_USER, bio: "Hello" });

    render(<Profile />);
    userEvent.clear(screen.getByLabelText(/^bio$/i));
    userEvent.type(screen.getByLabelText(/^bio$/i), "Hello");
    userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(mockedAuthAPI.updateProfile).toHaveBeenCalledWith(
        expect.objectContaining({ date_of_birth: null })
      );
    });
  });

  it("shows the backend's specific field error instead of a generic message", async () => {
    mockedAuthAPI.updateProfile.mockRejectedValue({
      response: { data: { date_of_birth: ["Date has wrong format."] } },
    });

    render(<Profile />);
    userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText("Date has wrong format.")).toBeInTheDocument();
    });
  });

  it("falls back to a generic message when the error has no field detail", async () => {
    mockedAuthAPI.updateProfile.mockRejectedValue(new Error("network error"));

    render(<Profile />);
    userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText(/failed to update profile/i)).toBeInTheDocument();
    });
  });

  it("shows a success message and updates the auth context on success", async () => {
    const updateUser = jest.fn();
    mockUseAuth.mockReturnValue({ user: BASE_USER, updateUser });
    mockedAuthAPI.updateProfile.mockResolvedValue({ ...BASE_USER, bio: "Updated" });

    render(<Profile />);
    userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
    });
    expect(updateUser).toHaveBeenCalledWith(expect.objectContaining({ bio: "Updated" }));
  });
});
