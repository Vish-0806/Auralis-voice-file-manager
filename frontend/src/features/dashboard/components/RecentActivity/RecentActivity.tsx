import React from 'react';
import { Card, EmptyState } from '../../../../components/common';

export const RecentActivity: React.FC = () => {
  return (
    <Card className="border-0 shadow-sm mb-4">
      <Card.Header>
        <h6 className="mb-0 text-secondary fw-bold d-flex align-items-center gap-2">
          <i className="bi bi-list-task text-primary" aria-hidden="true"></i>
          <span>Recent Activity</span>
        </h6>
      </Card.Header>
      
      <Card.Body>
        <div style={{ minHeight: '160px' }} className="d-flex align-items-center justify-content-center">
          <EmptyState
            title="No Recent Activity"
            description="Log activity will appear when file organization, editing buffers, and voice command operations are executed."
            icon="bi-activity text-muted"
          />
        </div>
      </Card.Body>
    </Card>
  );
};
export default RecentActivity;
