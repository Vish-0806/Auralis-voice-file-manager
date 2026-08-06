/**
 * Event Runtime Coordinator Implementation (Phase 16.4.2).
 *
 * Implements IEventRuntime acting as central coordinator delegating to IEventProvider.
 */

import {
  EventCapabilities,
  EventDiagnostics,
  EventHealth,
  EventHistory,
  EventPriority,
  EventRegistration,
  EventState,
  EventStatistics,
  PublishedEvent,
} from './models';
import { IEventProvider, IEventRuntime } from './interfaces';
import { EventProvider } from './event_provider';

export class EventRuntime implements IEventRuntime {
  private readonly _provider: IEventProvider;

  constructor(provider?: IEventProvider) {
    this._provider = provider ?? new EventProvider();
  }

  public initialize(): EventHealth {
    return this._provider.initialize();
  }

  public shutdown(): EventHealth {
    return this._provider.shutdown();
  }

  public restart(): EventHealth {
    return this._provider.restart();
  }

  public provider(): IEventProvider {
    return this._provider;
  }

  public health(): EventHealth {
    return this._provider.health();
  }

  public statistics(): EventStatistics {
    return this._provider.statistics();
  }

  public capabilities(): EventCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): EventDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): EventState {
    return this._provider.state();
  }

  public registerEvent(registration: EventRegistration): void {
    this._provider.registerEvent(registration);
  }

  public unregisterEvent(eventType: string): boolean {
    return this._provider.unregisterEvent(eventType);
  }

  public containsEvent(eventType: string): boolean {
    return this._provider.containsEvent(eventType);
  }

  public listEvents(): ReadonlyArray<EventRegistration> {
    return this._provider.listEvents();
  }

  public publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T> {
    return this._provider.publish(eventType, payload, options);
  }

  public history(): EventHistory {
    return this._provider.history();
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }
}
