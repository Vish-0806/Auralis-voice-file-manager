import React from 'react';
import { Card, Button, IconButton } from '../../../components/common';
import { ListenerControlProps } from './ListenerControl.types';

export const ListenerControl: React.FC<ListenerControlProps> = ({
  isRunning,
  loading,
  onStart,
  onStop,
  onRefresh,
  className = ''
}) => {
  const statusLabel = isRunning ? 'Running' : 'Stopped';
  const badgeClass = isRunning ? 'bg-success-subtle text-success border-success-subtle' : 'bg-secondary-subtle text-secondary border-secondary-subtle';

  return (
    <Card className={`listener-control-card shadow-sm border-0 ${className}`}>
      <Card.Header>
        <div className="d-flex align-items-center justify-content-between w-100">
          <h6 className="mb-0 text-secondary d-flex align-items-center gap-2">
            <i className="bi bi-broadcast text-primary" aria-hidden="true"></i>
            <span>Continuous Listener</span>
          </h6>
          <IconButton
            icon="bi-arrow-clockwise"
            aria-label="Refresh Listener Status"
            onClick={onRefresh}
            disabled={loading}
            className={loading ? 'spin' : ''}
          />
        </div>
      </Card.Header>
      <Card.Body>
        <div className="d-flex align-items-center justify-content-between">
          <div>
            <span className="small text-muted d-block mb-1">Status</span>
            <span className={`badge border px-2.5 py-1.5 rounded-pill ${badgeClass}`} data-testid="listener-status-badge">
              <i className={`bi ${isRunning ? 'bi-circle-fill text-success' : 'bi-circle-fill text-muted'} me-1.5`} style={{ fontSize: '0.5rem' }}></i>
              {statusLabel}
            </span>
          </div>

          <div className="d-flex align-items-center gap-2">
            {isRunning ? (
              <Button
                variant="outline-danger"
                size="sm"
                loading={loading}
                onClick={onStop}
                icon="bi-stop-circle"
                aria-label="Stop Continuous Listener"
              >
                Stop
              </Button>
            ) : (
              <Button
                variant="outline-success"
                size="sm"
                loading={loading}
                onClick={onStart}
                icon="bi-play-circle"
                aria-label="Start Continuous Listener"
              >
                Start
              </Button>
            )}
          </div>
        </div>
        <p className="text-muted small mt-3 mb-0" style={{ fontSize: '0.8rem' }}>
          When active, the backend continuously monitors voice commands in the background to orchestrate files automatically.
        </p>
      </Card.Body>
    </Card>

  );
};
export default ListenerControl;
