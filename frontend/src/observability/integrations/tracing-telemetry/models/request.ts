import { TelemetryTypeValue, SeverityValue } from '../../../telemetry/models/telemetry';

export interface TracingTelemetryRequest {
  readonly recordId: string;
  readonly telemetryType: TelemetryTypeValue;
  readonly timestamp: number;
  readonly traceId: string;
  readonly spanId: string;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly name: string;
  readonly duration: number;
  readonly severity: SeverityValue;
  readonly attributes: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly source: string;
}
