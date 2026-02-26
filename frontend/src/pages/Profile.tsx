import React, { useEffect, useState } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Form,
  Button,
  Alert,
  Tab,
  Tabs,
} from "react-bootstrap";
import { FaUser, FaLock, FaSave } from "react-icons/fa";
import { authAPI } from "../services/api";
import { useAuth } from "../utils/AuthContext";
import { User } from "../types";

type ProfileFormData = Pick<
  User,
  "first_name" | "last_name" | "username" | "phone_number" | "date_of_birth" | "bio"
>;

type PasswordFormData = {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
};

const EMPTY_PROFILE_FORM: ProfileFormData = {
  first_name: "",
  last_name: "",
  username: "",
  phone_number: "",
  date_of_birth: "",
  bio: "",
};

const EMPTY_PASSWORD_FORM: PasswordFormData = {
  old_password: "",
  new_password: "",
  new_password_confirm: "",
};

const Profile: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [profileForm, setProfileForm] = useState<ProfileFormData>(EMPTY_PROFILE_FORM);
  const [passwordForm, setPasswordForm] = useState<PasswordFormData>(EMPTY_PASSWORD_FORM);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;

    setProfileForm({
      first_name: user.first_name || "",
      last_name: user.last_name || "",
      username: user.username || "",
      phone_number: user.phone_number || "",
      date_of_birth: user.date_of_birth || "",
      bio: user.bio || "",
    });
  }, [user]);

  const resetFeedback = () => {
    setErrorMessage("");
    setSuccessMessage("");
  };

  const updateProfileField = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setProfileForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const updatePasswordField = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setPasswordForm((current) => ({
      ...current,
      [name]: value,
    }));
  };

  const handleProfileSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    resetFeedback();
    setIsSubmitting(true);

    try {
      const updatedUser = await authAPI.updateProfile(profileForm);
      updateUser(updatedUser);
      setSuccessMessage("Profile updated successfully!");
    } catch {
      setErrorMessage("Failed to update profile. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePasswordSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    resetFeedback();

    if (passwordForm.new_password !== passwordForm.new_password_confirm) {
      setErrorMessage("New passwords do not match");
      return;
    }

    setIsSubmitting(true);

    try {
      await authAPI.changePassword(passwordForm);
      setPasswordForm(EMPTY_PASSWORD_FORM);
      setSuccessMessage("Password changed successfully!");
    } catch (error: unknown) {
      const maybeAxiosError = error as {
        response?: { data?: { old_password?: string[] } };
      };
      setErrorMessage(
        maybeAxiosError.response?.data?.old_password?.[0] ||
          "Failed to change password"
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Container>
      <Row className="mb-4">
        <Col>
          <h1>Profile Settings</h1>
          <p className="text-muted">
            Manage your account information and security settings
          </p>
        </Col>
      </Row>

      {successMessage && <Alert variant="success">{successMessage}</Alert>}
      {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}

      <Row>
        <Col>
          <Card>
            <Card.Body>
              <Tabs defaultActiveKey="profile" id="profile-tabs">
                <Tab
                  eventKey="profile"
                  title={
                    <>
                      <FaUser className="me-2" />
                      Profile Information
                    </>
                  }
                >
                  <Form onSubmit={handleProfileSubmit} className="mt-3">
                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>First Name</Form.Label>
                          <Form.Control
                            type="text"
                            name="first_name"
                            value={profileForm.first_name}
                            onChange={updateProfileField}
                            required
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Last Name</Form.Label>
                          <Form.Control
                            type="text"
                            name="last_name"
                            value={profileForm.last_name}
                            onChange={updateProfileField}
                            required
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Username</Form.Label>
                          <Form.Control
                            type="text"
                            name="username"
                            value={profileForm.username}
                            onChange={updateProfileField}
                            required
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Phone Number</Form.Label>
                          <Form.Control
                            type="tel"
                            name="phone_number"
                            value={profileForm.phone_number || ""}
                            onChange={updateProfileField}
                            placeholder="(555) 123-4567"
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Form.Group className="mb-3">
                      <Form.Label>Date of Birth</Form.Label>
                      <Form.Control
                        type="date"
                        name="date_of_birth"
                        value={profileForm.date_of_birth || ""}
                        onChange={updateProfileField}
                      />
                    </Form.Group>

                    <Form.Group className="mb-3">
                      <Form.Label>Bio</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        name="bio"
                        value={profileForm.bio || ""}
                        onChange={updateProfileField}
                        placeholder="Tell us about yourself..."
                      />
                    </Form.Group>

                    <Button variant="primary" type="submit" disabled={isSubmitting}>
                      <FaSave className="me-2" />
                      {isSubmitting ? "Saving..." : "Save Changes"}
                    </Button>
                  </Form>
                </Tab>

                <Tab
                  eventKey="password"
                  title={
                    <>
                      <FaLock className="me-2" />
                      Change Password
                    </>
                  }
                >
                  <Form onSubmit={handlePasswordSubmit} className="mt-3">
                    <Form.Group className="mb-3">
                      <Form.Label>Current Password</Form.Label>
                      <Form.Control
                        type="password"
                        name="old_password"
                        value={passwordForm.old_password}
                        onChange={updatePasswordField}
                        required
                      />
                    </Form.Group>

                    <Row>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>New Password</Form.Label>
                          <Form.Control
                            type="password"
                            name="new_password"
                            value={passwordForm.new_password}
                            onChange={updatePasswordField}
                            required
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group className="mb-3">
                          <Form.Label>Confirm New Password</Form.Label>
                          <Form.Control
                            type="password"
                            name="new_password_confirm"
                            value={passwordForm.new_password_confirm}
                            onChange={updatePasswordField}
                            required
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Button variant="primary" type="submit" disabled={isSubmitting}>
                      <FaLock className="me-2" />
                      {isSubmitting ? "Changing..." : "Change Password"}
                    </Button>
                  </Form>
                </Tab>
              </Tabs>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Profile;

