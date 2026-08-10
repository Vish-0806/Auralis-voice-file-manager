export interface Trace {
  readonly traceId: string;
  readonly name: string;
  readonly startTime: number;
  readonly endTime?: number;
  readonly duration?: number;
  readonly rootSpanId: string;
  readonly status: 'UNSET' | 'OK' | 'ERROR';
  readonly metadata?: Record<string, unknown>;
  readonly spansCount: number;
}
