/**
 * Command Runtime Coordinator Implementation (Phase 16.6.2).
 *
 * Implements ICommandRuntime acting as central coordinator delegating to ICommandProvider.
 * Contains no business logic — all operations are forwarded to the provider instance.
 */

import {
  CommandAlias,
  CommandCapabilities,
  CommandCategory,
  CommandDefinition,
  CommandDiagnostics,
  CommandHealth,
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
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

  public registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition {
    return this._provider.registerCommand(registration);
  }

  public removeCommand(commandId: string): boolean {
    return this._provider.removeCommand(commandId);
  }

  public updateCommand(
    commandId: string,
    updates: Partial<CommandDefinition>,
  ): CommandDefinition {
    return this._provider.updateCommand(commandId, updates);
  }

  public containsCommand(commandId: string): boolean {
    return this._provider.containsCommand(commandId);
  }

  public findCommand(commandId: string): CommandDefinition | undefined {
    return this._provider.findCommand(commandId);
  }

  public findByAlias(alias: string): CommandDefinition | undefined {
    return this._provider.findByAlias(alias);
  }

  public findByName(name: string): CommandDefinition | undefined {
    return this._provider.findByName(name);
  }

  public listCommands(category?: string): ReadonlyArray<CommandDefinition> {
    return this._provider.listCommands(category);
  }

  public listAliases(): ReadonlyArray<CommandAlias> {
    return this._provider.listAliases();
  }

  public listCategories(): ReadonlyArray<CommandCategory> {
    return this._provider.listCategories();
  }

  public search(query: string): ReadonlyArray<CommandDefinition> {
    return this._provider.search(query);
  }

  public registryStatistics(): CommandRegistryStatistics {
    return this._provider.registryStatistics();
  }

  public registryHealth(): CommandRegistryHealth {
    return this._provider.registryHealth();
  }
}
