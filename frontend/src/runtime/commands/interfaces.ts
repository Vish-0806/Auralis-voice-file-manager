/**
 * Command Runtime Interfaces (Phase 16.6.2).
 *
 * Defines contract specifications for ICommandRegistry, ICommandProvider, and ICommandRuntime.
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
}
