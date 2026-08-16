import {
  CorrelationContext,
  CorrelatedEvent,
  CorrelationLink,
  CorrelationQuery,
  CorrelationStatistics,
  CorrelationDiagnostics,
  CorrelationHealthStatus
} from '../models';

export interface ICorrelationProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  createContext(options?: {
    traceId?: string;
    spanId?: string;
    parentCorrelationId?: string;
    requestId?: string;
    operationId?: string;
    source?: string;
    metadata?: Record<string, unknown>;
  }): CorrelationContext;
  childContext(
    parentContext: CorrelationContext,
    overrides?: Partial<CorrelationContext>
  ): CorrelationContext;
  validateContext(context: CorrelationContext): void;
  recordEvent(eventInput: {
    eventId?: string;
    eventType: string;
    context: CorrelationContext;
    sourceSubsystem: string;
    metadata?: Record<string, unknown>;
    payload?: Record<string, unknown>;
  }): CorrelatedEvent;
  getEvent(eventId: string): CorrelatedEvent | null;
  query(query: CorrelationQuery): ReadonlyArray<CorrelatedEvent>;
  addLink(link: {
    sourceId: string;
    targetId: string;
    kind: string;
    metadata?: Record<string, unknown>;
  }): CorrelationLink;
  getLinksForSource(sourceId: string): ReadonlyArray<CorrelationLink>;
  getLinksForTarget(targetId: string): ReadonlyArray<CorrelationLink>;
  getDiagnostics(): CorrelationDiagnostics;
  getStatistics(): CorrelationStatistics;
  getHealth(): CorrelationHealthStatus;
}
