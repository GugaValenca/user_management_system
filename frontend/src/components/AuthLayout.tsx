import React from "react";
import Logo from "./Logo";
import "./AuthLayout.css";

interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  wide?: boolean;
}

/**
 * Shared visual shell for every auth screen (login, register, forgot/reset
 * password, verify email) - a full-bleed branded page with the logo up
 * front, no nav bar competing for attention before the user is signed in.
 */
const AuthLayout: React.FC<AuthLayoutProps> = ({
  title,
  subtitle,
  children,
  footer,
  wide,
}) => (
  <div className="auth-page">
    <div className={`auth-card${wide ? " auth-card-wide" : ""}`}>
      <div className="auth-brand">
        <Logo size={64} />
        <span className="auth-brand-name">User Management</span>
      </div>
      <h1>{title}</h1>
      {subtitle && <p className="auth-subtitle">{subtitle}</p>}
      {children}
      {footer && <div className="auth-footer">{footer}</div>}
    </div>
  </div>
);

export default AuthLayout;
