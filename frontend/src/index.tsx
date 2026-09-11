import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
// Bootstrap first, then our own overrides, so index.css's theme tokens
// (which redeclare Bootstrap's own CSS variables) win the cascade.
import "bootstrap/dist/css/bootstrap.min.css";
import "./index.css";

const root = ReactDOM.createRoot(document.getElementById("root") as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
