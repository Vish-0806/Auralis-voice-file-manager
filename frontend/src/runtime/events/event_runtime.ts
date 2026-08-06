/**
 * Event Runtime Coordinator Implementation (Phase 16.4.1).
 *
 * Implements IEventRuntime acting as central coordinator delegating to IEventProvider.
 */

import {
  EventCapabilities,
  EventDiagnostics,
  EventHealth,
  EventState,
  EventStatistics,
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
}
