/**
 * Command Runtime Domain Models (Phase 16.6.4).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, command definitions,
 * parameters, registrations, categories, aliases, registry statistics, registry health,
 * execution requests, results, records, pipeline telemetry, execution statistics,
 * execution health, middleware models, interceptor models, pipeline execution telemetry,
 * pipeline statistics, pipeline health, and diagnostics telemetry for the Frontend Command Runtime.
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

export enum MiddlewarePriority {
  CRITICAL = 300,
  HIGH = 200,
  NORMAL = 100,
  LOW = 0,
}

export enum ExecutionStage {
  BEFORE = 'BEFORE',
  INTERCEPT = 'INTERCEPT',
  EXECUTE = 'EXECUTE',
  AFTER = 'AFTER',
  EXCEPTION = 'EXCEPTION',
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

export interface CommandMiddleware {
  readonly middlewareId: string;
  readonly name: string;
  readonly phase: 'BEFORE' | 'AFTER' | 'EXCEPTION';
  readonly priority: MiddlewarePriority;
  readonly enabled: boolean;
  readonly execute: (
    context: CommandExecutionContext,
    result?: CommandExecutionResult,
    error?: Error,
  ) => void | Promise<void>;
}

export interface MiddlewareExecution {
  readonly middlewareId: string;
  readonly name: string;
  readonly phase: 'BEFORE' | 'AFTER' | 'EXCEPTION';
  readonly success: boolean;
  readonly durationMs: number;
  readonly error?: string;
  readonly executedAt: string;
}

export interface MiddlewareResult {
  readonly executions: ReadonlyArray<MiddlewareExecution>;
  readonly totalExecutions: number;
  readonly successfulExecutions: number;
  readonly failedExecutions: number;
  readonly executedAt: string;
}

export interface MiddlewareStatistics {
  readonly totalRegistered: number;
  readonly beforeCount: number;
  readonly afterCount: number;
  readonly exceptionCount: number;
  readonly totalExecutions: number;
  readonly failedExecutions: number;
  readonly averageExecutionMs: number;
}

export interface MiddlewareHealth {
  readonly healthy: boolean;
  readonly activeMiddlewares: number;
  readonly failureRate: number;
  readonly message: string;
}

export type InterceptorHandler<TResult = unknown> = (
  context: CommandExecutionContext,
  next: () => Promise<CommandExecutionResult<TResult>>,
) => Promise<CommandExecutionResult<TResult>>;

export interface InterceptorRegistration<TResult = unknown> {
  readonly interceptorId: string;
  readonly name: string;
  readonly priority: MiddlewarePriority;
  readonly enabled: boolean;
  readonly intercept: InterceptorHandler<TResult>;
}

export interface InterceptorExecution {
  readonly interceptorId: string;
  readonly name: string;
  readonly success: boolean;
  readonly durationMs: number;
  readonly error?: string;
  readonly executedAt: string;
}

export interface InterceptorResult<TResult = unknown> {
  readonly executionResult: CommandExecutionResult<TResult>;
  readonly executions: ReadonlyArray<InterceptorExecution>;
  readonly totalInterceptors: number;
  readonly executedAt: string;
}

export interface PipelineExecution<TResult = unknown> {
  readonly pipelineId: string;
  readonly commandId: string;
  readonly executionResult: CommandExecutionResult<TResult>;
  readonly middlewareResult: MiddlewareResult;
  readonly interceptorResult?: InterceptorResult<TResult>;
  readonly durationMs: number;
  readonly executedAt: string;
}

export interface PipelineStatistics {
  readonly middlewareExecutions: number;
  readonly interceptorExecutions: number;
  readonly pipelineExecutions: number;
  readonly pipelineFailures: number;
  readonly averagePipelineTime: number;
  readonly maximumPipelineTime: number;
  readonly minimumPipelineTime: number;
  readonly activePipelines: number;
}

export interface PipelineHealth {
  readonly healthy: boolean;
  readonly failureRate: number;
  readonly averagePipelineTime: number;
  readonly registeredMiddleware: number;
  readonly registeredInterceptors: number;
  readonly pipelineThroughput: number;
  readonly message: string;
}

export interface PipelineConfiguration {
  readonly enableBeforeMiddleware: boolean;
  readonly enableAfterMiddleware: boolean;
  readonly enableExceptionMiddleware: boolean;
  readonly enableInterceptors: boolean;
  readonly pipelineTimeoutMs: number;
}

export interface PipelineCapabilities {
  readonly supportsBeforeMiddleware: boolean;
  readonly supportsAfterMiddleware: boolean;
  readonly supportsExceptionMiddleware: boolean;
  readonly supportsInterceptors: boolean;
  readonly supportsPriorityOrdering: boolean;
  readonly supportsContextEnrichment: boolean;
}

export interface PipelineDiagnostics {
  readonly statistics: PipelineStatistics;
  readonly health: PipelineHealth;
  readonly capabilities: PipelineCapabilities;
  readonly middlewareCount: number;
  readonly interceptorCount: number;
  readonly timestamp: string;
}

export interface PipelineSnapshot {
  readonly middleware: ReadonlyArray<CommandMiddleware>;
  readonly interceptors: ReadonlyArray<InterceptorRegistration>;
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
  readonly pipelineStatistics?: PipelineStatistics;
  readonly pipelineHealth?: PipelineHealth;
  readonly middlewareCount?: number;
  readonly interceptorCount?: number;
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
  const steps = params.steps ?? ['validation', 'before_middleware', 'interceptors', 'handler_execution', 'after_middleware', 'telemetry', 'history'];
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

export function createCommandMiddleware(
  params: Partial<CommandMiddleware> & {
    name: string;
    execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
  },
): CommandMiddleware {
  return Object.freeze({
    middlewareId: params.middlewareId ?? `mw_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    phase: params.phase ?? 'BEFORE',
    priority: params.priority ?? MiddlewarePriority.NORMAL,
    enabled: params.enabled ?? true,
    execute: params.execute,
  });
}

export function createMiddlewareExecution(
  params: Partial<MiddlewareExecution> & {
    middlewareId: string;
    name: string;
    phase: 'BEFORE' | 'AFTER' | 'EXCEPTION';
  },
): MiddlewareExecution {
  return Object.freeze({
    middlewareId: params.middlewareId,
    name: params.name,
    phase: params.phase,
    success: params.success ?? true,
    durationMs: params.durationMs ?? 0,
    error: params.error,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createMiddlewareResult(
  params: Partial<MiddlewareResult> = {},
): MiddlewareResult {
  const executions = params.executions ?? [];
  return Object.freeze({
    executions: Object.freeze([...executions]),
    totalExecutions: params.totalExecutions ?? executions.length,
    successfulExecutions: params.successfulExecutions ?? executions.filter((e) => e.success).length,
    failedExecutions: params.failedExecutions ?? executions.filter((e) => !e.success).length,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createMiddlewareStatistics(
  params: Partial<MiddlewareStatistics> = {},
): MiddlewareStatistics {
  return Object.freeze({
    totalRegistered: params.totalRegistered ?? 0,
    beforeCount: params.beforeCount ?? 0,
    afterCount: params.afterCount ?? 0,
    exceptionCount: params.exceptionCount ?? 0,
    totalExecutions: params.totalExecutions ?? 0,
    failedExecutions: params.failedExecutions ?? 0,
    averageExecutionMs: params.averageExecutionMs ?? 0,
  });
}

export function createMiddlewareHealth(
  params: Partial<MiddlewareHealth> = {},
): MiddlewareHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeMiddlewares: params.activeMiddlewares ?? 0,
    failureRate: params.failureRate ?? 0,
    message: params.message ?? 'Middleware manager is operational.',
  });
}

export function createInterceptorRegistration<TResult = unknown>(
  params: Partial<InterceptorRegistration<TResult>> & {
    name: string;
    intercept: InterceptorHandler<TResult>;
  },
): InterceptorRegistration<TResult> {
  return Object.freeze({
    interceptorId: params.interceptorId ?? `int_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    priority: params.priority ?? MiddlewarePriority.NORMAL,
    enabled: params.enabled ?? true,
    intercept: params.intercept,
  });
}

export function createInterceptorExecution(
  params: Partial<InterceptorExecution> & { interceptorId: string; name: string },
): InterceptorExecution {
  return Object.freeze({
    interceptorId: params.interceptorId,
    name: params.name,
    success: params.success ?? true,
    durationMs: params.durationMs ?? 0,
    error: params.error,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createInterceptorResult<TResult = unknown>(
  params: Partial<InterceptorResult<TResult>> & { executionResult: CommandExecutionResult<TResult> },
): InterceptorResult<TResult> {
  const executions = params.executions ?? [];
  return Object.freeze({
    executionResult: params.executionResult,
    executions: Object.freeze([...executions]),
    totalInterceptors: params.totalInterceptors ?? executions.length,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createPipelineExecution<TResult = unknown>(
  params: Partial<PipelineExecution<TResult>> & {
    commandId: string;
    executionResult: CommandExecutionResult<TResult>;
    middlewareResult: MiddlewareResult;
  },
): PipelineExecution<TResult> {
  return Object.freeze({
    pipelineId: params.pipelineId ?? `pipe_exec_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    commandId: params.commandId,
    executionResult: params.executionResult,
    middlewareResult: params.middlewareResult,
    interceptorResult: params.interceptorResult,
    durationMs: params.durationMs ?? 0,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createPipelineStatistics(
  params: Partial<PipelineStatistics> = {},
): PipelineStatistics {
  return Object.freeze({
    middlewareExecutions: params.middlewareExecutions ?? 0,
    interceptorExecutions: params.interceptorExecutions ?? 0,
    pipelineExecutions: params.pipelineExecutions ?? 0,
    pipelineFailures: params.pipelineFailures ?? 0,
    averagePipelineTime: params.averagePipelineTime ?? 0,
    maximumPipelineTime: params.maximumPipelineTime ?? 0,
    minimumPipelineTime: params.minimumPipelineTime ?? 0,
    activePipelines: params.activePipelines ?? 0,
  });
}

export function createPipelineHealth(
  params: Partial<PipelineHealth> = {},
): PipelineHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    failureRate: params.failureRate ?? 0,
    averagePipelineTime: params.averagePipelineTime ?? 0,
    registeredMiddleware: params.registeredMiddleware ?? 0,
    registeredInterceptors: params.registeredInterceptors ?? 0,
    pipelineThroughput: params.pipelineThroughput ?? 0,
    message: params.message ?? 'Command pipeline engine is operational.',
  });
}

export function createPipelineConfiguration(
  params: Partial<PipelineConfiguration> = {},
): PipelineConfiguration {
  return Object.freeze({
    enableBeforeMiddleware: params.enableBeforeMiddleware ?? true,
    enableAfterMiddleware: params.enableAfterMiddleware ?? true,
    enableExceptionMiddleware: params.enableExceptionMiddleware ?? true,
    enableInterceptors: params.enableInterceptors ?? true,
    pipelineTimeoutMs: params.pipelineTimeoutMs ?? 30000,
  });
}

export function createPipelineCapabilities(
  params: Partial<PipelineCapabilities> = {},
): PipelineCapabilities {
  return Object.freeze({
    supportsBeforeMiddleware: params.supportsBeforeMiddleware ?? true,
    supportsAfterMiddleware: params.supportsAfterMiddleware ?? true,
    supportsExceptionMiddleware: params.supportsExceptionMiddleware ?? true,
    supportsInterceptors: params.supportsInterceptors ?? true,
    supportsPriorityOrdering: params.supportsPriorityOrdering ?? true,
    supportsContextEnrichment: params.supportsContextEnrichment ?? true,
  });
}

export function createPipelineDiagnostics(
  params: Partial<PipelineDiagnostics> & {
    statistics: PipelineStatistics;
    health: PipelineHealth;
  },
): PipelineDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    capabilities: params.capabilities ?? createPipelineCapabilities(),
    middlewareCount: params.middlewareCount ?? 0,
    interceptorCount: params.interceptorCount ?? 0,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createPipelineSnapshot(
  params: Partial<PipelineSnapshot> = {},
): PipelineSnapshot {
  return Object.freeze({
    middleware: Object.freeze([...(params.middleware ?? [])]),
    interceptors: Object.freeze([...(params.interceptors ?? [])]),
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
    pipelineStatistics: params.pipelineStatistics,
    pipelineHealth: params.pipelineHealth,
    middlewareCount: params.middlewareCount,
    interceptorCount: params.interceptorCount,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
