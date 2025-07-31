import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Table,
  Badge,
  Alert,
  Button,
} from "react-bootstrap";
import { authAPI } from "../services/api";
import { User, UserStats } from "../types";
import { FaUserShield, FaUsers, FaEye } from "react-icons/fa";

const AdminPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [usersData, statsData] = await Promise.all([
          authAPI.getAllUsers(),
          authAPI.getUserStats(),
        ]);
        setUsers(usersData);
        setStats(statsData);
      } catch (error: any) {
        setError("Failed to load admin data");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const getRoleBadge = (role: string) => {
    const badgeMap: { [key: string]: string } = {
      admin: "danger",
      moderator: "warning",
      user: "primary",
    };
    return badgeMap[role] || "secondary";
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <Container>
        <div className="d-flex justify-content-center p-5">
          <div>Loading admin panel...</div>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <Row className="mb-4">
        <Col>
          <h1>
            <FaUserShield className="me-2" />
            Admin Panel
          </h1>
          <p className="text-muted">Manage users and view system statistics</p>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      {stats && (
        <Row className="mb-4">
          <Col md={3} className="mb-3">
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-primary">{stats.total_users}</h3>
                <p className="text-muted mb-0">Total Users</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-success">{stats.active_users}</h3>
                <p className="text-muted mb-0">Active Users</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-warning">{stats.admin_users}</h3>
                <p className="text-muted mb-0">Admin Users</p>
              </Card.Body>
            </Card>
          </Col>
          <Col md={3} className="mb-3">
            <Card className="text-center">
              <Card.Body>
                <h3 className="text-danger">{stats.inactive_users}</h3>
                <p className="text-muted mb-0">Inactive Users</p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">
                <FaUsers className="me-2" />
                User Management
              </h5>
            </Card.Header>
            <Card.Body className="p-0">
              {users.length === 0 ? (
                <div className="text-center p-4">
                  <p className="text-muted">No users found</p>
                </div>
              ) : (
                <Table responsive hover className="mb-0">
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Status</th>
                      <th>Joined</th>
                      <th>Last Login</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>
                          <div>
                            <strong>{user.full_name}</strong>
                            <br />
                            <small className="text-muted">
                              @{user.username}
                            </small>
                          </div>
                        </td>
                        <td>{user.email}</td>
                        <td>
                          <Badge bg={getRoleBadge(user.role)}>
                            {user.role.toUpperCase()}
                          </Badge>
                        </td>
                        <td>
                          <Badge
                            bg={user.is_email_verified ? "success" : "warning"}
                          >
                            {user.is_email_verified ? "Verified" : "Unverified"}
                          </Badge>
                        </td>
                        <td>{formatDate(user.created_at)}</td>
                        <td>
                          {user.last_login
                            ? formatDate(user.last_login)
                            : "Never"}
                        </td>
                        <td>
                          <Button variant="outline-primary" size="sm">
                            <FaEye className="me-1" />
                            View
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default AdminPanel;
