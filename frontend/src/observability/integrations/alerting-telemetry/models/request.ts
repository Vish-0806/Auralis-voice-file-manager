import { TelemetryTypeValue, SeverityValue } from '../../../telemetry/models/telemetry';
import { AlertingTelemetryPolicy } from './policy';

export interface AlertingTelemetryRequest {
  readonly recordId: string;
  readonly telemetryType: TelemetryTypeValue;
  readonly timestamp: number;
  readonly alertId?: string;
  readonly fingerprint?: string;
  readonly ruleId?: string;
  readonly sourceId?: string;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly traceId?: string;
  readonly name: string;
  readonly severity: SeverityValue;
  readonly attributes: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly source: string;
  readonly policy: AlertingTelemetryPolicy;
}
