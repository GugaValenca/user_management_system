import React from "react";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute";
import { useAuth } from "../utils/AuthContext";
import { User } from "../types";

jest.mock("../utils/AuthContext", () => ({
  useAuth: jest.fn(),
}));

const mockUseAuth = useAuth as jest.Mock;

const ADMIN_USER = { role: "admin" } as User;
const REGULAR_USER = { role: "user" } as User;

const renderProtectedRoute = (requireAdmin = false) =>
  render(
    <MemoryRouter initialEntries={["/protected"]}>
      <Routes>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/dashboard" element={<div>Dashboard page</div>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute requireAdmin={requireAdmin}>
              <div>Protected content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>
  );

describe("ProtectedRoute", () => {
  it("shows a loading state while auth is being resolved", () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null, isLoading: true });

    renderProtectedRoute();

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("redirects to login when the user is not authenticated", () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null, isLoading: false });

    renderProtectedRoute();

    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders the protected content for an authenticated user", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: REGULAR_USER,
      isLoading: false,
    });

    renderProtectedRoute();

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects a non-admin user away from an admin-only route", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: REGULAR_USER,
      isLoading: false,
    });

    renderProtectedRoute(true);

    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
  });

  it("renders admin-only content for an admin user", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: ADMIN_USER,
      isLoading: false,
    });

    renderProtectedRoute(true);

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
