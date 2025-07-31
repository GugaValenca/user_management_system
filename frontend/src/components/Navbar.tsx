import React from "react";
import { Navbar, Nav, NavDropdown, Container } from "react-bootstrap";
import { useAuth } from "../utils/AuthContext";
import { useNavigate } from "react-router-dom";
import { FaUser, FaSignOutAlt, FaCog } from "react-icons/fa";

const Navigation: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand href="/dashboard">User Management System</Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          {isAuthenticated && (
            <>
              <Nav className="me-auto">
                <Nav.Link href="/dashboard">Dashboard</Nav.Link>
                <Nav.Link href="/profile">Profile</Nav.Link>
                <Nav.Link href="/activity">Activity Logs</Nav.Link>
                {user?.role === "admin" && (
                  <Nav.Link href="/admin">Admin Panel</Nav.Link>
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
                  <NavDropdown.Item href="/profile">
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
