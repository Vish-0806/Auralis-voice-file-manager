import { CorrelationContext } from './correlation-context';

export interface CorrelatedEvent {
  readonly eventId: string;
  readonly eventType: string;
  readonly timestamp: number;
  readonly context: CorrelationContext;
  readonly sourceSubsystem: string;
  readonly metadata?: Record<string, unknown>;
  readonly payload?: Record<string, unknown>;
}

export function generateEventId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'ev_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10);
  return `ev_${Date.now()}_${rand}`;
}
