/**
 * Event & Messaging Runtime Interfaces (Phase 16.4.2).
 *
 * Defines contracts for IEventRegistry, IEventBus, IEventProvider, and IEventRuntime.
 */

import {
  EventBusHealth,
  EventBusStatistics,
  EventCapabilities,
  EventConfiguration,
  EventContext,
  EventDiagnostics,
  EventHealth,
  EventHistory,
  EventPriority,
  EventRegistration,
  EventState,
  EventStatistics,
  PublishedEvent,
} from './models';

export interface IEventRegistry {
  register(registration: EventRegistration): void;
  unregister(eventType: string): boolean;
  contains(eventType: string): boolean;
  get(eventType: string): EventRegistration | undefined;
  list(): ReadonlyArray<EventRegistration>;
  count(): number;
  clear(): void;
}

export interface IEventBus {
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  history(): EventHistory;
  clearHistory(): void;
  statistics(): EventBusStatistics;
  health(): EventBusHealth;
}

export interface IEventProvider {
  initialize(): EventHealth;
  shutdown(): EventHealth;
  restart(): EventHealth;
  health(): EventHealth;
  statistics(): EventStatistics;
  capabilities(): EventCapabilities;
  diagnostics(): EventDiagnostics;
  state(): EventState;
  configuration(): EventConfiguration;
  context(): EventContext;

  registerEvent(registration: EventRegistration): void;
  unregisterEvent(eventType: string): boolean;
  containsEvent(eventType: string): boolean;
  listEvents(): ReadonlyArray<EventRegistration>;
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  history(): EventHistory;
  clearHistory(): void;
}

export interface IEventRuntime {
  initialize(): EventHealth;
  shutdown(): EventHealth;
  restart(): EventHealth;
  provider(): IEventProvider;
  health(): EventHealth;
  statistics(): EventStatistics;
  capabilities(): EventCapabilities;
  diagnostics(): EventDiagnostics;
  state(): EventState;

  registerEvent(registration: EventRegistration): void;
  unregisterEvent(eventType: string): boolean;
  containsEvent(eventType: string): boolean;
  listEvents(): ReadonlyArray<EventRegistration>;
  publish<T = unknown>(
    eventType: string,
    payload: T,
    options?: { source?: string; correlationId?: string; priority?: EventPriority },
  ): PublishedEvent<T>;
  history(): EventHistory;
  clearHistory(): void;
}
