import React, { useEffect, useMemo, useState } from "react";
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
  Form,
  InputGroup,
  Spinner,
} from "react-bootstrap";
import { FaUserShield, FaUsers, FaEye, FaSearch } from "react-icons/fa";
import { authAPI } from "../services/api";
import { useAuth } from "../utils/AuthContext";
import { User, UserStats } from "../types";

type BadgeVariant =
  "primary" | "secondary" | "success" | "danger" | "warning" | "info" | "light" | "dark";

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

const ROLE_OPTIONS: User["role"][] = ["user", "moderator", "admin"];

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
            <strong>Role:</strong>{" "}
            <Badge bg={ROLE_BADGE_VARIANTS[user.role] ?? "secondary"}>
              {user.role.toUpperCase()}
            </Badge>
          </p>
          <p className="mb-2">
            <strong>Account Status:</strong> {user.is_active ? "Active" : "Deactivated"}
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

const PAGE_SIZE = 20;

const AdminPanel: React.FC = () => {
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState<User[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [stats, setStats] = useState<UserStats | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isTableLoading, setIsTableLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [pendingActionUserId, setPendingActionUserId] = useState<number | null>(null);

  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<User["role"] | "">("");
  const [activeFilter, setActiveFilter] = useState<"true" | "false" | "">("");

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(totalCount / PAGE_SIZE)),
    [totalCount]
  );

  useEffect(() => {
    authAPI
      .getUserStats()
      .then(setStats)
      .catch(() => setErrorMessage("Failed to load statistics"));
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setPage(1);
      setSearch(searchInput.trim());
    }, 400);
    return () => clearTimeout(timeoutId);
  }, [searchInput]);

  useEffect(() => {
    let cancelled = false;
    setIsTableLoading(true);

    authAPI
      .getAllUsers({ page, search, role: roleFilter, is_active: activeFilter })
      .then((data) => {
        if (cancelled) return;
        setUsers(data.results);
        setTotalCount(data.count);
      })
      .catch(() => {
        if (!cancelled) setErrorMessage("Failed to load users");
      })
      .finally(() => {
        if (!cancelled) {
          setIsTableLoading(false);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [page, search, roleFilter, activeFilter]);

  const applyUserUpdate = (userId: number, updatedFields: Partial<User>) => {
    setUsers((current) =>
      current.map((u) => (u.id === userId ? { ...u, ...updatedFields } : u))
    );
  };

  const handleRoleChange = async (targetUser: User, role: User["role"]) => {
    setActionError("");
    setPendingActionUserId(targetUser.id);
    try {
      const updated = await authAPI.updateUser(targetUser.id, { role });
      applyUserUpdate(targetUser.id, { role: updated.role });
    } catch {
      setActionError(`Failed to update role for ${targetUser.email}`);
    } finally {
      setPendingActionUserId(null);
    }
  };

  const handleToggleActive = async (targetUser: User) => {
    setActionError("");
    setPendingActionUserId(targetUser.id);
    try {
      const updated = await authAPI.updateUser(targetUser.id, {
        is_active: !targetUser.is_active,
      });
      applyUserUpdate(targetUser.id, { is_active: updated.is_active });
    } catch {
      setActionError(`Failed to update status for ${targetUser.email}`);
    } finally {
      setPendingActionUserId(null);
    }
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

      {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}
      {actionError && (
        <Alert variant="danger" dismissible onClose={() => setActionError("")}>
          {actionError}
        </Alert>
      )}

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
            <Card.Body>
              <Row className="mb-3 g-2">
                <Col md={5}>
                  <InputGroup>
                    <InputGroup.Text>
                      <FaSearch />
                    </InputGroup.Text>
                    <Form.Control
                      type="search"
                      placeholder="Search by name, username, or email"
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      aria-label="Search users"
                    />
                  </InputGroup>
                </Col>
                <Col md={3}>
                  <Form.Select
                    aria-label="Filter by role"
                    value={roleFilter}
                    onChange={(e) => {
                      setPage(1);
                      setRoleFilter(e.target.value as User["role"] | "");
                    }}
                  >
                    <option value="">All roles</option>
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {role.charAt(0).toUpperCase() + role.slice(1)}
                      </option>
                    ))}
                  </Form.Select>
                </Col>
                <Col md={4}>
                  <Form.Select
                    aria-label="Filter by status"
                    value={activeFilter}
                    onChange={(e) => {
                      setPage(1);
                      setActiveFilter(e.target.value as "true" | "false" | "");
                    }}
                  >
                    <option value="">All statuses</option>
                    <option value="true">Active only</option>
                    <option value="false">Deactivated only</option>
                  </Form.Select>
                </Col>
              </Row>
            </Card.Body>
            <Card.Body className="p-0 position-relative">
              {isTableLoading && (
                <div
                  className="position-absolute top-0 start-0 w-100 h-100 d-flex justify-content-center align-items-center"
                  style={{ background: "rgba(255,255,255,0.6)", zIndex: 1 }}
                >
                  <Spinner animation="border" size="sm" />
                </div>
              )}
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
                      <th>Email Verified</th>
                      <th>Joined</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((rowUser) => {
                      const isSelf = rowUser.id === currentUser?.id;
                      const isBusy = pendingActionUserId === rowUser.id;
                      return (
                        <tr key={rowUser.id}>
                          <td>
                            <div>
                              <strong>{rowUser.full_name}</strong>
                              <br />
                              <small className="text-muted">@{rowUser.username}</small>
                            </div>
                          </td>
                          <td>{rowUser.email}</td>
                          <td style={{ minWidth: 140 }}>
                            <Form.Select
                              size="sm"
                              value={rowUser.role}
                              disabled={isSelf || isBusy}
                              aria-label={`Role for ${rowUser.email}`}
                              onChange={(e) =>
                                handleRoleChange(rowUser, e.target.value as User["role"])
                              }
                            >
                              {ROLE_OPTIONS.map((role) => (
                                <option key={role} value={role}>
                                  {role.charAt(0).toUpperCase() + role.slice(1)}
                                </option>
                              ))}
                            </Form.Select>
                          </td>
                          <td>
                            <Badge bg={rowUser.is_active ? "success" : "secondary"}>
                              {rowUser.is_active ? "Active" : "Deactivated"}
                            </Badge>
                          </td>
                          <td>
                            <Badge bg={rowUser.is_email_verified ? "success" : "warning"}>
                              {rowUser.is_email_verified ? "Verified" : "Unverified"}
                            </Badge>
                          </td>
                          <td>{formatDate(rowUser.created_at)}</td>
                          <td>
                            <div className="d-flex gap-2">
                              <Button
                                variant="outline-primary"
                                size="sm"
                                onClick={() => setSelectedUser(rowUser)}
                              >
                                <FaEye className="me-1" />
                                View
                              </Button>
                              <Button
                                variant={
                                  rowUser.is_active ? "outline-danger" : "outline-success"
                                }
                                size="sm"
                                disabled={isSelf || isBusy}
                                onClick={() => handleToggleActive(rowUser)}
                                title={
                                  isSelf
                                    ? "You can't deactivate your own account"
                                    : undefined
                                }
                              >
                                {isBusy ? (
                                  <Spinner animation="border" size="sm" />
                                ) : rowUser.is_active ? (
                                  "Deactivate"
                                ) : (
                                  "Activate"
                                )}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              )}
            </Card.Body>
            <Card.Footer className="d-flex justify-content-between align-items-center">
              <small className="text-muted">
                {totalCount === 0
                  ? "No results"
                  : `Page ${page} of ${totalPages} (${totalCount} total)`}
              </small>
              <div className="d-flex gap-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next
                </Button>
              </div>
            </Card.Footer>
          </Card>
        </Col>
      </Row>

      <UserDetailsModal user={selectedUser} onClose={() => setSelectedUser(null)} />
    </Container>
  );
};

export default AdminPanel;
