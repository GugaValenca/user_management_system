import React, { useEffect, useState } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Table,
  Badge,
  Alert,
  Button,
  Modal,
} from "react-bootstrap";
import { FaUserShield, FaUsers, FaEye } from "react-icons/fa";
import { authAPI } from "../services/api";
import { User, UserStats } from "../types";

type BadgeVariant =
  | "primary"
  | "secondary"
  | "success"
  | "danger"
  | "warning"
  | "info"
  | "light"
  | "dark";

interface AdminStatsCardConfig {
  key: keyof UserStats;
  label: string;
  colorClass: string;
}

const ROLE_BADGE_VARIANTS: Record<User["role"], BadgeVariant> = {
  admin: "danger",
  moderator: "warning",
  user: "primary",
};

const ADMIN_STATS_CARDS: AdminStatsCardConfig[] = [
  { key: "total_users", label: "Total Users", colorClass: "text-primary" },
  { key: "active_users", label: "Active Users", colorClass: "text-success" },
  { key: "admin_users", label: "Admin Users", colorClass: "text-warning" },
  { key: "inactive_users", label: "Inactive Users", colorClass: "text-danger" },
];

const formatDate = (dateString?: string): string =>
  dateString ? new Date(dateString).toLocaleDateString() : "Never";

const formatDateTime = (dateString?: string): string =>
  dateString ? new Date(dateString).toLocaleString() : "Never";

const UserDetailsModal: React.FC<{
  user: User | null;
  onClose: () => void;
}> = ({ user, onClose }) => (
  <Modal show={!!user} onHide={onClose} centered>
    <Modal.Header closeButton>
      <Modal.Title>User Details</Modal.Title>
    </Modal.Header>
    <Modal.Body>
      {user && (
        <div>
          <p className="mb-2">
            <strong>Name:</strong> {user.full_name}
          </p>
          <p className="mb-2">
            <strong>Username:</strong> @{user.username}
          </p>
          <p className="mb-2">
            <strong>Email:</strong> {user.email}
          </p>
          <p className="mb-2">
            <strong>Role:</strong> {user.role}
          </p>
          <p className="mb-2">
            <strong>Email Verified:</strong> {user.is_email_verified ? "Yes" : "No"}
          </p>
          <p className="mb-2">
            <strong>Joined:</strong> {formatDateTime(user.created_at)}
          </p>
          <p className="mb-2">
            <strong>Last Login:</strong> {formatDateTime(user.last_login)}
          </p>
          <p className="mb-0">
            <strong>Bio:</strong> {user.bio || "N/A"}
          </p>
        </div>
      )}
    </Modal.Body>
    <Modal.Footer>
      <Button variant="secondary" onClick={onClose}>
        Close
      </Button>
    </Modal.Footer>
  </Modal>
);

const AdminPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  useEffect(() => {
    const loadAdminData = async () => {
      try {
        const [allUsers, userStats] = await Promise.all([
          authAPI.getAllUsers(),
          authAPI.getUserStats(),
        ]);
        setUsers(allUsers);
        setStats(userStats);
      } catch {
        setErrorMessage("Failed to load admin data");
      } finally {
        setIsLoading(false);
      }
    };

    loadAdminData();
  }, []);

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

      {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}

      {stats && (
        <Row className="mb-4">
          {ADMIN_STATS_CARDS.map(({ key, label, colorClass }) => (
            <Col md={3} className="mb-3" key={key}>
              <Card className="text-center">
                <Card.Body>
                  <h3 className={colorClass}>{stats[key]}</h3>
                  <p className="text-muted mb-0">{label}</p>
                </Card.Body>
              </Card>
            </Col>
          ))}
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
                            <small className="text-muted">@{user.username}</small>
                          </div>
                        </td>
                        <td>{user.email}</td>
                        <td>
                          <Badge bg={ROLE_BADGE_VARIANTS[user.role] ?? "secondary"}>
                            {user.role.toUpperCase()}
                          </Badge>
                        </td>
                        <td>
                          <Badge bg={user.is_email_verified ? "success" : "warning"}>
                            {user.is_email_verified ? "Verified" : "Unverified"}
                          </Badge>
                        </td>
                        <td>{formatDate(user.created_at)}</td>
                        <td>{formatDate(user.last_login)}</td>
                        <td>
                          <Button
                            variant="outline-primary"
                            size="sm"
                            onClick={() => setSelectedUser(user)}
                          >
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

      <UserDetailsModal
        user={selectedUser}
        onClose={() => setSelectedUser(null)}
      />
    </Container>
  );
};

export default AdminPanel;

