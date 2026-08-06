/**
 * Event & Messaging Runtime Interfaces (Phase 16.4.1).
 *
 * Defines contracts for IEventProvider and IEventRuntime.
 */

import {
  EventCapabilities,
  EventConfiguration,
  EventContext,
  EventDiagnostics,
  EventHealth,
  EventState,
  EventStatistics,
} from './models';

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
}
