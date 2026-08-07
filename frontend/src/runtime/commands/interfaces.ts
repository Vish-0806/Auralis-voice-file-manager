/**
 * Command Runtime Interfaces (Phase 16.6.4).
 *
 * Defines contract specifications for ICommandRegistry, ICommandExecutor,
 * IMiddlewareManager, IInterceptorManager, ICommandPipeline, ICommandProvider, and ICommandRuntime.
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
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
  ExecutionDiagnostics,
  InterceptorHandler,
  InterceptorRegistration,
  InterceptorResult,
  MiddlewareHealth,
  MiddlewareResult,
  MiddlewareStatistics,
  PipelineDiagnostics,
  PipelineExecution,
  PipelineHealth,
  PipelineSnapshot,
  PipelineStatistics,
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
}
