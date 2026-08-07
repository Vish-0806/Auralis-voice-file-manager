/**
 * Command Runtime Coordinator Implementation (Phase 16.6.6).
 *
 * Implements ICommandRuntime acting as central coordinator delegating to ICommandProvider.
 * Contains no business logic — all operations are forwarded to the provider instance.
 */

import {
  BackgroundTask,
  BackgroundHealth,
  BackgroundStatistics,
  CommandAlias,
  CommandCapabilities,
  CommandCategory,
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
  ExecutionPolicy,
  InterceptorHandler,
  InterceptorRegistration,
  PermissionHealth,
  PermissionResult,
  PermissionStatistics,
  PipelineExecution,
  PipelineHealth,
  PipelineStatistics,
  PolicyDecision,
  PolicyHealth,
  PolicyStatistics,
  QueueEntry,
  QueueHealth,
  QueueStatistics,
  ScheduledCommand,
  ScheduleHealth,
  ScheduleStatistics,
  ValidationHealth,
  ValidationResult,
  ValidationRule,
  ValidationStatistics,
  CertificationHealth,
  CertificationReport,
  CertificationStatistics,
  CommandCertification,
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

  public registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void {
    this._provider.registerHandler(commandId, handler);
  }

  public unregisterHandler(commandId: string): boolean {
    return this._provider.unregisterHandler(commandId);
  }

  public hasHandler(commandId: string): boolean {
    return this._provider.hasHandler(commandId);
  }

  public execute<TResult = unknown>(
    request: CommandExecutionRequest,
  ): CommandExecutionResult<TResult> {
    return this._provider.execute<TResult>(request);
  }

  public executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>> {
    return this._provider.executeAsync<TResult>(request);
  }

  public validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean> {
    return this._provider.validateExecution(request);
  }

  public cancelExecution(executionId: string): boolean {
    return this._provider.cancelExecution(executionId);
  }

  public executionHistory(): ReadonlyArray<CommandExecutionRecord> {
    return this._provider.executionHistory();
  }

  public clearExecutionHistory(): void {
    this._provider.clearExecutionHistory();
  }

  public executionStatistics(): CommandExecutionStatistics {
    return this._provider.executionStatistics();
  }

  public executionHealth(): CommandExecutionHealth {
    return this._provider.executionHealth();
  }

  public registerMiddleware(
    middleware: Partial<CommandMiddleware> & {
      name: string;
      execute: (context: CommandExecutionContext, result?: CommandExecutionResult, error?: Error) => void | Promise<void>;
    },
  ): CommandMiddleware {
    return this._provider.registerMiddleware(middleware);
  }

  public removeMiddleware(middlewareId: string): boolean {
    return this._provider.removeMiddleware(middlewareId);
  }

  public listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware> {
    return this._provider.listMiddlewares(phase);
  }

  public registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult> {
    return this._provider.registerInterceptor<TResult>(interceptor);
  }

  public removeInterceptor(interceptorId: string): boolean {
    return this._provider.removeInterceptor(interceptorId);
  }

  public listInterceptors(): ReadonlyArray<InterceptorRegistration> {
    return this._provider.listInterceptors();
  }

  public executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>> {
    return this._provider.executePipeline<TResult>(request);
  }

  public pipelineStatistics(): PipelineStatistics {
    return this._provider.pipelineStatistics();
  }

  public pipelineHealth(): PipelineHealth {
    return this._provider.pipelineHealth();
  }

  public registerValidationRule(
    rule: Parameters<ICommandProvider['registerValidationRule']>[0],
  ): ValidationRule {
    return this._provider.registerValidationRule(rule);
  }

  public removeValidationRule(ruleId: string): boolean {
    return this._provider.removeValidationRule(ruleId);
  }

  public listValidationRules(): ReadonlyArray<ValidationRule> {
    return this._provider.listValidationRules();
  }

  public validate(request: CommandExecutionRequest): Promise<ValidationResult> {
    return this._provider.validate(request);
  }

  public validationStatistics(): ValidationStatistics {
    return this._provider.validationStatistics();
  }

  public validationHealth(): ValidationHealth {
    return this._provider.validationHealth();
  }

  public registerPermission(
    permission: Parameters<ICommandProvider['registerPermission']>[0],
  ): CommandPermission {
    return this._provider.registerPermission(permission);
  }

  public removePermission(permissionId: string): boolean {
    return this._provider.removePermission(permissionId);
  }

  public listPermissions(): ReadonlyArray<CommandPermission> {
    return this._provider.listPermissions();
  }

  public grantPermission(userIdOrRole: string, permissionId: string): void {
    this._provider.grantPermission(userIdOrRole, permissionId);
  }

  public revokePermission(userIdOrRole: string, permissionId: string): boolean {
    return this._provider.revokePermission(userIdOrRole, permissionId);
  }

  public hasPermission(userIdOrRole: string, permissionId: string): PermissionResult {
    return this._provider.hasPermission(userIdOrRole, permissionId);
  }

  public permissionStatistics(): PermissionStatistics {
    return this._provider.permissionStatistics();
  }

  public permissionHealth(): PermissionHealth {
    return this._provider.permissionHealth();
  }

  public registerPolicy(
    policy: Parameters<ICommandProvider['registerPolicy']>[0],
  ): ExecutionPolicy {
    return this._provider.registerPolicy(policy);
  }

  public removePolicy(policyId: string): boolean {
    return this._provider.removePolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<ExecutionPolicy> {
    return this._provider.listPolicies();
  }

  public evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision> {
    return this._provider.evaluatePolicy(request, context);
  }

  public policyStatistics(): PolicyStatistics {
    return this._provider.policyStatistics();
  }

  public policyHealth(): PolicyHealth {
    return this._provider.policyHealth();
  }

  public schedule(request: CommandExecutionRequest, delayMs?: number): Promise<ScheduledCommand> {
    return this._provider.schedule(request, delayMs);
  }

  public scheduleDelayed(request: CommandExecutionRequest, delayMs: number): Promise<ScheduledCommand> {
    return this._provider.scheduleDelayed(request, delayMs);
  }

  public scheduleRecurring(request: CommandExecutionRequest, intervalMs: number): Promise<ScheduledCommand> {
    return this._provider.scheduleRecurring(request, intervalMs);
  }

  public cancelScheduled(scheduleId: string): boolean {
    return this._provider.cancelScheduled(scheduleId);
  }

  public pauseSchedule(): void {
    this._provider.pauseSchedule();
  }

  public resumeSchedule(): void {
    this._provider.resumeSchedule();
  }

  public listSchedules(): ReadonlyArray<ScheduledCommand> {
    return this._provider.listSchedules();
  }

  public schedulerStatistics(): ScheduleStatistics {
    return this._provider.schedulerStatistics();
  }

  public schedulerHealth(): ScheduleHealth {
    return this._provider.schedulerHealth();
  }

  public queue(request: CommandExecutionRequest, priority?: number): Promise<QueueEntry> {
    return this._provider.queue(request, priority);
  }

  public dequeue(): Promise<QueueEntry | undefined> {
    return this._provider.dequeue();
  }

  public peek(): QueueEntry | undefined {
    return this._provider.peek();
  }

  public queueSize(): number {
    return this._provider.queueSize();
  }

  public clearQueue(): void {
    this._provider.clearQueue();
  }

  public queueStatistics(): QueueStatistics {
    return this._provider.queueStatistics();
  }

  public queueHealth(): QueueHealth {
    return this._provider.queueHealth();
  }

  public submitBackgroundTask(request: CommandExecutionRequest): Promise<BackgroundTask> {
    return this._provider.submitBackgroundTask(request);
  }

  public cancelBackgroundTask(taskId: string): boolean {
    return this._provider.cancelBackgroundTask(taskId);
  }

  public backgroundTasks(): ReadonlyArray<BackgroundTask> {
    return this._provider.backgroundTasks();
  }

  public backgroundStatistics(): BackgroundStatistics {
    return this._provider.backgroundStatistics();
  }

  public backgroundHealth(): BackgroundHealth {
    return this._provider.backgroundHealth();
  }

  public async certify(): Promise<CommandCertification> {
    return this._provider.certify();
  }

  public async runCertification(): Promise<CertificationReport> {
    return this._provider.runCertification();
  }

  public async certificationReport(): Promise<CertificationReport> {
    return this._provider.certificationReport();
  }

  public certificationStatistics(): CertificationStatistics {
    return this._provider.certificationStatistics();
  }

  public certificationHealth(): CertificationHealth {
    return this._provider.certificationHealth();
  }
}
