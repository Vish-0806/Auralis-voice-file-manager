/**
 * Command Runtime Coordinator Implementation (Phase 16.6.4).
 *
 * Implements ICommandRuntime acting as central coordinator delegating to ICommandProvider.
 * Contains no business logic — all operations are forwarded to the provider instance.
 */

import {
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
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  InterceptorHandler,
  InterceptorRegistration,
  PipelineExecution,
  PipelineHealth,
  PipelineStatistics,
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
    return this._provider.registerInterceptor(interceptor);
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
}
