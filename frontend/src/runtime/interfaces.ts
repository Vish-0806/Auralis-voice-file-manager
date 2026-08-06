/**
 * Frontend Runtime Interfaces (Phase 16.1).
 *
 * Defines contract specifications for IFrontendProvider and IFrontendRuntime.
 */

import {
  FrontendCapabilities,
  FrontendConfiguration,
  FrontendContext,
  FrontendDiagnostics,
  FrontendHealth,
  FrontendRuntimeState,
  FrontendState,
  FrontendStatistics,
} from './models';

export interface IFrontendProvider {
  initialize(): FrontendHealth;
  shutdown(): FrontendHealth;
  restart(): FrontendHealth;
  health(): FrontendHealth;
  statistics(): FrontendStatistics;
  capabilities(): FrontendCapabilities;
  diagnostics(): FrontendDiagnostics;
  status(): FrontendRuntimeState;
  state(): FrontendState;
  configuration(): FrontendConfiguration;
  context(): FrontendContext;
}

export interface IFrontendRuntime {
  initialize(): FrontendHealth;
  shutdown(): FrontendHealth;
  restart(): FrontendHealth;
  health(): FrontendHealth;
  statistics(): FrontendStatistics;
  capabilities(): FrontendCapabilities;
  diagnostics(): FrontendDiagnostics;
  status(): FrontendRuntimeState;
  state(): FrontendState;
  provider(): IFrontendProvider;
}
