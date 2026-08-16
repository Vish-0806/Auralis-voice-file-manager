import { SpanKindValue, SpanStatusValue } from '../../../tracing/models/span';
import { SpanEvent } from '../../../tracing/models/event';
import { StructuredError } from '../../../logging/models/log';

export interface TracingTelemetryTrigger {
  readonly triggerId: string;
  readonly traceId: string;
  readonly spanId: string;
  readonly parentSpanId?: string;
  readonly timestamp: number;
  readonly startTime: number;
  readonly endTime?: number;
  readonly duration: number;
  readonly traceName?: string;
  readonly spanName: string;
  readonly spanKind: SpanKindValue;
  readonly spanStatus: SpanStatusValue;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly attributes: Record<string, unknown>;
  readonly events: ReadonlyArray<SpanEvent>;
  readonly error?: StructuredError;
}
