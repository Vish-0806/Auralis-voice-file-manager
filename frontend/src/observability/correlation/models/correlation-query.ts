export interface CorrelationQuery {
  readonly correlationId?: string;
  readonly traceId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly eventType?: string;
  readonly source?: string;
  readonly startTime?: number;
  readonly endTime?: number;
}
