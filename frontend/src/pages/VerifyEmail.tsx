import React, { useEffect, useRef, useState } from "react";
import { Container, Row, Col, Card, Alert, Spinner } from "react-bootstrap";
import { Link, useSearchParams } from "react-router-dom";
import { authAPI } from "../services/api";

type VerificationState = "verifying" | "success" | "error";

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const uid = searchParams.get("uid") || "";
  const token = searchParams.get("token") || "";

  const [state, setState] = useState<VerificationState>("verifying");
  const [message, setMessage] = useState("");
  const hasRequested = useRef(false);

  useEffect(() => {
    if (hasRequested.current) return;
    hasRequested.current = true;

    if (!uid || !token) {
      setState("error");
      setMessage("This link is missing required information.");
      return;
    }

    authAPI
      .confirmEmailVerification({ uid, token })
      .then((response) => {
        setState("success");
        setMessage(response.message);
      })
      .catch((err) => {
        setState("error");
        setMessage(
          err.response?.data?.non_field_errors?.[0] ||
            "This verification link is invalid or has expired."
        );
      });
  }, [uid, token]);

  return (
    <Container className="mt-5">
      <Row className="justify-content-center">
        <Col md={6} lg={4}>
          <Card>
            <Card.Body className="p-4 text-center">
              <h2 className="mb-4">Email Verification</h2>

              {state === "verifying" && (
                <>
                  <Spinner animation="border" className="mb-3" />
                  <p className="text-muted">Verifying your email...</p>
                </>
              )}

              {state === "success" && <Alert variant="success">{message}</Alert>}
              {state === "error" && <Alert variant="danger">{message}</Alert>}

              {state !== "verifying" && (
                <Link to="/dashboard" className="btn btn-primary">
                  Go to Dashboard
                </Link>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default VerifyEmail;
