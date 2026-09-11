import React, { useState } from "react";
import { Form, Button, Alert } from "react-bootstrap";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { FaLock } from "react-icons/fa";
import { authAPI } from "../services/api";
import AuthLayout from "../components/AuthLayout";
import AuthField from "../components/AuthField";

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";

  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirm, setNewPasswordConfirm] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const linkIsMissingParams = !uid || !token;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (newPassword !== newPasswordConfirm) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);
    try {
      const response = await authAPI.confirmPasswordReset({
        uid,
        token,
        new_password: newPassword,
        new_password_confirm: newPasswordConfirm,
      });
      setMessage(response.message);
      setTimeout(() => navigate("/login"), 2500);
    } catch (err: any) {
      const apiData = err.response?.data;
      setError(
        apiData?.new_password?.[0] ||
          apiData?.non_field_errors?.[0] ||
          apiData?.detail ||
          "This reset link is invalid or has expired."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Choose a new password for your account."
      footer={<Link to="/login">Back to login</Link>}
    >
      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="danger">{error}</Alert>}
      {linkIsMissingParams && !message && (
        <Alert variant="danger">
          This link is missing required information. Please request a new one.
        </Alert>
      )}

      {!message && !linkIsMissingParams && (
        <Form onSubmit={handleSubmit}>
          <AuthField
            controlId="resetNewPassword"
            label="New Password"
            icon={<FaLock />}
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New Password"
            required
            autoComplete="new-password"
          />

          <AuthField
            controlId="resetNewPasswordConfirm"
            label="Confirm New Password"
            icon={<FaLock />}
            type="password"
            value={newPasswordConfirm}
            onChange={(e) => setNewPasswordConfirm(e.target.value)}
            placeholder="Confirm New Password"
            required
            autoComplete="new-password"
          />

          <Button type="submit" className="auth-submit-btn" disabled={isLoading}>
            {isLoading ? "Resetting..." : "Reset Password"}
          </Button>
        </Form>
      )}
    </AuthLayout>
  );
};

export default ResetPassword;
