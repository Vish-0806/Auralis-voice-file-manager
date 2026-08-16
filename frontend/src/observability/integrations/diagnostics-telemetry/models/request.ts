import { TelemetryTypeValue, SeverityValue } from '../../../telemetry/models/telemetry';

export interface DiagnosticsTelemetryRequest {
  readonly recordId: string;
  readonly telemetryType: TelemetryTypeValue;
  readonly timestamp: number;
  readonly diagnosticRunId: string;
  readonly resultId?: string;
  readonly sourceId: string;
  readonly checkId?: string;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly traceId?: string;
  readonly name: string;
  readonly severity: SeverityValue;
  readonly status: string;
  readonly attributes: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly source: string;
}
