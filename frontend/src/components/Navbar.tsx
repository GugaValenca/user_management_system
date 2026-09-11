import React from "react";
import { Navbar, Nav, NavDropdown, Container } from "react-bootstrap";
import { useAuth } from "../utils/AuthContext";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { FaUser, FaSignOutAlt, FaCog } from "react-icons/fa";
import Logo from "./Logo";

const AUTH_ROUTES = [
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/verify-email",
];

const Navigation: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  // The auth screens (login, register, ...) are full-bleed branded pages of
  // their own - a nav bar with nothing to navigate to (the user isn't signed
  // in yet) just eats into that layout for no benefit.
  if (AUTH_ROUTES.includes(location.pathname)) {
    return null;
  }

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand
          as={Link}
          to="/dashboard"
          className="d-flex align-items-center gap-2"
        >
          <Logo size={32} />
          User Management System
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          {isAuthenticated && (
            <>
              <Nav className="me-auto">
                <Nav.Link as={Link} to="/dashboard">
                  Dashboard
                </Nav.Link>
                <Nav.Link as={Link} to="/profile">
                  Profile
                </Nav.Link>
                <Nav.Link as={Link} to="/activity">
                  Activity Logs
                </Nav.Link>
                {user?.role === "admin" && (
                  <Nav.Link as={Link} to="/admin">
                    Admin Panel
                  </Nav.Link>
                )}
              </Nav>
              <Nav>
                <NavDropdown
                  title={
                    <span>
                      <FaUser className="me-2" />
                      {user?.full_name || user?.email}
                    </span>
                  }
                  id="user-dropdown"
                >
                  <NavDropdown.Item as={Link} to="/profile">
                    <FaCog className="me-2" />
                    Settings
                  </NavDropdown.Item>
                  <NavDropdown.Divider />
                  <NavDropdown.Item onClick={handleLogout}>
                    <FaSignOutAlt className="me-2" />
                    Logout
                  </NavDropdown.Item>
                </NavDropdown>
              </Nav>
            </>
          )}
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default Navigation;
