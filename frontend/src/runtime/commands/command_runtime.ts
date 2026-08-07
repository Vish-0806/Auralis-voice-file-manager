/**
 * Command Runtime Coordinator Implementation (Phase 16.6.1).
 *
 * Implements ICommandRuntime acting as central coordinator delegating to ICommandProvider.
 * Contains no business logic — all operations are forwarded to the provider instance.
 */

import {
  CommandCapabilities,
  CommandDiagnostics,
  CommandHealth,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
} from './models';
import { ICommandProvider, ICommandRuntime } from './interfaces';
import { CommandProvider } from './command_provider';

export class CommandRuntime implements ICommandRuntime {
  private readonly _provider: ICommandProvider;

  constructor(provider?: ICommandProvider) {
    this._provider = provider ?? new CommandProvider();
  }

  public initialize(): CommandHealth {
    return this._provider.initialize();
  }

  public shutdown(): CommandHealth {
    return this._provider.shutdown();
  }

  public restart(): CommandHealth {
    return this._provider.restart();
  }

  public health(): CommandHealth {
    return this._provider.health();
  }

  public statistics(): CommandStatistics {
    return this._provider.statistics();
  }

  public capabilities(): CommandCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): CommandDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): CommandState {
    return this._provider.state();
  }

  public status(): CommandRuntimeState {
    return this._provider.status();
  }

  public provider(): ICommandProvider {
    return this._provider;
  }
}
