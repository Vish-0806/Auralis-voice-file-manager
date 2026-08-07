/**
 * Command Runtime Domain Models (Phase 16.6.2).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, command definitions,
 * parameters, registrations, categories, aliases, registry statistics, registry health,
 * and diagnostics telemetry for the Frontend Command Runtime.
 */

export enum CommandRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export interface CommandState {
  readonly runtimeState: CommandRuntimeState;
  readonly initialized: boolean;
  readonly startedAt: string | null;
}

export interface CommandContext {
  readonly runtimeId: string;
  readonly createdAt: string;
  readonly environment: string;
}

export interface CommandCapabilities {
  readonly supportsCommandExecution: boolean;
  readonly supportsCommandValidation: boolean;
  readonly supportsUndoRedo: boolean;
  readonly supportsCommandHistory: boolean;
  readonly supportsBatchExecution: boolean;
  readonly supportsDiagnostics: boolean;
}

export interface CommandHealth {
  readonly healthy: boolean;
  readonly runtimeState: CommandRuntimeState;
  readonly message: string;
}

export interface CommandStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface CommandConfiguration {
  readonly runtimeName: string;
  readonly version: string;
  readonly strictMode: boolean;
  readonly maxHistorySize?: number;
  readonly allowDuplicateNames?: boolean;
}

export interface CommandParameter {
  readonly name: string;
  readonly type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'any';
  readonly required: boolean;
  readonly description?: string;
  readonly defaultValue?: unknown;
}

export interface CommandDefinition {
  readonly id: string;
  readonly displayName: string;
  readonly description: string;
  readonly category: string;
  readonly aliases: ReadonlyArray<string>;
  readonly parameters: ReadonlyArray<CommandParameter>;
  readonly examples?: ReadonlyArray<string>;
  readonly version?: string;
  readonly enabled: boolean;
  readonly hidden?: boolean;
  readonly experimental?: boolean;
  readonly deprecated?: boolean;
  readonly permission?: string;
  readonly tags?: ReadonlyArray<string>;
}

export interface CommandAlias {
  readonly alias: string;
  readonly commandId: string;
}

export interface CommandCategory {
  readonly name: string;
  readonly description?: string;
  readonly commandCount: number;
}

export interface CommandRegistration {
  readonly id: string;
  readonly displayName: string;
  readonly description?: string;
  readonly category?: string;
  readonly aliases?: ReadonlyArray<string>;
  readonly parameters?: ReadonlyArray<CommandParameter>;
  readonly examples?: ReadonlyArray<string>;
  readonly version?: string;
  readonly enabled?: boolean;
  readonly hidden?: boolean;
  readonly experimental?: boolean;
  readonly deprecated?: boolean;
  readonly permission?: string;
  readonly tags?: ReadonlyArray<string>;
  readonly registeredAt?: string;
}

export interface CommandRegistryStatistics {
  readonly registeredCommands: number;
  readonly removedCommands: number;
  readonly updates: number;
  readonly lookups: number;
  readonly failedLookups: number;
  readonly searches: number;
  readonly duplicateAttempts: number;
  readonly categoryCount: number;
  readonly aliasCount: number;
}

export interface CommandRegistryHealth {
  readonly healthy: boolean;
  readonly duplicateIds: number;
  readonly duplicateAliases: number;
  readonly missingMetadata: number;
  readonly orphanCategories: number;
  readonly invalidRegistrations: number;
  readonly message: string;
}

export interface CommandDiagnostics {
  readonly health: CommandHealth;
  readonly statistics: CommandStatistics;
  readonly capabilities: CommandCapabilities;
  readonly context: CommandContext;
  readonly registeredCommands?: ReadonlyArray<string>;
  readonly registeredCategories?: ReadonlyArray<string>;
  readonly registeredAliases?: ReadonlyArray<string>;
  readonly registryStatistics?: CommandRegistryStatistics;
  readonly registryHealth?: CommandRegistryHealth;
  readonly timestamp: string;
}

export function createCommandState(params: Partial<CommandState> = {}): CommandState {
  return Object.freeze({
    runtimeState: params.runtimeState ?? CommandRuntimeState.UNINITIALIZED,
    initialized: params.initialized ?? false,
    startedAt: params.startedAt ?? null,
  });
}

export function createCommandContext(params: Partial<CommandContext> = {}): CommandContext {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `command_runtime_${Date.now()}`,
    createdAt: params.createdAt ?? new Date().toISOString(),
    environment: params.environment ?? 'production',
  });
}

export function createCommandCapabilities(
  params: Partial<CommandCapabilities> = {},
): CommandCapabilities {
  return Object.freeze({
    supportsCommandExecution: params.supportsCommandExecution ?? true,
    supportsCommandValidation: params.supportsCommandValidation ?? true,
    supportsUndoRedo: params.supportsUndoRedo ?? true,
    supportsCommandHistory: params.supportsCommandHistory ?? true,
    supportsBatchExecution: params.supportsBatchExecution ?? true,
    supportsDiagnostics: params.supportsDiagnostics ?? true,
  });
}

