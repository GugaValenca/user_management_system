import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { authAPI } from "./services/api";

jest.mock("./services/api", () => ({
  authAPI: {
    // AuthProvider always calls this on mount to try to restore a session
    // from the httpOnly refresh cookie - rejecting it here is what a real
    // first visit with no cookie looks like, and avoids the app actually
    // trying to reach the network during this test.
    refreshSession: jest.fn().mockRejectedValue(new Error("no session")),
  },
}));

beforeEach(() => {
  jest.clearAllMocks();
  (authAPI.refreshSession as jest.Mock).mockRejectedValue(new Error("no session"));
});

test("redirects an unauthenticated visitor to the login page", async () => {
  render(<App />);

  expect(await screen.findByRole("heading", { name: /login/i })).toBeInTheDocument();
});
