import React, { useState, useEffect, useMemo } from "react";
import { Container, Row, Col, Card, Table, Badge, Alert, Button } from "react-bootstrap";
import { authAPI } from "../services/api";
import { ActivityLog } from "../types";
import { FaHistory, FaClock, FaMapMarkerAlt } from "react-icons/fa";

const PAGE_SIZE = 20;

const ACTIVITY_BADGE_VARIANTS: { [key: string]: string } = {
  login: "success",
  logout: "secondary",
  register: "success",
  profile_update: "info",
  password_change: "warning",
  password_reset: "warning",
  email_change: "primary",
  email_verified: "success",
  admin_update: "dark",
};

const getActivityBadge = (activityType: string) =>
  ACTIVITY_BADGE_VARIANTS[activityType] || "light";

const formatDate = (dateString: string) => new Date(dateString).toLocaleString();

const ActivityLogs: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(totalCount / PAGE_SIZE)),
    [totalCount]
  );

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    authAPI
      .getActivityLogs(page)
      .then((data) => {
        if (cancelled) return;
        setLogs(data.results);
        setTotalCount(data.count);
      })
      .catch(() => {
        if (!cancelled) setError("Failed to load activity logs");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [page]);

  if (isLoading) {
    return (
      <Container>
        <div className="d-flex justify-content-center p-5">
          <div>Loading activity logs...</div>
        </div>
      </Container>
    );
  }

  return (
    <Container>
      <Row className="mb-4">
        <Col>
          <h1>
            <FaHistory className="me-2" />
            Activity Logs
          </h1>
          <p className="text-muted">Track your account activity and security events</p>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      <Row>
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Recent Activity</h5>
            </Card.Header>
            <Card.Body className="p-0">
              {logs.length === 0 ? (
                <div className="text-center p-4">
                  <p className="text-muted">No activity logs found</p>
                </div>
              ) : (
                <Table responsive striped hover className="mb-0">
                  <thead>
                    <tr>
                      <th>Activity</th>
                      <th>Description</th>
                      <th>
                        <FaClock className="me-1" />
                        Date & Time
                      </th>
                      <th>
                        <FaMapMarkerAlt className="me-1" />
                        IP Address
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td>
                          <Badge bg={getActivityBadge(log.activity_type)}>
                            {log.activity_type.replace(/_/g, " ").toUpperCase()}
                          </Badge>
                        </td>
                        <td>{log.description}</td>
                        <td>{formatDate(log.timestamp)}</td>
                        <td>
                          <code>{log.ip_address || "N/A"}</code>
                        </td>
                      </tr>
                    ))}
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
    </Container>
  );
};

export default ActivityLogs;
