import React, { useEffect, useRef, useState } from "react";
import { Alert, Spinner } from "react-bootstrap";
import { Link, useSearchParams } from "react-router-dom";
import { authAPI } from "../services/api";
import AuthLayout from "../components/AuthLayout";

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
    <AuthLayout
      title="Email Verification"
      footer={<Link to="/dashboard">Go to Dashboard</Link>}
    >
      <div className="text-center">
        {state === "verifying" && (
          <>
            <Spinner animation="border" className="mb-3" style={{ color: "#6ea8ff" }} />
            <p className="auth-subtitle mb-0">Verifying your email...</p>
          </>
        )}

        {state === "success" && <Alert variant="success">{message}</Alert>}
        {state === "error" && <Alert variant="danger">{message}</Alert>}
      </div>
    </AuthLayout>
  );
};

export default VerifyEmail;
