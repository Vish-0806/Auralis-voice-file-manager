import { AlertSeverityValue } from './severity';

export const AlertState = {
  ACTIVE: 'ACTIVE',
  ACKNOWLEDGED: 'ACKNOWLEDGED',
  SUPPRESSED: 'SUPPRESSED',
  RESOLVED: 'RESOLVED',
  EXPIRED: 'EXPIRED'
} as const;

export type AlertStateValue = typeof AlertState[keyof typeof AlertState];

export interface AlertRecord {
  readonly id: string;
  readonly sourceId: string;
  readonly severity: AlertSeverityValue;
  readonly state: AlertStateValue;
  readonly title: string;
  readonly message: string;
  readonly createdAt: number;
  readonly updatedAt: number;
  readonly metadata: Record<string, unknown>;
}