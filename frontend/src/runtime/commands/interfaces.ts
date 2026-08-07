/**
 * Command Runtime Interfaces (Phase 16.6.3).
 *
 * Defines contract specifications for ICommandRegistry, ICommandExecutor,
 * ICommandProvider, and ICommandRuntime.
 */

import {
  CommandAlias,
  CommandCapabilities,
  CommandCategory,
  CommandConfiguration,
  CommandContext,
  CommandDefinition,
  CommandDiagnostics,
  CommandExecutionHealth,
  CommandExecutionRecord,
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandExecutionStatistics,
  CommandHandler,
  CommandHealth,
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  ExecutionDiagnostics,
} from './models';

export interface ICommandRegistry {
  registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition;
  removeCommand(commandId: string): boolean;
  updateCommand(commandId: string, updates: Partial<CommandDefinition>): CommandDefinition;
  containsCommand(commandId: string): boolean;
  findCommand(commandId: string): CommandDefinition | undefined;
  findByAlias(alias: string): CommandDefinition | undefined;
  findByName(name: string): CommandDefinition | undefined;
  listCommands(category?: string): ReadonlyArray<CommandDefinition>;
  listAliases(): ReadonlyArray<CommandAlias>;
  listCategories(): ReadonlyArray<CommandCategory>;
  search(query: string): ReadonlyArray<CommandDefinition>;
  statistics(): CommandRegistryStatistics;
  health(): CommandRegistryHealth;
  clear(): void;
}

export interface ICommandExecutor {
  registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void;
  unregisterHandler(commandId: string): boolean;
  hasHandler(commandId: string): boolean;
  execute<TResult = unknown>(request: CommandExecutionRequest): CommandExecutionResult<TResult>;
  executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>>;
  validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean>;
  cancelExecution(executionId: string): boolean;
  executionHistory(): ReadonlyArray<CommandExecutionRecord>;
  clearExecutionHistory(): void;
  statistics(): CommandExecutionStatistics;
  health(): CommandExecutionHealth;
  diagnostics(): ExecutionDiagnostics;
}

export interface ICommandProvider {
  initialize(): CommandHealth;
  shutdown(): CommandHealth;
  restart(): CommandHealth;
  health(): CommandHealth;
  statistics(): CommandStatistics;
  capabilities(): CommandCapabilities;
  diagnostics(): CommandDiagnostics;
  state(): CommandState;
  configuration(): CommandConfiguration;
  context(): CommandContext;
  status(): CommandRuntimeState;

  registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition;
  removeCommand(commandId: string): boolean;
  updateCommand(commandId: string, updates: Partial<CommandDefinition>): CommandDefinition;
  containsCommand(commandId: string): boolean;
  findCommand(commandId: string): CommandDefinition | undefined;
  findByAlias(alias: string): CommandDefinition | undefined;
  findByName(name: string): CommandDefinition | undefined;
  listCommands(category?: string): ReadonlyArray<CommandDefinition>;
  listAliases(): ReadonlyArray<CommandAlias>;
  listCategories(): ReadonlyArray<CommandCategory>;
  search(query: string): ReadonlyArray<CommandDefinition>;
  registryStatistics(): CommandRegistryStatistics;
  registryHealth(): CommandRegistryHealth;

  registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void;
  unregisterHandler(commandId: string): boolean;
  hasHandler(commandId: string): boolean;
  execute<TResult = unknown>(request: CommandExecutionRequest): CommandExecutionResult<TResult>;
  executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>>;
  validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean>;
  cancelExecution(executionId: string): boolean;
  executionHistory(): ReadonlyArray<CommandExecutionRecord>;
  clearExecutionHistory(): void;
  executionStatistics(): CommandExecutionStatistics;
  executionHealth(): CommandExecutionHealth;
}

export interface ICommandRuntime {
  initialize(): CommandHealth;
  shutdown(): CommandHealth;
  restart(): CommandHealth;
  health(): CommandHealth;
  statistics(): CommandStatistics;
  capabilities(): CommandCapabilities;
  diagnostics(): CommandDiagnostics;
  state(): CommandState;
  status(): CommandRuntimeState;
  provider(): ICommandProvider;

  registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition;
  removeCommand(commandId: string): boolean;
  updateCommand(commandId: string, updates: Partial<CommandDefinition>): CommandDefinition;
  containsCommand(commandId: string): boolean;
  findCommand(commandId: string): CommandDefinition | undefined;
  findByAlias(alias: string): CommandDefinition | undefined;
  findByName(name: string): CommandDefinition | undefined;
  listCommands(category?: string): ReadonlyArray<CommandDefinition>;
  listAliases(): ReadonlyArray<CommandAlias>;
  listCategories(): ReadonlyArray<CommandCategory>;
  search(query: string): ReadonlyArray<CommandDefinition>;
  registryStatistics(): CommandRegistryStatistics;
  registryHealth(): CommandRegistryHealth;

  registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void;
  unregisterHandler(commandId: string): boolean;
  hasHandler(commandId: string): boolean;
  execute<TResult = unknown>(request: CommandExecutionRequest): CommandExecutionResult<TResult>;
  executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>>;
  validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean>;
  cancelExecution(executionId: string): boolean;
  executionHistory(): ReadonlyArray<CommandExecutionRecord>;
  clearExecutionHistory(): void;
  executionStatistics(): CommandExecutionStatistics;
  executionHealth(): CommandExecutionHealth;
}
