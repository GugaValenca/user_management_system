import React, { useState } from "react";
import { Form, Button, Alert } from "react-bootstrap";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../utils/AuthContext";
import { FaUser, FaEnvelope, FaLock } from "react-icons/fa";
import AuthLayout from "../components/AuthLayout";
import AuthField from "../components/AuthField";

const Register: React.FC = () => {
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (formData.password !== formData.password_confirm) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await register(formData);
      navigate("/dashboard");
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.email?.[0] ||
        error.response?.data?.username?.[0] ||
        error.response?.data?.detail ||
        "Registration failed. Please try again.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create Account"
      subtitle="Join us today! Please fill in your information."
      wide
      footer={
        <>
          Already have an account? <Link to="/login">Sign in</Link>
        </>
      }
    >
      {error && <Alert variant="danger">{error}</Alert>}

      <Form onSubmit={handleSubmit}>
        <div className="auth-field-pair">
          <AuthField
            controlId="registerFirstName"
            label="First Name"
            icon={<FaUser />}
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            placeholder="First Name"
            required
            autoComplete="given-name"
          />
          <AuthField
            controlId="registerLastName"
            label="Last Name"
            icon={<FaUser />}
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            placeholder="Last Name"
            required
            autoComplete="family-name"
          />
        </div>

        <AuthField
          controlId="registerUsername"
          label="Username"
          icon={<FaUser />}
          name="username"
          value={formData.username}
          onChange={handleChange}
          placeholder="Username"
          required
          autoComplete="username"
        />

        <AuthField
          controlId="registerEmail"
          label="Email"
          icon={<FaEnvelope />}
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="Email"
          required
          autoComplete="email"
        />

        <div className="auth-field-pair">
          <AuthField
            controlId="registerPassword"
            label="Password"
            icon={<FaLock />}
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Password"
            required
            autoComplete="new-password"
          />
          <AuthField
            controlId="registerPasswordConfirm"
            label="Confirm Password"
            icon={<FaLock />}
            type="password"
            name="password_confirm"
            value={formData.password_confirm}
            onChange={handleChange}
            placeholder="Confirm Password"
            required
            autoComplete="new-password"
          />
        </div>

        <Button type="submit" className="auth-submit-btn" disabled={isLoading}>
          {isLoading ? "Creating Account..." : "Create Account"}
        </Button>
      </Form>
    </AuthLayout>
  );
};

export default Register;
