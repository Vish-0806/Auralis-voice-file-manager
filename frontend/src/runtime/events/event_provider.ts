/**
 * Event Provider Implementation (Phase 16.4.1).
 *
 * Implements IEventProvider owning runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities reporting,
 * and diagnostics aggregation for the Frontend Event Runtime.
 */

import {
  createEventCapabilities,
  createEventConfiguration,
  createEventContext,
  createEventDiagnostics,
  createEventHealth,
  createEventState,
  createEventStatistics,
  EventCapabilities,
  EventConfiguration,
  EventContext,
  EventDiagnostics,
  EventHealth,
  EventRuntimeState,
  EventState,
  EventStatistics,
} from './models';
import { IEventProvider } from './interfaces';

export class EventProvider implements IEventProvider {
  private _runtimeState: EventRuntimeState = EventRuntimeState.UNINITIALIZED;
  private readonly _config: EventConfiguration;
  private readonly _capabilities: EventCapabilities;
  private readonly _context: EventContext;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: EventConfiguration,
    capabilities?: EventCapabilities,
    context?: EventContext,
  ) {
    this._config = config ?? createEventConfiguration();
    this._capabilities = capabilities ?? createEventCapabilities();
    this._context = context ?? createEventContext();
  }

  public initialize(): EventHealth {
    if (
      this._runtimeState === EventRuntimeState.INITIALIZING ||
      this._runtimeState === EventRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = EventRuntimeState.INITIALIZING;
    this._runtimeState = EventRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): EventHealth {
    if (this._runtimeState === EventRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = EventRuntimeState.STOPPING;
    this._runtimeState = EventRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): EventHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): EventHealth {
    const healthy = this._runtimeState === EventRuntimeState.READY;
    const message = healthy
      ? 'Event runtime is ready and operational.'
      : `Event runtime is in state ${this._runtimeState}.`;

    return createEventHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): EventStatistics {
    const uptime =
      this._runtimeState === EventRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createEventStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): EventCapabilities {
    return this._capabilities;
  }

  public diagnostics(): EventDiagnostics {
    return createEventDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      timestamp: new Date().toISOString(),
    });
  }

  public state(): EventState {
    return createEventState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === EventRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): EventConfiguration {
    return this._config;
  }

  public context(): EventContext {
    return this._context;
  }
}
