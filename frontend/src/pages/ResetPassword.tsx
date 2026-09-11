import React, { useState } from "react";
import { Container, Row, Col, Card, Form, Button, Alert } from "react-bootstrap";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { FaLock } from "react-icons/fa";
import { authAPI } from "../services/api";

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
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md={6} lg={4}>
          <Card>
            <Card.Body className="p-4">
              <div className="text-center mb-4">
                <h2>Reset Password</h2>
                <p className="text-muted">Choose a new password for your account.</p>
              </div>

              {message && <Alert variant="success">{message}</Alert>}
              {error && <Alert variant="danger">{error}</Alert>}
              {linkIsMissingParams && !message && (
                <Alert variant="danger">
                  This link is missing required information. Please request a new one.
                </Alert>
              )}

              {!message && !linkIsMissingParams && (
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3" controlId="resetNewPassword">
                    <Form.Label>
                      <FaLock className="me-2" />
                      New Password
                    </Form.Label>
                    <Form.Control
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      placeholder="Enter a new password"
                    />
                  </Form.Group>

                  <Form.Group className="mb-3" controlId="resetNewPasswordConfirm">
                    <Form.Label>
                      <FaLock className="me-2" />
                      Confirm New Password
                    </Form.Label>
                    <Form.Control
                      type="password"
                      value={newPasswordConfirm}
                      onChange={(e) => setNewPasswordConfirm(e.target.value)}
                      required
                      placeholder="Confirm your new password"
                    />
                  </Form.Group>

                  <Button
                    variant="primary"
                    type="submit"
                    className="w-100 mb-3"
                    disabled={isLoading}
                  >
                    {isLoading ? "Resetting..." : "Reset password"}
                  </Button>
                </Form>
              )}

              <div className="text-center">
                <Link to="/login" className="text-decoration-none">
                  Back to login
                </Link>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ResetPassword;
