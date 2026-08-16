import { ICorrelationRuntime } from '../interfaces/correlation-runtime';
import { ICorrelationProvider } from '../interfaces/correlation-provider';
import { CorrelationProvider } from '../provider/CorrelationProvider';
import {
  CorrelationContext,
  CorrelatedEvent,
  CorrelationLink,
  CorrelationQuery,
  CorrelationStatistics,
  CorrelationDiagnostics,
  CorrelationHealthStatus
} from '../models';

export class CorrelationRuntime implements ICorrelationRuntime {
  private readonly _provider: ICorrelationProvider;

  constructor(provider?: ICorrelationProvider) {
    this._provider = provider || new CorrelationProvider();
  }

  public provider(): ICorrelationProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public createContext(options?: {
    traceId?: string;
    spanId?: string;
    parentCorrelationId?: string;
    requestId?: string;
    operationId?: string;
    source?: string;
    metadata?: Record<string, unknown>;
  }): CorrelationContext {
    return this._provider.createContext(options);
  }

  public childContext(
    parentContext: CorrelationContext,
    overrides?: Partial<CorrelationContext>
  ): CorrelationContext {
    return this._provider.childContext(parentContext, overrides);
  }

  public validateContext(context: CorrelationContext): void {
    this._provider.validateContext(context);
  }

  public recordEvent(eventInput: {
    eventId?: string;
    eventType: string;
    context: CorrelationContext;
    sourceSubsystem: string;
    metadata?: Record<string, unknown>;
    payload?: Record<string, unknown>;
  }): CorrelatedEvent {
    return this._provider.recordEvent(eventInput);
  }

  public getEvent(eventId: string): CorrelatedEvent | null {
    return this._provider.getEvent(eventId);
  }

  public query(query: CorrelationQuery): ReadonlyArray<CorrelatedEvent> {
    return this._provider.query(query);
  }

  public addLink(link: {
    sourceId: string;
    targetId: string;
    kind: string;
    metadata?: Record<string, unknown>;
  }): CorrelationLink {
    return this._provider.addLink(link);
  }

  public getLinksForSource(sourceId: string): ReadonlyArray<CorrelationLink> {
    return this._provider.getLinksForSource(sourceId);
  }

  public getLinksForTarget(targetId: string): ReadonlyArray<CorrelationLink> {
    return this._provider.getLinksForTarget(targetId);
  }

  public getDiagnostics(): CorrelationDiagnostics {
    return this._provider.getDiagnostics();
  }

  public getStatistics(): CorrelationStatistics {
    return this._provider.getStatistics();
  }

  public getHealth(): CorrelationHealthStatus {
    return this._provider.getHealth();
  }
}
