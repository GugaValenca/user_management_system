import React, { useState, useEffect } from "react";
import { Container, Row, Col, Card, Alert } from "react-bootstrap";
import { useAuth } from "../utils/AuthContext";
import { authAPI } from "../services/api";
import { UserStats } from "../types";
import {
  FaUsers,
  FaUserCheck,
  FaUserShield,
  FaUserTimes,
  FaUser,
} from "react-icons/fa";

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      if (user?.role === "admin") {
        try {
          const statsData = await authAPI.getUserStats();
          setStats(statsData);
        } catch (error: any) {
          setError("Failed to load statistics");
        }
      }
    };

    fetchStats();
  }, [user]);

  return (
    <Container>
      <Row className="mb-4">
        <Col>
          <h1>Dashboard</h1>
          <p className="text-muted">
            Welcome back, {user?.full_name || user?.email}!
          </p>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      <Row className="mb-4">
        <Col md={6} lg={3} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <FaUser className="text-primary" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="small text-muted">Role</div>
                  <div className="fw-bold text-capitalize">{user?.role}</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <FaUserCheck className="text-success" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="small text-muted">Email Status</div>
                  <div className="fw-bold">
                    {user?.is_email_verified ? "Verified" : "Unverified"}
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <FaUser className="text-info" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="small text-muted">Member Since</div>
                  <div className="fw-bold">
                    {user?.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center">
                <div className="flex-shrink-0">
                  <FaUser className="text-warning" size={24} />
                </div>
                <div className="flex-grow-1 ms-3">
                  <div className="small text-muted">Last Login</div>
                  <div className="fw-bold">
                    {user?.last_login
                      ? new Date(user.last_login).toLocaleDateString()
                      : "N/A"}
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {user?.role === "admin" && stats && (
        <>
          <Row className="mb-4">
            <Col>
              <h3>System Statistics</h3>
            </Col>
          </Row>

          <Row>
            <Col md={6} lg={3} className="mb-3">
              <Card className="h-100 border-primary">
                <Card.Body>
                  <div className="d-flex align-items-center">
                    <div className="flex-shrink-0">
                      <FaUsers className="text-primary" size={30} />
                    </div>
                    <div className="flex-grow-1 ms-3">
                      <div className="small text-muted">Total Users</div>
                      <div className="h4 mb-0">{stats.total_users}</div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>

            <Col md={6} lg={3} className="mb-3">
              <Card className="h-100 border-success">
                <Card.Body>
                  <div className="d-flex align-items-center">
                    <div className="flex-shrink-0">
                      <FaUserCheck className="text-success" size={30} />
                    </div>
                    <div className="flex-grow-1 ms-3">
                      <div className="small text-muted">Active Users</div>
                      <div className="h4 mb-0">{stats.active_users}</div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>

            <Col md={6} lg={3} className="mb-3">
              <Card className="h-100 border-warning">
                <Card.Body>
                  <div className="d-flex align-items-center">
                    <div className="flex-shrink-0">
                      <FaUserShield className="text-warning" size={30} />
                    </div>
                    <div className="flex-grow-1 ms-3">
                      <div className="small text-muted">Admin Users</div>
                      <div className="h4 mb-0">{stats.admin_users}</div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>

            <Col md={6} lg={3} className="mb-3">
              <Card className="h-100 border-danger">
                <Card.Body>
                  <div className="d-flex align-items-center">
                    <div className="flex-shrink-0">
                      <FaUserTimes className="text-danger" size={30} />
                    </div>
                    <div className="flex-grow-1 ms-3">
                      <div className="small text-muted">Inactive Users</div>
                      <div className="h4 mb-0">{stats.inactive_users}</div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </Container>
  );
};

export default Dashboard;
