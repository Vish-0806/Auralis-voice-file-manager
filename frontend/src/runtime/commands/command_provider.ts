/**
 * Command Provider Implementation (Phase 16.6.5).
 *
 * Implements ICommandProvider owning runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities
 * reporting, command registration management, execution pipelines, handler management,
 * middleware pipelines, interceptor chains, validation rules, permission authorization,
 * policy evaluation, history tracking, execution health, pipeline statistics, and diagnostics generation.
 */

import {
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
  ValidationHealth,
  ValidationResult,
  ValidationRule,
  ValidationStatistics,
  createCommandCapabilities,
  createCommandConfiguration,
  createCommandContext,
  createCommandDiagnostics,
  createCommandHealth,
  createCommandState,
  createCommandStatistics,
} from './models';
import {
  ICommandExecutor,
  ICommandPipeline,
  ICommandProvider,
  ICommandRegistry,
  ICommandValidator,
  IPermissionManager,
  IPolicyManager,
} from './interfaces';
import { CommandRegistry } from './command_registry';
import { CommandExecutor } from './command_executor';
import { CommandPipeline } from './command_pipeline';
import { CommandValidator } from './command_validator';
import { PermissionManager } from './permission_manager';
import { PolicyManager } from './policy_manager';

export class CommandProvider implements ICommandProvider {
  private _runtimeState: CommandRuntimeState = CommandRuntimeState.UNINITIALIZED;
  private readonly _config: CommandConfiguration;
  private readonly _capabilities: CommandCapabilities;
  private readonly _context: CommandContext;
  private readonly _registry: ICommandRegistry;
  private readonly _executor: ICommandExecutor;
  private readonly _validator: ICommandValidator;
  private readonly _permissionManager: IPermissionManager;
  private readonly _policyManager: IPolicyManager;
  private readonly _pipeline: ICommandPipeline;

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
    executor?: ICommandExecutor,
    pipeline?: ICommandPipeline,
    validator?: ICommandValidator,
    permissionManager?: IPermissionManager,
    policyManager?: IPolicyManager,
  ) {
    this._config = config ?? createCommandConfiguration();
    this._capabilities = capabilities ?? createCommandCapabilities();
    this._context = context ?? createCommandContext();
    this._registry = registry ?? new CommandRegistry();
    this._executor = executor ?? new CommandExecutor(this._registry);
    this._validator = validator ?? new CommandValidator(this._registry);
    this._permissionManager = permissionManager ?? new PermissionManager();
    this._policyManager = policyManager ?? new PolicyManager();
    this._pipeline =
      pipeline ??
      new CommandPipeline(
        this._executor,
        undefined,
        undefined,
        undefined,
        this._registry,
        this._validator,
        this._permissionManager,
        this._policyManager,
      );
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
    const execStats = this._executor.statistics();
    const execHealth = this._executor.health();
    const execHistory = this._executor.executionHistory();
    const pipeStats = this._pipeline.statistics();
    const pipeHealth = this._pipeline.health();

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
      executionStatistics: execStats,
      executionHealth: execHealth,
      executionHistorySize: execHistory.length,
      pipelineStatistics: pipeStats,
      pipelineHealth: pipeHealth,
      middlewareCount: this._pipeline.listMiddlewares().length,
      interceptorCount: this._pipeline.listInterceptors().length,
      validationDiagnostics: this._validator.diagnostics(),
      permissionDiagnostics: this._permissionManager.diagnostics(),
      policyDiagnostics: this._policyManager.diagnostics(),
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

  public registerHandler<TArgs = Record<string, unknown>, TResult = unknown>(
    commandId: string,
    handler: CommandHandler<TArgs, TResult>,
  ): void {
    this._executor.registerHandler(commandId, handler);
  }

  public unregisterHandler(commandId: string): boolean {
    return this._executor.unregisterHandler(commandId);
  }

  public hasHandler(commandId: string): boolean {
    return this._executor.hasHandler(commandId);
  }

  public execute<TResult = unknown>(
    request: CommandExecutionRequest,
  ): CommandExecutionResult<TResult> {
    return this._executor.execute<TResult>(request);
  }

  public executeAsync<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<CommandExecutionResult<TResult>> {
    return this._executor.executeAsync<TResult>(request);
  }

  public validateExecution(request: CommandExecutionRequest): CommandExecutionResult<boolean> {
    return this._executor.validateExecution(request);
  }

  public cancelExecution(executionId: string): boolean {
    return this._executor.cancelExecution(executionId);
  }

  public executionHistory(): ReadonlyArray<CommandExecutionRecord> {
    return this._executor.executionHistory();
  }

  public clearExecutionHistory(): void {
    this._executor.clearExecutionHistory();
  }

  public executionStatistics(): CommandExecutionStatistics {
    return this._executor.statistics();
  }

  public executionHealth(): CommandExecutionHealth {
    return this._executor.health();
  }

  public registerMiddleware(middleware: Parameters<ICommandPipeline['registerMiddleware']>[0]): CommandMiddleware {
    return this._pipeline.registerMiddleware(middleware);
  }

  public removeMiddleware(middlewareId: string): boolean {
    return this._pipeline.removeMiddleware(middlewareId);
  }

  public listMiddlewares(phase?: 'BEFORE' | 'AFTER' | 'EXCEPTION'): ReadonlyArray<CommandMiddleware> {
    return this._pipeline.listMiddlewares(phase);
  }

  public registerInterceptor<TResult = unknown>(
    interceptor: Partial<InterceptorRegistration<TResult>> & {
      name: string;
      intercept: InterceptorHandler<TResult>;
    },
  ): InterceptorRegistration<TResult> {
    return this._pipeline.registerInterceptor<TResult>(interceptor);
  }

  public removeInterceptor(interceptorId: string): boolean {
    return this._pipeline.removeInterceptor(interceptorId);
  }

  public listInterceptors(): ReadonlyArray<InterceptorRegistration> {
    return this._pipeline.listInterceptors();
  }

  public executePipeline<TResult = unknown>(
    request: CommandExecutionRequest,
  ): Promise<PipelineExecution<TResult>> {
    return this._pipeline.executePipeline<TResult>(request);
  }

  public pipelineStatistics(): PipelineStatistics {
    return this._pipeline.statistics();
  }

  public pipelineHealth(): PipelineHealth {
    return this._pipeline.health();
  }

  public registerValidationRule(
    rule: Parameters<ICommandValidator['registerValidationRule']>[0],
  ): ValidationRule {
    return this._validator.registerValidationRule(rule);
  }

  public removeValidationRule(ruleId: string): boolean {
    return this._validator.removeValidationRule(ruleId);
  }

  public listValidationRules(): ReadonlyArray<ValidationRule> {
    return this._validator.listValidationRules();
  }

  public validate(request: CommandExecutionRequest): Promise<ValidationResult> {
    return this._validator.validate(request);
  }

  public validationStatistics(): ValidationStatistics {
    return this._validator.statistics();
  }

  public validationHealth(): ValidationHealth {
    return this._validator.health();
  }

  public registerPermission(
    permission: Parameters<IPermissionManager['registerPermission']>[0],
  ): CommandPermission {
    return this._permissionManager.registerPermission(permission);
  }

  public removePermission(permissionId: string): boolean {
    return this._permissionManager.removePermission(permissionId);
  }

  public listPermissions(): ReadonlyArray<CommandPermission> {
    return this._permissionManager.listPermissions();
  }

  public grantPermission(userIdOrRole: string, permissionId: string): void {
    this._permissionManager.grantPermission(userIdOrRole, permissionId);
  }

  public revokePermission(userIdOrRole: string, permissionId: string): boolean {
    return this._permissionManager.revokePermission(userIdOrRole, permissionId);
  }

  public hasPermission(userIdOrRole: string, permissionId: string): PermissionResult {
    return this._permissionManager.hasPermission(userIdOrRole, permissionId);
  }

  public permissionStatistics(): PermissionStatistics {
    return this._permissionManager.statistics();
  }

  public permissionHealth(): PermissionHealth {
    return this._permissionManager.health();
  }

  public registerPolicy(
    policy: Parameters<IPolicyManager['registerPolicy']>[0],
  ): ExecutionPolicy {
    return this._policyManager.registerPolicy(policy);
  }

  public removePolicy(policyId: string): boolean {
    return this._policyManager.removePolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<ExecutionPolicy> {
    return this._policyManager.listPolicies();
  }

  public evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision> {
    return this._policyManager.evaluatePolicy(request, context);
  }

  public policyStatistics(): PolicyStatistics {
    return this._policyManager.statistics();
  }

  public policyHealth(): PolicyHealth {
    return this._policyManager.health();
  }
}
