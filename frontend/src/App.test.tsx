import React from "react";
import { render, screen } from "@testing-library/react";
import App from "./App";

beforeEach(() => {
  localStorage.clear();
});

test("redirects an unauthenticated visitor to the login page", async () => {
  render(<App />);

  expect(await screen.findByRole("heading", { name: /login/i })).toBeInTheDocument();
});
