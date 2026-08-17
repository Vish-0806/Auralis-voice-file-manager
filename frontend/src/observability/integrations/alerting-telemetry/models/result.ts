import { TelemetryTypeValue } from '../../../telemetry/models/telemetry';

export interface AlertingTelemetryResult {
  readonly status: 'ACCEPTED' | 'SKIPPED' | 'REJECTED';
  readonly triggerId?: string;
  readonly recordId?: string;
  readonly telemetryType?: TelemetryTypeValue;
  readonly reason?: string;
  readonly duration: number;
  readonly timestamp: number;
}
