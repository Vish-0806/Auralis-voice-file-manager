import type { SpanEvent } from './event';
import type { StructuredError } from '../../logging/models/log';

export const SpanKind = {
  INTERNAL: 'INTERNAL',
  SERVER: 'SERVER',
  CLIENT: 'CLIENT',
  PRODUCER: 'PRODUCER',
  CONSUMER: 'CONSUMER'
} as const;

export type SpanKindValue = typeof SpanKind[keyof typeof SpanKind];

export const SpanStatus = {
  UNSET: 'UNSET',
  OK: 'OK',
  ERROR: 'ERROR'
} as const;

export type SpanStatusValue = typeof SpanStatus[keyof typeof SpanStatus];

export interface Span {
  readonly spanId: string;
  readonly traceId: string;
  readonly parentSpanId?: string;
  readonly name: string;
  readonly kind: SpanKindValue;
  readonly startTime: number;
  readonly endTime?: number;
  readonly duration?: number;
  readonly status: SpanStatusValue;
  readonly attributes?: Record<string, unknown>;
  readonly events?: ReadonlyArray<SpanEvent>;
  readonly error?: StructuredError;
}
