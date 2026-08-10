import type { ISpan } from './span';
import type { Trace } from '../models/trace';
import type { Span } from '../models/span';
import type { TraceContext } from '../models/context';
import type { TracingStatistics, TracingDiagnostics } from '../models/statistics';

export interface StartTraceOptions {
  readonly traceId?: string;
  readonly parentSpanId?: string;
  readonly attributes?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly kind?: 'INTERNAL' | 'SERVER' | 'CLIENT' | 'PRODUCER' | 'CONSUMER';
}

export interface StartSpanOptions {
  readonly traceId: string;
  readonly parentSpanId?: string;
  readonly attributes?: Record<string, unknown>;
  readonly kind?: 'INTERNAL' | 'SERVER' | 'CLIENT' | 'PRODUCER' | 'CONSUMER';
}

export interface ITracingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  startTrace(name: string, options?: StartTraceOptions): ISpan;
  startSpan(name: string, options: StartSpanOptions): ISpan;

  getTrace(traceId: string): Trace | null;
  getSpan(spanId: string): Span | null;
  getTraceSpans(traceId: string): ReadonlyArray<Span>;
  getChildSpans(spanId: string): ReadonlyArray<Span>;

  listRecentTraces(limit?: number): ReadonlyArray<Trace>;
  clearHistory(): void;

  getActiveSpans(): ReadonlyArray<ISpan>;
  getActiveSpanCount(): number;

  createContext(span: ISpan): TraceContext;
  extractContext(context: TraceContext): TraceContext;
  injectContext(context: TraceContext): TraceContext;

  getStatistics(): TracingStatistics;
  getDiagnostics(): TracingDiagnostics;
}
