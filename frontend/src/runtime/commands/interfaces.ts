/**
 * Command Runtime Interfaces (Phase 16.6.6).
 *
 * Defines contract specifications for ICommandRegistry, ICommandExecutor,
 * IMiddlewareManager, IInterceptorManager, ICommandPipeline, ICommandValidator,
 * IPermissionManager, IPolicyManager, ICommandScheduler, ICommandQueue,
 * IBackgroundExecutionManager, ICommandProvider, and ICommandRuntime.
 */

import {
  BackgroundTask,
  BackgroundDiagnostics,
  BackgroundHealth,
  BackgroundStatistics,
  CommandAlias,
  CommandCapabilities,
  CommandCategory,
  CommandConfiguration,
  CommandContext,
  CommandDefinition,
  CommandDiagnostics,
  CommandExecutionContext,
  CommandExecutionHealth,
  CommandExecutionRecord,
  CommandExecutionRequest,
  CommandExecutionResult,
  CommandExecutionStatistics,
  CommandHandler,
  CommandHealth,
  CommandMiddleware,
  CommandPermission,
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  ExecutionDiagnostics,
  ExecutionPolicy,
  InterceptorHandler,
  InterceptorRegistration,
  InterceptorResult,
  MiddlewareHealth,
  MiddlewareResult,
  MiddlewareStatistics,
  PermissionDiagnostics,
  PermissionHealth,
  PermissionResult,
  PermissionStatistics,
  PipelineDiagnostics,
  PipelineExecution,
  PipelineHealth,
  PipelineSnapshot,
  PipelineStatistics,
  PolicyDecision,
  PolicyDiagnostics,
  PolicyHealth,
  PolicyStatistics,
  QueueEntry,
  QueueDiagnostics,
  QueueHealth,
  QueueStatistics,
  ScheduledCommand,
  SchedulingDiagnostics,
  ScheduleHealth,
  ScheduleStatistics,
  ValidationDiagnostics,
  ValidationHealth,
  ValidationResult,
  ValidationRule,
  ValidationStatistics,
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

export interface IMiddlewareManager {
  registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware;
  removeMiddleware(middlewareId: string): boolean;
  listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware>;
  executeBefore(context: CommandExecutionContext): Promise<MiddlewareResult>;
  executeAfter(context: CommandExecutionContext, result: CommandExecutionResult): Promise<MiddlewareResult>;
  executeException(context: CommandExecutionContext, error: Error): Promise<MiddlewareResult>;
  statistics(): MiddlewareStatistics;
  health(): MiddlewareHealth;
  clear(): void;
}

export interface IInterceptorManager {
  registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult>;
  removeInterceptor(interceptorId: string): boolean;
  listInterceptors(): ReadonlyArray<InterceptorRegistration>;
  executeChain<TResult = unknown>(
    context: CommandExecutionContext,
    coreExecution: () => Promise<CommandExecutionResult<TResult>>,
  ): Promise<InterceptorResult<TResult>>;
  clear(): void;
}

export interface ICommandPipeline {
  registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware;
  removeMiddleware(middlewareId: string): boolean;
  listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware>;
  registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult>;
  removeInterceptor(interceptorId: string): boolean;
  listInterceptors(): ReadonlyArray<InterceptorRegistration>;
  executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>>;
  statistics(): PipelineStatistics;
  health(): PipelineHealth;
  diagnostics(): PipelineDiagnostics;
  snapshot(): PipelineSnapshot;
}

export interface ICommandValidator {
  registerValidationRule(
    rule: Partial<ValidationRule> & {
      name: string;
      validate: ValidationRule['validate'];
    },
  ): ValidationRule;
  removeValidationRule(ruleId: string): boolean;
  listValidationRules(): ReadonlyArray<ValidationRule>;
  validate(request: CommandExecutionRequest): Promise<ValidationResult>;
  statistics(): ValidationStatistics;
  health(): ValidationHealth;
  diagnostics(): ValidationDiagnostics;
  clear(): void;
}

export interface IPermissionManager {
  registerPermission(
    permission: Partial<CommandPermission> & { name: string },
  ): CommandPermission;
  removePermission(permissionId: string): boolean;
  listPermissions(): ReadonlyArray<CommandPermission>;
  grantPermission(userIdOrRole: string, permissionId: string): void;
  revokePermission(userIdOrRole: string, permissionId: string): boolean;
  hasPermission(userIdOrRole: string, permissionId: string): PermissionResult;
  statistics(): PermissionStatistics;
  health(): PermissionHealth;
  diagnostics(): PermissionDiagnostics;
  clear(): void;
}

export interface IPolicyManager {
  registerPolicy(
    policy: Partial<ExecutionPolicy> & {
      name: string;
      evaluate: ExecutionPolicy['evaluate'];
    },
  ): ExecutionPolicy;
  removePolicy(policyId: string): boolean;
  listPolicies(): ReadonlyArray<ExecutionPolicy>;
  evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision>;
  statistics(): PolicyStatistics;
  health(): PolicyHealth;
  diagnostics(): PolicyDiagnostics;
  clear(): void;
}

export interface ICommandScheduler {
  schedule(request: CommandExecutionRequest, delayMs?: number): Promise<ScheduledCommand>;
  scheduleDelayed(request: CommandExecutionRequest, delayMs: number): Promise<ScheduledCommand>;
  scheduleRecurring(request: CommandExecutionRequest, intervalMs: number): Promise<ScheduledCommand>;
  cancelScheduled(scheduleId: string): boolean;
  pauseSchedule(): void;
  resumeSchedule(): void;
  listSchedules(): ReadonlyArray<ScheduledCommand>;
  statistics(): ScheduleStatistics;
  health(): ScheduleHealth;
  diagnostics(): SchedulingDiagnostics;
  clear(): void;
}

export interface ICommandQueue {
  queue(request: CommandExecutionRequest, priority?: number): Promise<QueueEntry>;
  dequeue(): Promise<QueueEntry | undefined>;
  peek(): QueueEntry | undefined;
  queueSize(): number;
  clearQueue(): void;
  statistics(): QueueStatistics;
  health(): QueueHealth;
  diagnostics(): QueueDiagnostics;
  clear(): void;
}

export interface IBackgroundExecutionManager {
  submitBackgroundTask(request: CommandExecutionRequest): Promise<BackgroundTask>;
  cancelBackgroundTask(taskId: string): boolean;
  backgroundTasks(): ReadonlyArray<BackgroundTask>;
  statistics(): BackgroundStatistics;
  health(): BackgroundHealth;
  diagnostics(): BackgroundDiagnostics;
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

  registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware;
  removeMiddleware(middlewareId: string): boolean;
  listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware>;
  registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult>;
  removeInterceptor(interceptorId: string): boolean;
  listInterceptors(): ReadonlyArray<InterceptorRegistration>;
  executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>>;
  pipelineStatistics(): PipelineStatistics;
  pipelineHealth(): PipelineHealth;

  registerValidationRule(
    rule: Partial<ValidationRule> & {
      name: string;
      validate: ValidationRule['validate'];
    },
  ): ValidationRule;
  removeValidationRule(ruleId: string): boolean;
  listValidationRules(): ReadonlyArray<ValidationRule>;
  validate(request: CommandExecutionRequest): Promise<ValidationResult>;
  validationStatistics(): ValidationStatistics;
  validationHealth(): ValidationHealth;

  registerPermission(
    permission: Partial<CommandPermission> & { name: string },
  ): CommandPermission;
  removePermission(permissionId: string): boolean;
  listPermissions(): ReadonlyArray<CommandPermission>;
  grantPermission(userIdOrRole: string, permissionId: string): void;
  revokePermission(userIdOrRole: string, permissionId: string): boolean;
  hasPermission(userIdOrRole: string, permissionId: string): PermissionResult;
  permissionStatistics(): PermissionStatistics;
  permissionHealth(): PermissionHealth;

  registerPolicy(
    policy: Partial<ExecutionPolicy> & {
      name: string;
      evaluate: ExecutionPolicy['evaluate'];
    },
  ): ExecutionPolicy;
  removePolicy(policyId: string): boolean;
  listPolicies(): ReadonlyArray<ExecutionPolicy>;
  evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision>;
  policyStatistics(): PolicyStatistics;
  policyHealth(): PolicyHealth;

  schedule(request: CommandExecutionRequest, delayMs?: number): Promise<ScheduledCommand>;
  scheduleDelayed(request: CommandExecutionRequest, delayMs: number): Promise<ScheduledCommand>;
  scheduleRecurring(request: CommandExecutionRequest, intervalMs: number): Promise<ScheduledCommand>;
  cancelScheduled(scheduleId: string): boolean;
  pauseSchedule(): void;
  resumeSchedule(): void;
  listSchedules(): ReadonlyArray<ScheduledCommand>;
  schedulerStatistics(): ScheduleStatistics;
  schedulerHealth(): ScheduleHealth;

  queue(request: CommandExecutionRequest, priority?: number): Promise<QueueEntry>;
  dequeue(): Promise<QueueEntry | undefined>;
  peek(): QueueEntry | undefined;
  queueSize(): number;
  clearQueue(): void;
  queueStatistics(): QueueStatistics;
  queueHealth(): QueueHealth;

  submitBackgroundTask(request: CommandExecutionRequest): Promise<BackgroundTask>;
  cancelBackgroundTask(taskId: string): boolean;
  backgroundTasks(): ReadonlyArray<BackgroundTask>;
  backgroundStatistics(): BackgroundStatistics;
  backgroundHealth(): BackgroundHealth;
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

  registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware;
  removeMiddleware(middlewareId: string): boolean;
  listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware>;
  registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult>;
  removeInterceptor(interceptorId: string): boolean;
  listInterceptors(): ReadonlyArray<InterceptorRegistration>;
  executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>>;
  pipelineStatistics(): PipelineStatistics;
  pipelineHealth(): PipelineHealth;

  registerValidationRule(
    rule: Partial<ValidationRule> & {
      name: string;
      validate: ValidationRule['validate'];
    },
  ): ValidationRule;
  removeValidationRule(ruleId: string): boolean;
  listValidationRules(): ReadonlyArray<ValidationRule>;
  validate(request: CommandExecutionRequest): Promise<ValidationResult>;
  validationStatistics(): ValidationStatistics;
  validationHealth(): ValidationHealth;

  registerPermission(
    permission: Partial<CommandPermission> & { name: string },
  ): CommandPermission;
  removePermission(permissionId: string): boolean;
  listPermissions(): ReadonlyArray<CommandPermission>;
  grantPermission(userIdOrRole: string, permissionId: string): void;
  revokePermission(userIdOrRole: string, permissionId: string): boolean;
  hasPermission(userIdOrRole: string, permissionId: string): PermissionResult;
  permissionStatistics(): PermissionStatistics;
  permissionHealth(): PermissionHealth;

  registerPolicy(
    policy: Partial<ExecutionPolicy> & {
      name: string;
      evaluate: ExecutionPolicy['evaluate'];
    },
  ): ExecutionPolicy;
  removePolicy(policyId: string): boolean;
  listPolicies(): ReadonlyArray<ExecutionPolicy>;
  evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision>;
  policyStatistics(): PolicyStatistics;
  policyHealth(): PolicyHealth;

  schedule(request: CommandExecutionRequest, delayMs?: number): Promise<ScheduledCommand>;
  scheduleDelayed(request: CommandExecutionRequest, delayMs: number): Promise<ScheduledCommand>;
  scheduleRecurring(request: CommandExecutionRequest, intervalMs: number): Promise<ScheduledCommand>;
  cancelScheduled(scheduleId: string): boolean;
  pauseSchedule(): void;
  resumeSchedule(): void;
  listSchedules(): ReadonlyArray<ScheduledCommand>;
  schedulerStatistics(): ScheduleStatistics;
  schedulerHealth(): ScheduleHealth;

  queue(request: CommandExecutionRequest, priority?: number): Promise<QueueEntry>;
  dequeue(): Promise<QueueEntry | undefined>;
  peek(): QueueEntry | undefined;
  queueSize(): number;
  clearQueue(): void;
  queueStatistics(): QueueStatistics;
  queueHealth(): QueueHealth;

  submitBackgroundTask(request: CommandExecutionRequest): Promise<BackgroundTask>;
  cancelBackgroundTask(taskId: string): boolean;
  backgroundTasks(): ReadonlyArray<BackgroundTask>;
  backgroundStatistics(): BackgroundStatistics;
  backgroundHealth(): BackgroundHealth;
}
