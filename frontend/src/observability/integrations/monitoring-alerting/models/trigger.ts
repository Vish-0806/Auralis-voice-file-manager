import { MonitorStatusValue } from '../../../models/health';
import { MonitoringResult } from '../../../models/monitoring';

export interface MonitoringAlertTrigger {
  readonly triggerId: string;
  readonly componentId: string;
  readonly checkId?: string;
  readonly status: MonitorStatusValue;
  readonly severity?: string;
  readonly result?: MonitoringResult;
  readonly timestamp: number;
  readonly correlationId?: string;
  readonly metadata?: Record<string, unknown>;
}

export function generateTriggerId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'trig_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10);
  return `trig_${Date.now()}_${rand}`;
}
