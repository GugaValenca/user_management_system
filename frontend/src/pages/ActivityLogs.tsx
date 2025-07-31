import React, { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Table,
  Badge,
  Alert,
} from "react-bootstrap";
import { authAPI } from "../services/api";
import { ActivityLog } from "../types";
import { FaHistory, FaClock, FaMapMarkerAlt } from "react-icons/fa";

const ActivityLogs: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const logsData = await authAPI.getActivityLogs();
        setLogs(logsData);
      } catch (error: any) {
        setError("Failed to load activity logs");
      } finally {
        setIsLoading(false);
      }
    };

    fetchLogs();
  }, []);

  const getActivityBadge = (activityType: string) => {
    const badgeMap: { [key: string]: string } = {
      login: "success",
      logout: "secondary",
      profile_update: "info",
      password_change: "warning",
      email_change: "primary",
    };
    return badgeMap[activityType] || "light";
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

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
          <p className="text-muted">
            Track your account activity and security events
          </p>
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
                            {log.activity_type.replace("_", " ").toUpperCase()}
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
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default ActivityLogs;
