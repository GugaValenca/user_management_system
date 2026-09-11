import React, { useState } from "react";
import { Form, Button, Alert } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../utils/AuthContext";
import { FaEnvelope, FaLock } from "react-icons/fa";
import AuthLayout from "../components/AuthLayout";
import AuthField from "../components/AuthField";

const Login: React.FC = () => {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      await login({ identifier: identifier.trim(), password });
      navigate("/dashboard");
    } catch (error: any) {
      const apiData = error.response?.data;
      setError(
        apiData?.detail ||
          apiData?.non_field_errors?.[0] ||
          apiData?.error ||
          "Login failed. Please check your credentials and try again."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Login"
      subtitle="Welcome back! Please sign in to your account."
      footer={
        <>
          Don't have an account? <Link to="/register">Sign up</Link>
        </>
      }
    >
      {error && <Alert variant="danger">{error}</Alert>}

      <Form onSubmit={handleSubmit}>
        <AuthField
          controlId="loginIdentifier"
          label="Email or Username"
          icon={<FaEnvelope />}
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          placeholder="Email or Username"
          required
          autoComplete="username"
        />

        <AuthField
          controlId="loginPassword"
          label="Password"
          icon={<FaLock />}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          required
          autoComplete="current-password"
        />

        <div className="auth-row-between">
          <span />
          <Link to="/forgot-password">Forgot Password?</Link>
        </div>

        <Button type="submit" className="auth-submit-btn" disabled={isLoading}>
          {isLoading ? "Signing in..." : "Login"}
        </Button>
      </Form>
    </AuthLayout>
  );
};

export default Login;
