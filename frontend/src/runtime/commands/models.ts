/**
 * Command Runtime Domain Models (Phase 16.6.5).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, command definitions,
 * parameters, registrations, categories, aliases, registry statistics, registry health,
 * execution requests, results, records, pipeline telemetry, execution statistics,
 * execution health, middleware models, interceptor models, pipeline execution telemetry,
 * pipeline statistics, pipeline health, validation rules, validation issues, validation results,
 * validation telemetry, permission scopes, permissions, permission evaluation results,
 * permission telemetry, policy rules, execution policies, policy decisions, policy telemetry,
 * and diagnostics telemetry for the Frontend Command Runtime.
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

export type PermissionScope = 'global' | 'workspace' | 'session' | 'user';

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

export interface CommandPermission {
  readonly permissionId: string;
  readonly name: string;
  readonly description?: string;
  readonly scope: PermissionScope;
  readonly roles: ReadonlyArray<string>;
  readonly enabled: boolean;
}

export interface PermissionResult {
  readonly granted: boolean;
  readonly permissionId?: string;
  readonly userId?: string;
  readonly reason?: string;
  readonly evaluatedAt: string;
}

export interface PermissionStatistics {
  readonly totalChecks: number;
  readonly grantedChecks: number;
  readonly deniedChecks: number;
  readonly activePermissions: number;
}

export interface PermissionHealth {
  readonly healthy: boolean;
  readonly grantedRate: number;
  readonly activePermissions: number;
  readonly message: string;
}

export interface ValidationIssue {
  readonly severity: 'error' | 'warning';
  readonly code: string;
  readonly message: string;
  readonly field?: string;
}

export interface ValidationRule {
  readonly ruleId: string;
  readonly name: string;
  readonly description?: string;
  readonly validate: (
    request: CommandExecutionRequest,
    definition?: CommandDefinition,
  ) => ValidationIssue | undefined | null | Promise<ValidationIssue | undefined | null>;
}

export interface ValidationResult {
  readonly valid: boolean;
  readonly commandId: string;
  readonly issues: ReadonlyArray<ValidationIssue>;
  readonly validatedAt: string;
}

export interface ValidationStatistics {
  readonly totalValidations: number;
  readonly successfulValidations: number;
  readonly failedValidations: number;
  readonly warningCount: number;
  readonly averageValidationMs: number;
}

export interface ValidationHealth {
  readonly healthy: boolean;
  readonly failureRate: number;
  readonly averageValidationMs: number;
  readonly message: string;
}

export interface PolicyRule {
  readonly ruleId: string;
  readonly name: string;
  readonly policyId: string;
  readonly condition: (
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ) => boolean | Promise<boolean>;
}

export interface ExecutionPolicy {
  readonly policyId: string;
  readonly name: string;
  readonly description?: string;
  readonly enabled: boolean;
  readonly evaluate: (
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ) => PolicyDecision | Promise<PolicyDecision>;
}

export interface PolicyDecision {
  readonly allowed: boolean;
  readonly policyId?: string;
  readonly reason?: string;
  readonly evaluatedAt: string;
}

export interface PolicyStatistics {
  readonly totalEvaluations: number;
  readonly allowedEvaluations: number;
  readonly deniedEvaluations: number;
  readonly averageEvaluationMs: number;
}

export interface PolicyHealth {
  readonly healthy: boolean;
  readonly allowedRate: number;
  readonly activePolicies: number;
  readonly message: string;
}

export interface ValidationDiagnostics {
  readonly statistics: ValidationStatistics;
  readonly health: ValidationHealth;
  readonly ruleCount: number;
  readonly timestamp: string;
}

export interface PermissionDiagnostics {
  readonly statistics: PermissionStatistics;
  readonly health: PermissionHealth;
  readonly permissionCount: number;
  readonly timestamp: string;
}

export interface PolicyDiagnostics {
  readonly statistics: PolicyStatistics;
  readonly health: PolicyHealth;
  readonly policyCount: number;
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
  readonly validationDiagnostics?: ValidationDiagnostics;
  readonly permissionDiagnostics?: PermissionDiagnostics;
  readonly policyDiagnostics?: PolicyDiagnostics;
  readonly schedulingDiagnostics?: SchedulingDiagnostics;
  readonly queueDiagnostics?: QueueDiagnostics;
  readonly backgroundDiagnostics?: BackgroundDiagnostics;
  readonly certification?: CommandCertification;
  readonly certificationSummary?: CommandCertificationSummary;
  readonly certificationStatistics?: CertificationStatistics;
  readonly certificationHealth?: CertificationHealth;
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

export function createCommandPermission(
  params: Partial<CommandPermission> & { name: string },
): CommandPermission {
  const roles = params.roles ?? [];
  return Object.freeze({
    permissionId: params.permissionId ?? `perm_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    description: params.description,
    scope: params.scope ?? 'global',
    roles: Object.freeze([...roles]),
    enabled: params.enabled ?? true,
  });
}

export function createPermissionResult(
  params: Partial<PermissionResult> = {},
): PermissionResult {
  return Object.freeze({
    granted: params.granted ?? true,
    permissionId: params.permissionId,
    userId: params.userId,
    reason: params.reason,
    evaluatedAt: params.evaluatedAt ?? new Date().toISOString(),
  });
}

export function createPermissionStatistics(
  params: Partial<PermissionStatistics> = {},
): PermissionStatistics {
  return Object.freeze({
    totalChecks: params.totalChecks ?? 0,
    grantedChecks: params.grantedChecks ?? 0,
    deniedChecks: params.deniedChecks ?? 0,
    activePermissions: params.activePermissions ?? 0,
  });
}

export function createPermissionHealth(
  params: Partial<PermissionHealth> = {},
): PermissionHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    grantedRate: params.grantedRate ?? 100,
    activePermissions: params.activePermissions ?? 0,
    message: params.message ?? 'Permission manager is operational.',
  });
}

export function createValidationIssue(
  params: Partial<ValidationIssue> & { message: string },
): ValidationIssue {
  return Object.freeze({
    severity: params.severity ?? 'error',
    code: params.code ?? 'VALIDATION_ERROR',
    message: params.message,
    field: params.field,
  });
}

export function createValidationRule(
  params: Partial<ValidationRule> & {
    name: string;
    validate: (request: CommandExecutionRequest, definition?: CommandDefinition) => ValidationIssue | undefined | null | Promise<ValidationIssue | undefined | null>;
  },
): ValidationRule {
  return Object.freeze({
    ruleId: params.ruleId ?? `vrule_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    description: params.description,
    validate: params.validate,
  });
}

export function createValidationResult(
  params: Partial<ValidationResult> & { commandId: string },
): ValidationResult {
  const issues = params.issues ?? [];
  return Object.freeze({
    valid: params.valid ?? issues.every((i) => i.severity !== 'error'),
    commandId: params.commandId,
    issues: Object.freeze([...issues]),
    validatedAt: params.validatedAt ?? new Date().toISOString(),
  });
}

export function createValidationStatistics(
  params: Partial<ValidationStatistics> = {},
): ValidationStatistics {
  return Object.freeze({
    totalValidations: params.totalValidations ?? 0,
    successfulValidations: params.successfulValidations ?? 0,
    failedValidations: params.failedValidations ?? 0,
    warningCount: params.warningCount ?? 0,
    averageValidationMs: params.averageValidationMs ?? 0,
  });
}

export function createValidationHealth(
  params: Partial<ValidationHealth> = {},
): ValidationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    failureRate: params.failureRate ?? 0,
    averageValidationMs: params.averageValidationMs ?? 0,
    message: params.message ?? 'Command validator is operational.',
  });
}

export function createPolicyRule(
  params: Partial<PolicyRule> & {
    name: string;
    policyId: string;
    condition: (request: CommandExecutionRequest, context?: CommandExecutionContext) => boolean | Promise<boolean>;
  },
): PolicyRule {
  return Object.freeze({
    ruleId: params.ruleId ?? `prule_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    policyId: params.policyId,
    condition: params.condition,
  });
}

export function createExecutionPolicy(
  params: Partial<ExecutionPolicy> & {
    name: string;
    evaluate: (request: CommandExecutionRequest, context?: CommandExecutionContext) => PolicyDecision | Promise<PolicyDecision>;
  },
): ExecutionPolicy {
  return Object.freeze({
    policyId: params.policyId ?? `policy_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    description: params.description,
    enabled: params.enabled ?? true,
    evaluate: params.evaluate,
  });
}

export function createPolicyDecision(
  params: Partial<PolicyDecision> = {},
): PolicyDecision {
  return Object.freeze({
    allowed: params.allowed ?? true,
    policyId: params.policyId,
    reason: params.reason,
    evaluatedAt: params.evaluatedAt ?? new Date().toISOString(),
  });
}

export function createPolicyStatistics(
  params: Partial<PolicyStatistics> = {},
): PolicyStatistics {
  return Object.freeze({
    totalEvaluations: params.totalEvaluations ?? 0,
    allowedEvaluations: params.allowedEvaluations ?? 0,
    deniedEvaluations: params.deniedEvaluations ?? 0,
    averageEvaluationMs: params.averageEvaluationMs ?? 0,
  });
}

export function createPolicyHealth(
  params: Partial<PolicyHealth> = {},
): PolicyHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    allowedRate: params.allowedRate ?? 100,
    activePolicies: params.activePolicies ?? 0,
    message: params.message ?? 'Policy manager is operational.',
  });
}

export function createValidationDiagnostics(
  params: Partial<ValidationDiagnostics> & {
    statistics: ValidationStatistics;
    health: ValidationHealth;
  },
): ValidationDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    ruleCount: params.ruleCount ?? 0,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createPermissionDiagnostics(
  params: Partial<PermissionDiagnostics> & {
    statistics: PermissionStatistics;
    health: PermissionHealth;
  },
): PermissionDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    permissionCount: params.permissionCount ?? 0,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createPolicyDiagnostics(
  params: Partial<PolicyDiagnostics> & {
    statistics: PolicyStatistics;
    health: PolicyHealth;
  },
): PolicyDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    policyCount: params.policyCount ?? 0,
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
    validationDiagnostics: params.validationDiagnostics,
    permissionDiagnostics: params.permissionDiagnostics,
    policyDiagnostics: params.policyDiagnostics,
    schedulingDiagnostics: params.schedulingDiagnostics,
    queueDiagnostics: params.queueDiagnostics,
    backgroundDiagnostics: params.backgroundDiagnostics,
    certification: params.certification,
    certificationSummary: params.certificationSummary,
    certificationStatistics: params.certificationStatistics,
    certificationHealth: params.certificationHealth,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export type ScheduleType = 'immediate' | 'delayed' | 'timestamp' | 'interval' | 'cron';

export interface RetrySchedule {
  readonly maxRetries: number;
  readonly delayMs: number;
  readonly backoffFactor?: number;
}

export interface ExecutionWindow {
  readonly startHour: number; // 0-23
  readonly endHour: number;   // 0-23
  readonly daysOfWeek?: ReadonlyArray<number>; // 0 (Sunday) to 6 (Saturday)
}

export interface CommandSchedule {
  readonly scheduleId: string;
  readonly type: ScheduleType;
  readonly delayMs?: number;
  readonly timestamp?: string;
  readonly intervalMs?: number;
  readonly cronExpression?: string;
  readonly retrySchedule?: RetrySchedule;
  readonly executionWindow?: ExecutionWindow;
}

export interface ScheduledCommand {
  readonly scheduleId: string;
  readonly request: CommandExecutionRequest;
  readonly schedule: CommandSchedule;
  readonly status: 'pending' | 'running' | 'completed' | 'cancelled' | 'failed';
  readonly nextRunTime: string | null;
  readonly lastRunTime: string | null;
  readonly runCount: number;
  readonly errorCount: number;
}

export interface ScheduledExecution {
  readonly executionId: string;
  readonly scheduleId: string;
  readonly commandId: string;
  readonly status: CommandExecutionStatus;
  readonly executedAt: string;
  readonly durationMs: number;
  readonly error?: string;
}

export interface ScheduleStatistics {
  readonly totalScheduled: number;
  readonly activeSchedules: number;
  readonly executedSchedules: number;
  readonly cancelledSchedules: number;
  readonly recurringSchedules: number;
  readonly averageScheduleDelayMs: number;
}

export interface ScheduleHealth {
  readonly healthy: boolean;
  readonly activeSchedules: number;
  readonly failureRate: number;
  readonly message: string;
}

export interface QueueEntry {
  readonly queueId: string;
  readonly request: CommandExecutionRequest;
  readonly priority: number;
  readonly enqueuedAt: string;
  readonly delayMs?: number;
}

export interface QueueStatistics {
  readonly totalInsertions: number;
  readonly totalRemovals: number;
  readonly currentSize: number;
  readonly capacity: number;
  readonly peakSize: number;
  readonly averageQueueTimeMs: number;
}

export interface QueueHealth {
  readonly healthy: boolean;
  readonly occupancyRate: number;
  readonly message: string;
}

export interface BackgroundTask {
  readonly taskId: string;
  readonly commandId: string;
  readonly request: CommandExecutionRequest;
  readonly status: 'pending' | 'running' | 'completed' | 'cancelled' | 'failed';
  readonly submittedAt: string;
  readonly startedAt: string | null;
  readonly completedAt: string | null;
  readonly durationMs: number;
  readonly retries: number;
  readonly maxRetries: number;
  readonly error?: string;
}

export interface BackgroundExecution {
  readonly taskId: string;
  readonly result: CommandExecutionResult;
  readonly durationMs: number;
  readonly executedAt: string;
}

export interface BackgroundStatistics {
  readonly totalSubmitted: number;
  readonly activeTasks: number;
  readonly completedTasks: number;
  readonly failedTasks: number;
  readonly cancelledTasks: number;
  readonly retryAttempts: number;
}

export interface BackgroundHealth {
  readonly healthy: boolean;
  readonly activeTasks: number;
  readonly failureRate: number;
  readonly message: string;
}

export interface SchedulingConfiguration {
  readonly maxQueueSize: number;
  readonly enableBackgroundExecution: boolean;
  readonly checkIntervalMs: number;
  readonly defaultPriority: number;
}

export interface SchedulingDiagnostics {
  readonly statistics: ScheduleStatistics;
  readonly health: ScheduleHealth;
  readonly activeSchedulesCount: number;
  readonly timestamp: string;
}

export interface QueueDiagnostics {
  readonly statistics: QueueStatistics;
  readonly health: QueueHealth;
  readonly currentSize: number;
  readonly timestamp: string;
}

export interface BackgroundDiagnostics {
  readonly statistics: BackgroundStatistics;
  readonly health: BackgroundHealth;
  readonly activeTasksCount: number;
  readonly timestamp: string;
}

export function createRetrySchedule(params: Partial<RetrySchedule> = {}): RetrySchedule {
  return Object.freeze({
    maxRetries: params.maxRetries ?? 3,
    delayMs: params.delayMs ?? 1000,
    backoffFactor: params.backoffFactor ?? 2,
  });
}

export function createExecutionWindow(params: Partial<ExecutionWindow> = {}): ExecutionWindow {
  return Object.freeze({
    startHour: params.startHour ?? 0,
    endHour: params.endHour ?? 23,
    daysOfWeek: params.daysOfWeek ? Object.freeze([...params.daysOfWeek]) : undefined,
  });
}

export function createCommandSchedule(params: Partial<CommandSchedule> = {}): CommandSchedule {
  return Object.freeze({
    scheduleId: params.scheduleId ?? `sched_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    type: params.type ?? 'immediate',
    delayMs: params.delayMs,
    timestamp: params.timestamp,
    intervalMs: params.intervalMs,
    cronExpression: params.cronExpression,
    retrySchedule: params.retrySchedule ? createRetrySchedule(params.retrySchedule) : undefined,
    executionWindow: params.executionWindow ? createExecutionWindow(params.executionWindow) : undefined,
  });
}

export function createScheduledCommand(
  params: Partial<ScheduledCommand> & { request: CommandExecutionRequest; schedule: CommandSchedule },
): ScheduledCommand {
  return Object.freeze({
    scheduleId: params.scheduleId ?? params.schedule.scheduleId,
    request: params.request,
    schedule: params.schedule,
    status: params.status ?? 'pending',
    nextRunTime: params.nextRunTime ?? null,
    lastRunTime: params.lastRunTime ?? null,
    runCount: params.runCount ?? 0,
    errorCount: params.errorCount ?? 0,
  });
}

export function createScheduledExecution(
  params: Partial<ScheduledExecution> & { scheduleId: string; commandId: string },
): ScheduledExecution {
  return Object.freeze({
    executionId: params.executionId ?? `schex_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    scheduleId: params.scheduleId,
    commandId: params.commandId,
    status: params.status ?? CommandExecutionStatus.PENDING,
    executedAt: params.executedAt ?? new Date().toISOString(),
    durationMs: params.durationMs ?? 0,
    error: params.error,
  });
}

export function createScheduleStatistics(params: Partial<ScheduleStatistics> = {}): ScheduleStatistics {
  return Object.freeze({
    totalScheduled: params.totalScheduled ?? 0,
    activeSchedules: params.activeSchedules ?? 0,
    executedSchedules: params.executedSchedules ?? 0,
    cancelledSchedules: params.cancelledSchedules ?? 0,
    recurringSchedules: params.recurringSchedules ?? 0,
    averageScheduleDelayMs: params.averageScheduleDelayMs ?? 0,
  });
}

export function createScheduleHealth(params: Partial<ScheduleHealth> = {}): ScheduleHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeSchedules: params.activeSchedules ?? 0,
    failureRate: params.failureRate ?? 0,
    message: params.message ?? 'Command scheduler is operational.',
  });
}

export function createQueueEntry(
  params: Partial<QueueEntry> & { request: CommandExecutionRequest },
): QueueEntry {
  return Object.freeze({
    queueId: params.queueId ?? `q_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    request: params.request,
    priority: params.priority ?? 0,
    enqueuedAt: params.enqueuedAt ?? new Date().toISOString(),
    delayMs: params.delayMs,
  });
}

export function createQueueStatistics(params: Partial<QueueStatistics> = {}): QueueStatistics {
  return Object.freeze({
    totalInsertions: params.totalInsertions ?? 0,
    totalRemovals: params.totalRemovals ?? 0,
    currentSize: params.currentSize ?? 0,
    capacity: params.capacity ?? 1000,
    peakSize: params.peakSize ?? 0,
    averageQueueTimeMs: params.averageQueueTimeMs ?? 0,
  });
}

export function createQueueHealth(params: Partial<QueueHealth> = {}): QueueHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    occupancyRate: params.occupancyRate ?? 0,
    message: params.message ?? 'Command queue is operational.',
  });
}

export function createBackgroundTask(
  params: Partial<BackgroundTask> & { commandId: string; request: CommandExecutionRequest },
): BackgroundTask {
  return Object.freeze({
    taskId: params.taskId ?? `bg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    commandId: params.commandId,
    request: params.request,
    status: params.status ?? 'pending',
    submittedAt: params.submittedAt ?? new Date().toISOString(),
    startedAt: params.startedAt ?? null,
    completedAt: params.completedAt ?? null,
    durationMs: params.durationMs ?? 0,
    retries: params.retries ?? 0,
    maxRetries: params.maxRetries ?? 3,
    error: params.error,
  });
}

export function createBackgroundExecution(
  params: Partial<BackgroundExecution> & { taskId: string; result: CommandExecutionResult },
): BackgroundExecution {
  return Object.freeze({
    taskId: params.taskId,
    result: params.result,
    durationMs: params.durationMs ?? 0,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createBackgroundStatistics(params: Partial<BackgroundStatistics> = {}): BackgroundStatistics {
  return Object.freeze({
    totalSubmitted: params.totalSubmitted ?? 0,
    activeTasks: params.activeTasks ?? 0,
    completedTasks: params.completedTasks ?? 0,
    failedTasks: params.failedTasks ?? 0,
    cancelledTasks: params.cancelledTasks ?? 0,
    retryAttempts: params.retryAttempts ?? 0,
  });
}

export function createBackgroundHealth(params: Partial<BackgroundHealth> = {}): BackgroundHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeTasks: params.activeTasks ?? 0,
    failureRate: params.failureRate ?? 0,
    message: params.message ?? 'Background execution manager is operational.',
  });
}

export function createSchedulingConfiguration(params: Partial<SchedulingConfiguration> = {}): SchedulingConfiguration {
  return Object.freeze({
    maxQueueSize: params.maxQueueSize ?? 1000,
    enableBackgroundExecution: params.enableBackgroundExecution ?? true,
    checkIntervalMs: params.checkIntervalMs ?? 1000,
    defaultPriority: params.defaultPriority ?? 0,
  });
}

export function createSchedulingDiagnostics(
  params: Partial<SchedulingDiagnostics> & { statistics: ScheduleStatistics; health: ScheduleHealth },
): SchedulingDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    activeSchedulesCount: params.activeSchedulesCount ?? params.statistics.activeSchedules,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createQueueDiagnostics(
  params: Partial<QueueDiagnostics> & { statistics: QueueStatistics; health: QueueHealth },
): QueueDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    currentSize: params.currentSize ?? params.statistics.currentSize,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createBackgroundDiagnostics(
  params: Partial<BackgroundDiagnostics> & { statistics: BackgroundStatistics; health: BackgroundHealth },
): BackgroundDiagnostics {
  return Object.freeze({
    statistics: params.statistics,
    health: params.health,
    activeTasksCount: params.activeTasksCount ?? params.statistics.activeTasks,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export interface CertificationIssue {
  readonly issueId: string;
  readonly severity: 'INFO' | 'WARNING' | 'CRITICAL';
  readonly category: string;
  readonly message: string;
  readonly timestamp: string;
}

export interface CommandCertification {
  readonly certified: boolean;
  readonly score: number;
  readonly passedChecks: number;
  readonly failedChecks: number;
  readonly certifiedAt: string;
}

export interface CommandCertificationSummary {
  readonly certified: boolean;
  readonly score: number;
  readonly status: 'PASSED' | 'FAILED';
  readonly certifiedAt: string;
}

export interface CertificationStatistics {
  readonly totalCertifications: number;
  readonly passedCertifications: number;
  readonly failedCertifications: number;
  readonly averageScore: number;
}

export interface CertificationHealth {
  readonly healthy: boolean;
  readonly certified: boolean;
  readonly score: number;
}

export interface CertificationReport {
  readonly certification: CommandCertification;
  readonly summary: CommandCertificationSummary;
  readonly issues: ReadonlyArray<CertificationIssue>;
  readonly diagnostics: CommandDiagnostics;
  readonly generatedAt: string;
}

export interface CertificationStage {
  readonly name: string;
  readonly status: 'PASSED' | 'FAILED';
  readonly durationMs: number;
  readonly checks: ReadonlyArray<CertificationCheck>;
}

export interface CertificationCheck {
  readonly name: string;
  readonly status: 'PASSED' | 'FAILED';
  readonly error?: string;
}

export interface CertificationScore {
  readonly value: number;
  readonly status: 'PASSED' | 'FAILED';
  readonly totalChecks: number;
  readonly passedChecks: number;
  readonly failedChecks: number;
}

export interface CertificationDiagnostics {
  readonly lastReport: CertificationReport | null;
  readonly statistics: CertificationStatistics;
  readonly health: CertificationHealth;
  readonly stageResults: ReadonlyArray<CertificationStage>;
}

export function createCertificationIssue(
  params: Partial<CertificationIssue> & { category: string; message: string },
): CertificationIssue {
  return Object.freeze({
    issueId: params.issueId ?? `issue_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    severity: params.severity ?? 'INFO',
    category: params.category,
    message: params.message,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createCommandCertification(params: Partial<CommandCertification> = {}): CommandCertification {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    passedChecks: params.passedChecks ?? 12,
    failedChecks: params.failedChecks ?? 0,
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createCommandCertificationSummary(params: Partial<CommandCertificationSummary> = {}): CommandCertificationSummary {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    status: params.status ?? 'PASSED',
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createCertificationStatistics(params: Partial<CertificationStatistics> = {}): CertificationStatistics {
  return Object.freeze({
    totalCertifications: params.totalCertifications ?? 0,
    passedCertifications: params.passedCertifications ?? 0,
    failedCertifications: params.failedCertifications ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationHealth(params: Partial<CertificationHealth> = {}): CertificationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    certified: params.certified ?? true,
    score: params.score ?? 100,
  });
}

export function createCertificationReport(
  params: Partial<CertificationReport> & { diagnostics: CommandDiagnostics },
): CertificationReport {
  const issues = params.issues ?? [];
  const cert = params.certification ?? createCommandCertification();
  const summary = params.summary ?? createCommandCertificationSummary({ certified: cert.certified, score: cert.score });

  return Object.freeze({
    certification: cert,
    summary,
    issues: Object.freeze([...issues]),
    diagnostics: params.diagnostics,
    generatedAt: params.generatedAt ?? new Date().toISOString(),
  });
}

export function createCertificationStage(
  params: Partial<CertificationStage> & { name: string; checks: ReadonlyArray<CertificationCheck> },
): CertificationStage {
  return Object.freeze({
    name: params.name,
    status: params.status ?? 'PASSED',
    durationMs: params.durationMs ?? 0,
    checks: Object.freeze([...params.checks]),
  });
}

export function createCertificationCheck(
  params: Partial<CertificationCheck> & { name: string },
): CertificationCheck {
  return Object.freeze({
    name: params.name,
    status: params.status ?? 'PASSED',
    error: params.error,
  });
}

export function createCertificationScore(params: Partial<CertificationScore> = {}): CertificationScore {
  return Object.freeze({
    value: params.value ?? 100,
    status: params.status ?? 'PASSED',
    totalChecks: params.totalChecks ?? 12,
    passedChecks: params.passedChecks ?? 12,
    failedChecks: params.failedChecks ?? 0,
  });
}

export function createCertificationDiagnostics(
  params: Partial<CertificationDiagnostics> & { statistics: CertificationStatistics; health: CertificationHealth },
): CertificationDiagnostics {
  return Object.freeze({
    lastReport: params.lastReport ?? null,
    statistics: params.statistics,
    health: params.health,
    stageResults: Object.freeze([...(params.stageResults ?? [])]),
  });
}
