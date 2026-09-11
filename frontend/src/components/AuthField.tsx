import React, { useState } from "react";
import { Form } from "react-bootstrap";
import { FaEye, FaEyeSlash } from "react-icons/fa";

interface AuthFieldProps {
  controlId: string;
  label: string;
  icon: React.ReactNode;
  type?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder: string;
  required?: boolean;
  name?: string;
  autoComplete?: string;
}

/**
 * One underlined, icon-prefixed input matching the auth screens' visual
 * language. The label stays in the DOM for screen readers (and so
 * getByLabelText keeps working in tests) but is visually hidden - the
 * design leans on the icon + placeholder instead of a visible label.
 *
 * type="password" fields get a show/hide toggle for free, so someone can
 * check what they actually typed before submitting.
 */
const AuthField: React.FC<AuthFieldProps> = ({
  controlId,
  label,
  icon,
  type = "text",
  value,
  onChange,
  placeholder,
  required,
  name,
  autoComplete,
}) => {
  const [isRevealed, setIsRevealed] = useState(false);
  const isPassword = type === "password";
  const effectiveType = isPassword && isRevealed ? "text" : type;

  return (
    <Form.Group className="auth-field" controlId={controlId}>
      <Form.Label className="visually-hidden">{label}</Form.Label>
      <div className="auth-field-row">
        <span className="auth-field-icon">{icon}</span>
        <Form.Control
          className="auth-input"
          type={effectiveType}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          autoComplete={autoComplete}
        />
        {isPassword && (
          <button
            type="button"
            className="auth-field-toggle"
            onClick={() => setIsRevealed((current) => !current)}
            aria-label={
              isRevealed ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`
            }
          >
            {isRevealed ? <FaEyeSlash /> : <FaEye />}
          </button>
        )}
      </div>
    </Form.Group>
  );
};

export default AuthField;
