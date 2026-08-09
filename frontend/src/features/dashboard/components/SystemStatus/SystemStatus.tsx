import React, { useState, useEffect } from 'react';
import { assistantService, HealthResponsePayload, StatusResponsePayload } from '../../../../services/api/assistantService';
import { Card } from '../../../../components/common';

export const SystemStatus: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'healthy' | 'degraded' | 'unavailable' | 'error'>('loading');
  const [healthData, setHealthData] = useState<HealthResponsePayload | null>(null);
  const [statusData, setStatusData] = useState<StatusResponsePayload | null>(null);

  useEffect(() => {
    let active = true;

    const fetchStatus = async () => {
      try {
        const [health, platform] = await Promise.all([
          assistantService.getHealth(),
          assistantService.getStatus().catch(() => null) // Allow status to fail for degraded state checking
        ]);

        if (!active) return;

        if (health && health.status === 'ok') {
          setHealthData(health);
          if (platform) {
            setStatusData(platform);
            setStatus('healthy');
          } else {
            setStatus('degraded');
          }
        } else {
          setStatus('error');
        }
      } catch (err) {
        if (active) {
          setStatus('unavailable');
        }
      }
    };

    fetchStatus();
    return () => {
      active = false;
    };
  }, []);

  if (status === 'loading') {
    return (
      <Card className="border-0 shadow-sm mb-4">
        <Card.Body className="d-flex align-items-center justify-content-center py-4">
          <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
          <span className="text-muted small">Checking system status...</span>
        </Card.Body>
      </Card>
    );
  }

  let statusText = 'System Offline';
  let badgeVariant = 'bg-danger text-danger-inverse';
  let statusDesc = 'The Auralis FastAPI backend is currently unreachable.';

  if (status === 'healthy') {
    statusText = 'Online';
    badgeVariant = 'bg-success-subtle text-success border border-success-subtle';
    statusDesc = `All capabilities loaded successfully. Version ${healthData?.version || 'N/A'}`;
  } else if (status === 'degraded') {
    statusText = 'Degraded';
    badgeVariant = 'bg-warning-subtle text-warning border border-warning-subtle';
    statusDesc = 'System health is healthy, but platform stats are currently unavailable.';
  } else if (status === 'error') {
    statusText = 'Error';
    badgeVariant = 'bg-danger-subtle text-danger border border-danger-subtle';
    statusDesc = 'The system returned an unhealthy status code.';
  }

  return (
    <Card className="border-0 shadow-sm mb-4">
      <Card.Body>
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h6 className="card-subtitle mb-0 text-muted text-uppercase small fw-bold">Backend Service Status</h6>
          <span className={`badge px-2.5 py-1.5 rounded-pill ${badgeVariant}`} data-testid="backend-status-badge">
            {statusText}
          </span>
        </div>
        <p className="card-text text-secondary small mb-2">{statusDesc}</p>
        
        {status === 'healthy' && statusData && (
          <div className="mt-3 pt-3 border-top border-light" style={{ fontSize: '0.8rem' }}>
            <div className="row g-2">
              <div className="col-6">
                <span className="text-muted d-block">OS Platform:</span>
                <span className="fw-semibold text-secondary">{statusData.platform.system} ({statusData.platform.machine})</span>
              </div>
              <div className="col-6">
                <span className="text-muted d-block">Capabilities:</span>
                <span className="fw-semibold text-secondary">{statusData.loaded_capabilities.length} active modules</span>
              </div>
            </div>
          </div>
        )}
      </Card.Body>
    </Card>
  );
};
export default SystemStatus;
