import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import VerifyEmail from "./VerifyEmail";
import { authAPI } from "../services/api";

jest.mock("../services/api", () => ({
  authAPI: {
    confirmEmailVerification: jest.fn(),
  },
}));

const mockedAuthAPI = authAPI as jest.Mocked<typeof authAPI>;

const renderPage = (path = "/verify-email?uid=MQ&token=abc123") =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/dashboard" element={<div>Dashboard page</div>} />
      </Routes>
    </MemoryRouter>
  );

beforeEach(() => {
  jest.clearAllMocks();
});

describe("VerifyEmail", () => {
  it("confirms verification automatically using the uid/token from the URL", async () => {
    mockedAuthAPI.confirmEmailVerification.mockResolvedValue({
      message: "Email verified successfully.",
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/email verified successfully/i)).toBeInTheDocument();
    });
    expect(mockedAuthAPI.confirmEmailVerification).toHaveBeenCalledWith({
      uid: "MQ",
      token: "abc123",
    });
  });

  it("shows an error state for an invalid link", async () => {
    mockedAuthAPI.confirmEmailVerification.mockRejectedValue({
      response: { data: {} },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/invalid or has expired/i)).toBeInTheDocument();
    });
  });

  it("shows an error without calling the API when the link is missing params", async () => {
    renderPage("/verify-email");

    await waitFor(() => {
      expect(screen.getByText(/missing required information/i)).toBeInTheDocument();
    });
    expect(mockedAuthAPI.confirmEmailVerification).not.toHaveBeenCalled();
  });
});
