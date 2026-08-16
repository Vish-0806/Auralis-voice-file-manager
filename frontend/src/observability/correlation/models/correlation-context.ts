export interface CorrelationContext {
  readonly correlationId: string;
  readonly traceId?: string;
  readonly spanId?: string;
  readonly parentCorrelationId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly source?: string;
  readonly timestamp: number;
  readonly metadata?: Record<string, unknown>;
}

export function generateCorrelationId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'corr_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10) + Math.random().toString(36).substring(2, 10);
  return `corr_${Date.now()}_${rand}`;
}
