import React, { useState, useEffect } from "react";
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
import { useAuth } from "../utils/AuthContext";
import { authAPI } from "../services/api";
import { FaUser, FaLock, FaSave } from "react-icons/fa";

const Profile: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [profileData, setProfileData] = useState({
    first_name: "",
    last_name: "",
    username: "",
    phone_number: "",
    date_of_birth: "",
    bio: "",
  });
  const [passwordData, setPasswordData] = useState({
    old_password: "",
    new_password: "",
    new_password_confirm: "",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || "",
        last_name: user.last_name || "",
        username: user.username || "",
        phone_number: user.phone_number || "",
        date_of_birth: user.date_of_birth || "",
        bio: user.bio || "",
      });
    }
  }, [user]);

  const handleProfileChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setIsLoading(true);

    try {
      const updatedUser = await authAPI.updateProfile(profileData);
      updateUser(updatedUser);
      setMessage("Profile updated successfully!");
    } catch (error: any) {
      setError("Failed to update profile. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (passwordData.new_password !== passwordData.new_password_confirm) {
      setError("New passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      await authAPI.changePassword(passwordData);
      setPasswordData({
        old_password: "",
        new_password: "",
        new_password_confirm: "",
      });
      setMessage("Password changed successfully!");
    } catch (error: any) {
      setError(
        error.response?.data?.old_password?.[0] || "Failed to change password"
      );
    } finally {
      setIsLoading(false);
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

      {message && <Alert variant="success">{message}</Alert>}
      {error && <Alert variant="danger">{error}</Alert>}

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
                            value={profileData.first_name}
                            onChange={handleProfileChange}
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
                            value={profileData.last_name}
                            onChange={handleProfileChange}
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
                            value={profileData.username}
                            onChange={handleProfileChange}
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
                            value={profileData.phone_number}
                            onChange={handleProfileChange}
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
                        value={profileData.date_of_birth}
                        onChange={handleProfileChange}
                      />
                    </Form.Group>

                    <Form.Group className="mb-3">
                      <Form.Label>Bio</Form.Label>
                      <Form.Control
                        as="textarea"
                        rows={3}
                        name="bio"
                        value={profileData.bio}
                        onChange={handleProfileChange}
                        placeholder="Tell us about yourself..."
                      />
                    </Form.Group>

                    <Button
                      variant="primary"
                      type="submit"
                      disabled={isLoading}
                    >
                      <FaSave className="me-2" />
                      {isLoading ? "Saving..." : "Save Changes"}
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
                        value={passwordData.old_password}
                        onChange={handlePasswordChange}
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
                            value={passwordData.new_password}
                            onChange={handlePasswordChange}
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
                            value={passwordData.new_password_confirm}
                            onChange={handlePasswordChange}
                            required
                          />
                        </Form.Group>
                      </Col>
                    </Row>

                    <Button
                      variant="primary"
                      type="submit"
                      disabled={isLoading}
                    >
                      <FaLock className="me-2" />
                      {isLoading ? "Changing..." : "Change Password"}
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
