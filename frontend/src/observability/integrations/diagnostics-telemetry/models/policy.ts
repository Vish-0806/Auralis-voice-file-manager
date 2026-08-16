import { DiagnosticSeverityValue, DiagnosticStatusValue, DiagnosticCategoryValue } from '../../../diagnostics/models/diagnostic';
import { TelemetryTypeValue } from '../../../telemetry/models/telemetry';

export interface DiagnosticsTelemetryPolicy {
  readonly id: string;
  readonly enabled: boolean;
  readonly priority: number;
  readonly sourceId?: string;
  readonly checkId?: string;
  readonly category?: DiagnosticCategoryValue;
  readonly severity?: DiagnosticSeverityValue;
  readonly status?: DiagnosticStatusValue;
  readonly minDuration?: number;
  readonly samplingRate?: number;
  readonly telemetryType: TelemetryTypeValue;
  readonly metadata?: Record<string, unknown>;
  readonly staticAttributes?: Record<string, unknown>;
  readonly bypassSamplingOnError?: boolean;
  readonly level: 'RUN' | 'RESULT';
  readonly allowRepeat?: boolean;
}
