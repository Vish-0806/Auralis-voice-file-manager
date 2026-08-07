/**
 * Command Runtime Domain Models (Phase 16.6.1).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, and diagnostics
 * telemetry for the Frontend Command Runtime.
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
}

export interface CommandDiagnostics {
  readonly health: CommandHealth;
  readonly statistics: CommandStatistics;
  readonly capabilities: CommandCapabilities;
  readonly context: CommandContext;
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
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