export function createCommandHealth(params: Partial<CommandHealth> = {}): CommandHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    runtimeState: params.runtimeState ?? CommandRuntimeState.UNINITIALIZED,
    message: params.message ?? 'Command runtime is uninitialized.',
  });
}

export function createCommandStatistics(
  params: Partial<CommandStatistics> = {},
): CommandStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    errors: params.errors ?? 0,
    uptime: params.uptime ?? 0,
  });
}

export function createCommandConfiguration(
  params: Partial<CommandConfiguration> = {},
): CommandConfiguration {
  return Object.freeze({
    runtimeName: params.runtimeName ?? 'Auralis Command Runtime',
    version: params.version ?? '1.0.0',
    strictMode: params.strictMode ?? true,
    maxHistorySize: params.maxHistorySize ?? 1000,
    allowDuplicateNames: params.allowDuplicateNames ?? false,
  });
}

export function createCommandParameter(
  params: Partial<CommandParameter> & { name: string },
): CommandParameter {
  return Object.freeze({
    name: params.name,
    type: params.type ?? 'any',
    required: params.required ?? false,
    description: params.description,
    defaultValue: params.defaultValue,
  });
}

export function createCommandDefinition(
  params: Partial<CommandDefinition> & { id: string; displayName: string },
): CommandDefinition {
  return Object.freeze({
    id: params.id,
    displayName: params.displayName,
    description: params.description ?? '',
    category: params.category ?? 'General',
    aliases: Object.freeze([...(params.aliases ?? [])]),
    parameters: Object.freeze([...(params.parameters ?? [])]),
    examples: params.examples ? Object.freeze([...params.examples]) : undefined,
    version: params.version ?? '1.0.0',
    enabled: params.enabled ?? true,
    hidden: params.hidden ?? false,
    experimental: params.experimental ?? false,
    deprecated: params.deprecated ?? false,
    permission: params.permission,
    tags: params.tags ? Object.freeze([...params.tags]) : undefined,
  });
}

export function createCommandAlias(
  params: Partial<CommandAlias> & { alias: string; commandId: string },
): CommandAlias {
  return Object.freeze({
    alias: params.alias,
    commandId: params.commandId,
  });
}

export function createCommandCategory(
  params: Partial<CommandCategory> & { name: string },
): CommandCategory {
  return Object.freeze({
    name: params.name,
    description: params.description,
    commandCount: params.commandCount ?? 0,
  });
}

export function createCommandRegistration(
  params: Partial<CommandRegistration> & { id: string; displayName: string },
): CommandRegistration {
  return Object.freeze({
    id: params.id,
    displayName: params.displayName,
    description: params.description,
    category: params.category,
    aliases: params.aliases ? Object.freeze([...params.aliases]) : undefined,
    parameters: params.parameters ? Object.freeze([...params.parameters]) : undefined,
    examples: params.examples ? Object.freeze([...params.examples]) : undefined,
    version: params.version,
    enabled: params.enabled,
    hidden: params.hidden,
    experimental: params.experimental,
    deprecated: params.deprecated,
    permission: params.permission,
    tags: params.tags ? Object.freeze([...params.tags]) : undefined,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createCommandRegistryStatistics(
  params: Partial<CommandRegistryStatistics> = {},
): CommandRegistryStatistics {
  return Object.freeze({
    registeredCommands: params.registeredCommands ?? 0,
    removedCommands: params.removedCommands ?? 0,
    updates: params.updates ?? 0,
    lookups: params.lookups ?? 0,
    failedLookups: params.failedLookups ?? 0,
    searches: params.searches ?? 0,
    duplicateAttempts: params.duplicateAttempts ?? 0,
    categoryCount: params.categoryCount ?? 0,
    aliasCount: params.aliasCount ?? 0,
  });
}

export function createCommandRegistryHealth(
  params: Partial<CommandRegistryHealth> = {},
): CommandRegistryHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    duplicateIds: params.duplicateIds ?? 0,
    duplicateAliases: params.duplicateAliases ?? 0,
    missingMetadata: params.missingMetadata ?? 0,
    orphanCategories: params.orphanCategories ?? 0,
    invalidRegistrations: params.invalidRegistrations ?? 0,
    message: params.message ?? 'Command registry is operational.',
  });
}

export function createCommandDiagnostics(
  params: Partial<CommandDiagnostics> = {},
): CommandDiagnostics {
  return Object.freeze({
    health: params.health ?? createCommandHealth(),
    statistics: params.statistics ?? createCommandStatistics(),
    capabilities: params.capabilities ?? createCommandCapabilities(),
    context: params.context ?? createCommandContext(),
    registeredCommands: params.registeredCommands ? Object.freeze([...params.registeredCommands]) : undefined,
    registeredCategories: params.registeredCategories ? Object.freeze([...params.registeredCategories]) : undefined,
    registeredAliases: params.registeredAliases ? Object.freeze([...params.registeredAliases]) : undefined,
    registryStatistics: params.registryStatistics,
    registryHealth: params.registryHealth,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
