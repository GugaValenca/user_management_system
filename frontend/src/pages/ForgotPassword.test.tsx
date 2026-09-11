import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import ForgotPassword from "./ForgotPassword";
import { authAPI } from "../services/api";

jest.mock("../services/api", () => ({
  authAPI: {
    requestPasswordReset: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

const renderPage = () =>
  render(
    <MemoryRouter>
      <ForgotPassword />
    </MemoryRouter>
  );

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ForgotPassword", () => {
  it("submits the email and shows the generic success message", async () => {
    mockedAuthAPI.requestPasswordReset.mockResolvedValue({
      message: "If an account exists for that email, a reset link has been sent.",
    });

    renderPage();
    userEvent.type(screen.getByLabelText(/email/i), "user@example.com");
    userEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByText(/reset link has been sent/i)).toBeInTheDocument();
    });
    expect(mockedAuthAPI.requestPasswordReset).toHaveBeenCalledWith("user@example.com");
  });

  it("shows an error message when the request fails", async () => {
    mockedAuthAPI.requestPasswordReset.mockRejectedValue(new Error("network error"));

    renderPage();
    userEvent.type(screen.getByLabelText(/email/i), "user@example.com");
    userEvent.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
  });
});
