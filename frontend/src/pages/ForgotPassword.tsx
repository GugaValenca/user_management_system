import React, { useState } from "react";
import { Form, Button, Alert } from "react-bootstrap";
import { Link } from "react-router-dom";
import { FaEnvelope } from "react-icons/fa";
import { authAPI } from "../services/api";
import AuthLayout from "../components/AuthLayout";
import AuthField from "../components/AuthField";

const ForgotPassword: React.FC = () => {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setIsLoading(true);

    try {
      const response = await authAPI.requestPasswordReset(email.trim());
      setMessage(response.message);
    } catch (err: any) {
      setError(
        err.response?.data?.email?.[0] || "Something went wrong. Please try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Forgot Password"
      subtitle="Enter your email and we'll send you a link to reset your password."
      footer={<Link to="/login">Back to login</Link>}
    >
      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="danger">{error}</Alert>}

      {!message && (
        <Form onSubmit={handleSubmit}>
          <AuthField
            controlId="forgotPasswordEmail"
            label="Email"
            icon={<FaEnvelope />}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            required
            autoComplete="email"
          />

          <Button type="submit" className="auth-submit-btn" disabled={isLoading}>
            {isLoading ? "Sending..." : "Send Reset Link"}
          </Button>
        </Form>
      )}
    </AuthLayout>
  );
};

export default ForgotPassword;
