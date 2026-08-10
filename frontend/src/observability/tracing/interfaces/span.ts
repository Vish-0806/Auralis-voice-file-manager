import type { SpanKindValue, SpanStatusValue, Span } from '../models/span';
import type { SpanEvent } from '../models/event';
import type { StructuredError } from '../../logging/models/log';
import type { TraceContext } from '../models/context';

export interface ISpan {
  readonly spanId: string;
  readonly traceId: string;
  readonly parentSpanId?: string;
  readonly name: string;
  readonly kind: SpanKindValue;
  readonly startTime: number;
  readonly endTime?: number;
  readonly duration?: number;
  readonly status: SpanStatusValue;
  readonly attributes: Record<string, unknown>;
  readonly events: ReadonlyArray<SpanEvent>;
  readonly error?: StructuredError;

  isEnabled(): boolean;
  setEnabled(enabled: boolean): void;

  setAttribute(key: string, value: unknown): void;
  setAttributes(values: Record<string, unknown>): void;
  addEvent(name: string, attributes?: Record<string, unknown>): void;
  recordError(error: Error | unknown, metadata?: Record<string, unknown>): void;
  setStatus(status: SpanStatusValue): void;
  end(): void;

  toModel(): Span;
  getContext(): TraceContext;
}
