/**
 * Command Runtime Domain Models (Phase 16.6.3).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, command definitions,
 * parameters, registrations, categories, aliases, registry statistics, registry health,
 * execution requests, results, records, pipeline telemetry, execution statistics,
 * execution health, and diagnostics telemetry for the Frontend Command Runtime.
 */

export enum CommandRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export enum CommandExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
  FAILED = 'FAILED',
  TIMED_OUT = 'TIMED_OUT',
  REJECTED = 'REJECTED',
  VALIDATION_FAILED = 'VALIDATION_FAILED',
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

export interface ExecutionTiming {
  readonly startTime: string;
  readonly endTime?: string;
  readonly durationMs: number;
}

export interface ExecutionError {
  readonly code: string;
  readonly message: string;
  readonly stack?: string;
  readonly details?: Readonly<Record<string, unknown>>;
}

export interface ExecutionWarning {
  readonly code: string;
  readonly message: string;
  readonly timestamp: string;
}

export interface CommandExecutionContext {
  readonly executionId: string;
  readonly commandId: string;
  readonly timestamp: string;
  readonly userId?: string;
  readonly sessionId?: string;
  readonly correlationId?: string;
  readonly environment: string;
  readonly source: string;
  readonly mode: 'sync' | 'async';
  readonly args: Readonly<Record<string, unknown>>;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface CommandExecutionRequest {
  readonly commandId: string;
  readonly args?: Readonly<Record<string, unknown>>;
  readonly userId?: string;
  readonly sessionId?: string;
  readonly correlationId?: string;
  readonly source?: string;
  readonly metadata?: Readonly<Record<string, unknown>>;
}

export interface CommandExecutionResult<TResult = unknown> {
  readonly executionId: string;
  readonly commandId: string;
  readonly status: CommandExecutionStatus;
  readonly value?: TResult;
  readonly error?: ExecutionError;
  readonly warnings: ReadonlyArray<ExecutionWarning>;
  readonly timing: ExecutionTiming;
  readonly context: CommandExecutionContext;
}

export interface CommandExecutionRecord<TResult = unknown> {
  readonly result: CommandExecutionResult<TResult>;
  readonly recordedAt: string;
}

export interface CommandExecutionStatistics {
  readonly executions: number;
  readonly successfulExecutions: number;
  readonly failedExecutions: number;
  readonly cancelledExecutions: number;
  readonly validationFailures: number;
  readonly averageExecutionTime: number;
  readonly maximumExecutionTime: number;
  readonly minimumExecutionTime: number;
  readonly historySize: number;
  readonly activeExecutions: number;
}

export interface CommandExecutionHealth {
  readonly healthy: boolean;
  readonly failureRate: number;
  readonly successRate: number;
  readonly averageExecutionTime: number;
  readonly historyCapacity: number;
  readonly activeExecutions: number;
  readonly validationFailures: number;
  readonly executionThroughput: number;
  readonly message: string;
}

export interface CommandExecutionConfiguration {
  readonly maxHistorySize: number;
  readonly executionTimeoutMs: number;
  readonly strictParameterValidation: boolean;
}

export interface ExecutionPipeline {
  readonly pipelineId: string;
  readonly steps: ReadonlyArray<string>;
  readonly createdAt: string;
}

export interface ExecutionCapabilities {
  readonly supportsSyncExecution: boolean;
  readonly supportsAsyncExecution: boolean;
  readonly supportsCancellation: boolean;
  readonly supportsHistoryTracking: boolean;
  readonly supportsParameterValidation: boolean;
}

export interface ExecutionDiagnostics {
  readonly statistics: CommandExecutionStatistics;
  readonly health: CommandExecutionHealth;
  readonly capabilities: ExecutionCapabilities;
  readonly historySize: number;
  readonly activeExecutions: number;
  readonly timestamp: string;
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
  readonly executionStatistics?: CommandExecutionStatistics;
  readonly executionHealth?: CommandExecutionHealth;
  readonly executionHistorySize?: number;
  readonly timestamp: string;
}

export type CommandHandler<TArgs = Record<string, unknown>, TResult = unknown> = (
  args: TArgs,
  context: CommandExecutionContext,
) => TResult | Promise<TResult>;

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

export function createExecutionTiming(params: Partial<ExecutionTiming> = {}): ExecutionTiming {
  return Object.freeze({
    startTime: params.startTime ?? new Date().toISOString(),
    endTime: params.endTime,
    durationMs: params.durationMs ?? 0,
  });
}

export function createExecutionError(
  params: Partial<ExecutionError> & { message: string },
): ExecutionError {
  return Object.freeze({
    code: params.code ?? 'COMMAND_EXECUTION_ERROR',
    message: params.message,
    stack: params.stack,
    details: params.details ? Object.freeze({ ...params.details }) : undefined,
  });
}

export function createExecutionWarning(
  params: Partial<ExecutionWarning> & { message: string },
): ExecutionWarning {
  return Object.freeze({
    code: params.code ?? 'COMMAND_EXECUTION_WARNING',
    message: params.message,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createCommandExecutionContext(
  params: Partial<CommandExecutionContext> & { commandId: string },
): CommandExecutionContext {
  return Object.freeze({
    executionId: params.executionId ?? `exec_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    commandId: params.commandId,
    timestamp: params.timestamp ?? new Date().toISOString(),
    userId: params.userId,
    sessionId: params.sessionId,
    correlationId: params.correlationId,
    environment: params.environment ?? 'production',
    source: params.source ?? 'runtime',
    mode: params.mode ?? 'sync',
    args: Object.freeze({ ...(params.args ?? {}) }),
    metadata: params.metadata ? Object.freeze({ ...params.metadata }) : undefined,
  });
}

export function createCommandExecutionRequest(
  params: Partial<CommandExecutionRequest> & { commandId: string },
): CommandExecutionRequest {
  return Object.freeze({
    commandId: params.commandId,
    args: params.args ? Object.freeze({ ...params.args }) : Object.freeze({}),
    userId: params.userId,
    sessionId: params.sessionId,
    correlationId: params.correlationId,
    source: params.source,
    metadata: params.metadata ? Object.freeze({ ...params.metadata }) : undefined,
  });
}

export function createCommandExecutionResult<TResult = unknown>(
  params: Partial<CommandExecutionResult<TResult>> & { commandId: string; context: CommandExecutionContext },
): CommandExecutionResult<TResult> {
  const warnings = params.warnings ?? [];
  return Object.freeze({
    executionId: params.executionId ?? params.context.executionId,
    commandId: params.commandId,
    status: params.status ?? CommandExecutionStatus.COMPLETED,
    value: params.value,
    error: params.error,
    warnings: Object.freeze([...warnings]),
    timing: params.timing ?? createExecutionTiming(),
    context: params.context,
  });
}

export function createCommandExecutionRecord<TResult = unknown>(
  params: Partial<CommandExecutionRecord<TResult>> & { result: CommandExecutionResult<TResult> },
): CommandExecutionRecord<TResult> {
  return Object.freeze({
    result: params.result,
    recordedAt: params.recordedAt ?? new Date().toISOString(),
  });
}

export function createCommandExecutionStatistics(
  params: Partial<CommandExecutionStatistics> = {},
): CommandExecutionStatistics {
  return Object.freeze({
    executions: params.executions ?? 0,
    successfulExecutions: params.successfulExecutions ?? 0,
    failedExecutions: params.failedExecutions ?? 0,
    cancelledExecutions: params.cancelledExecutions ?? 0,
    validationFailures: params.validationFailures ?? 0,
    averageExecutionTime: params.averageExecutionTime ?? 0,
    maximumExecutionTime: params.maximumExecutionTime ?? 0,
    minimumExecutionTime: params.minimumExecutionTime ?? 0,
    historySize: params.historySize ?? 0,
    activeExecutions: params.activeExecutions ?? 0,
  });
}

export function createCommandExecutionHealth(
  params: Partial<CommandExecutionHealth> = {},
): CommandExecutionHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    failureRate: params.failureRate ?? 0,
    successRate: params.successRate ?? 100,
    averageExecutionTime: params.averageExecutionTime ?? 0,
    historyCapacity: params.historyCapacity ?? 1000,
    activeExecutions: params.activeExecutions ?? 0,
    validationFailures: params.validationFailures ?? 0,
    executionThroughput: params.executionThroughput ?? 0,
    message: params.message ?? 'Command execution engine is operational.',
  });
}

export function createCommandExecutionConfiguration(
  params: Partial<CommandExecutionConfiguration> = {},
): CommandExecutionConfiguration {
  return Object.freeze({
    maxHistorySize: params.maxHistorySize ?? 1000,
    executionTimeoutMs: params.executionTimeoutMs ?? 30000,
    strictParameterValidation: params.strictParameterValidation ?? true,
  });
}

export function createExecutionPipeline(
  params: Partial<ExecutionPipeline> = {},
): ExecutionPipeline {
  const steps = params.steps ?? ['validation', 'lookup', 'parameter_validation', 'context_creation', 'handler_execution', 'telemetry', 'history'];
  return Object.freeze({
    pipelineId: params.pipelineId ?? `pipe_${Date.now()}`,
    steps: Object.freeze([...steps]),
    createdAt: params.createdAt ?? new Date().toISOString(),
  });
}

export function createExecutionCapabilities(
  params: Partial<ExecutionCapabilities> = {},
): ExecutionCapabilities {
  return Object.freeze({
    supportsSyncExecution: params.supportsSyncExecution ?? true,
    supportsAsyncExecution: params.supportsAsyncExecution ?? true,
    supportsCancellation: params.supportsCancellation ?? true,
    supportsHistoryTracking: params.supportsHistoryTracking ?? true,
    supportsParameterValidation: params.supportsParameterValidation ?? true,
  });
}

export function createExecutionDiagnostics(
  params: Partial<ExecutionDiagnostics> & {
    statistics: CommandExecutionStatistics;
    health: CommandExecutionHealth;
  },
): ExecutionDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    capabilities: params.capabilities ?? createExecutionCapabilities(),
    historySize: params.historySize ?? params.statistics.historySize,
    activeExecutions: params.activeExecutions ?? params.statistics.activeExecutions,
    timestamp: params.timestamp ?? new Date().toISOString(),
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
    executionStatistics: params.executionStatistics,
    executionHealth: params.executionHealth,
    executionHistorySize: params.executionHistorySize,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
