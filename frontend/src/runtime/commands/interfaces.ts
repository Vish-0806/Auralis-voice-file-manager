/**
 * Command Runtime Interfaces (Phase 16.6.1).
 *
 * Defines contract specifications for ICommandProvider and ICommandRuntime.
 */

import {
  CommandCapabilities,
  CommandConfiguration,
  CommandContext,
  CommandDiagnostics,
  CommandHealth,
  CommandRuntimeState,
  CommandState,
  CommandStatistics,
} from './models';

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
}
