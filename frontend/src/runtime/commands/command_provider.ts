/**
 * Command Provider Implementation (Phase 16.6.2).
 *
 * Implements ICommandProvider owning runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities
 * reporting, command registration management, alias resolution, category lookup,
 * search engine evaluation, registry health, and diagnostics generation.
 */

import {
  CommandAlias,
  CommandCapabilities,
  CommandCategory,
  CommandConfiguration,
  CommandContext,
  CommandDefinition,
  CommandDiagnostics,
  CommandHealth,
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  createCommandCapabilities,
  createCommandConfiguration,
  createCommandContext,
  createCommandDiagnostics,
  createCommandHealth,
  createCommandState,
  createCommandStatistics,
} from './models';
import { ICommandProvider, ICommandRegistry } from './interfaces';
import { CommandRegistry } from './command_registry';

export class CommandProvider implements ICommandProvider {
  private _runtimeState: CommandRuntimeState = CommandRuntimeState.UNINITIALIZED;
  private readonly _config: CommandConfiguration;
  private readonly _capabilities: CommandCapabilities;
  private readonly _context: CommandContext;
  private readonly _registry: ICommandRegistry;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: CommandConfiguration,
    capabilities?: CommandCapabilities,
    context?: CommandContext,
    registry?: ICommandRegistry,
  ) {
    this._config = config ?? createCommandConfiguration();
    this._capabilities = capabilities ?? createCommandCapabilities();
    this._context = context ?? createCommandContext();
    this._registry = registry ?? new CommandRegistry();
  }

  public initialize(): CommandHealth {
    if (
      this._runtimeState === CommandRuntimeState.INITIALIZING ||
      this._runtimeState === CommandRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = CommandRuntimeState.INITIALIZING;
    this._runtimeState = CommandRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): CommandHealth {
    if (this._runtimeState === CommandRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = CommandRuntimeState.STOPPING;
    this._runtimeState = CommandRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): CommandHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): CommandHealth {
    const healthy = this._runtimeState === CommandRuntimeState.READY;
    const message = healthy
      ? 'Command runtime is ready and operational.'
      : `Command runtime is in state ${this._runtimeState}.`;

    return createCommandHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): CommandStatistics {
    const uptime =
      this._runtimeState === CommandRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createCommandStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): CommandCapabilities {
    return this._capabilities;
  }

  public diagnostics(): CommandDiagnostics {
    const commands = this._registry.listCommands();
    const categories = this._registry.listCategories();
    const aliases = this._registry.listAliases();

    return createCommandDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      registeredCommands: commands.map((c) => c.id),
      registeredCategories: categories.map((c) => c.name),
      registeredAliases: aliases.map((a) => a.alias),
      registryStatistics: this._registry.statistics(),
      registryHealth: this._registry.health(),
      timestamp: new Date().toISOString(),
    });
  }

  public state(): CommandState {
    return createCommandState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === CommandRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): CommandConfiguration {
    return this._config;
  }

  public context(): CommandContext {
    return this._context;
  }

  public status(): CommandRuntimeState {
    return this._runtimeState;
  }

  public registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition {
    return this._registry.registerCommand(registration);
  }

  public removeCommand(commandId: string): boolean {
    return this._registry.removeCommand(commandId);
  }

  public updateCommand(
    commandId: string,
    updates: Partial<CommandDefinition>,
  ): CommandDefinition {
    return this._registry.updateCommand(commandId, updates);
  }

  public containsCommand(commandId: string): boolean {
    return this._registry.containsCommand(commandId);
  }

  public findCommand(commandId: string): CommandDefinition | undefined {
    return this._registry.findCommand(commandId);
  }

  public findByAlias(alias: string): CommandDefinition | undefined {
    return this._registry.findByAlias(alias);
  }

  public findByName(name: string): CommandDefinition | undefined {
    return this._registry.findByName(name);
  }

  public listCommands(category?: string): ReadonlyArray<CommandDefinition> {
    return this._registry.listCommands(category);
  }

  public listAliases(): ReadonlyArray<CommandAlias> {
    return this._registry.listAliases();
  }

  public listCategories(): ReadonlyArray<CommandCategory> {
    return this._registry.listCategories();
  }

  public search(query: string): ReadonlyArray<CommandDefinition> {
    return this._registry.search(query);
  }

  public registryStatistics(): CommandRegistryStatistics {
    return this._registry.statistics();
  }

  public registryHealth(): CommandRegistryHealth {
    return this._registry.health();
  }
}
