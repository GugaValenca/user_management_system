import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ResetPassword from "./ResetPassword";
import { authAPI } from "../services/api";

jest.mock("../services/api", () => ({
  authAPI: {
    confirmPasswordReset: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

const renderPage = (path = "/reset-password?uid=MQ&token=abc123") =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/login" element={<div>Login page</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ResetPassword", () => {
  it("warns when the link is missing uid/token", () => {
    renderPage("/reset-password");

    expect(screen.getByText(/missing required information/i)).toBeInTheDocument();
  });

  it("submits the new password using the uid/token from the URL", async () => {
    mockedAuthAPI.confirmPasswordReset.mockResolvedValue({
      message: "Password reset successfully. Please log in again.",
    });

    renderPage();
    userEvent.type(screen.getByLabelText(/^new password$/i), "NewPass123!");
    userEvent.type(screen.getByLabelText(/^confirm new password$/i), "NewPass123!");
    userEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(screen.getByText(/password reset successfully/i)).toBeInTheDocument();
    });
    expect(mockedAuthAPI.confirmPasswordReset).toHaveBeenCalledWith({
      uid: "MQ",
      token: "abc123",
      new_password: "NewPass123!",
      new_password_confirm: "NewPass123!",
    });
  });

  it("rejects mismatched passwords before calling the API", async () => {
    renderPage();
    userEvent.type(screen.getByLabelText(/^new password$/i), "NewPass123!");
    userEvent.type(screen.getByLabelText(/^confirm new password$/i), "Different456!");
    userEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
    expect(mockedAuthAPI.confirmPasswordReset).not.toHaveBeenCalled();
  });

  it("shows the server error for an invalid or expired link", async () => {
    mockedAuthAPI.confirmPasswordReset.mockRejectedValue({
      response: {
        data: { non_field_errors: ["This reset link is invalid or has expired"] },
      },
    });

    renderPage();
    userEvent.type(screen.getByLabelText(/^new password$/i), "NewPass123!");
    userEvent.type(screen.getByLabelText(/^confirm new password$/i), "NewPass123!");
    userEvent.click(screen.getByRole("button", { name: /reset password/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid or has expired/i)).toBeInTheDocument();
    });
  });
});
