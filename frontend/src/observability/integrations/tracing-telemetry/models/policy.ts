import { SpanKindValue, SpanStatusValue } from '../../../tracing/models/span';
import { TelemetryTypeValue } from '../../../telemetry/models/telemetry';

export interface TracingTelemetryPolicy {
  readonly id: string;
  readonly enabled: boolean;
  readonly priority: number;
  readonly traceName?: string;
  readonly spanName?: string;
  readonly spanKind?: SpanKindValue;
  readonly minDuration?: number;
  readonly statusFilter?: ReadonlyArray<SpanStatusValue>;
  readonly samplingRate?: number;
  readonly telemetryType: TelemetryTypeValue;
  readonly metadata?: Record<string, unknown>;
  readonly staticAttributes?: Record<string, unknown>;
  readonly bypassSamplingOnError?: boolean;
}
