/**
 * Configuration Runtime Interfaces (Phase 16.3.1).
 *
 * Defines contracts for IConfigurationProvider and IConfigurationRuntime.
 */

import {
  ConfigurationCapabilities,
  ConfigurationConfiguration,
  ConfigurationContext,
  ConfigurationDiagnostics,
  ConfigurationHealth,
  ConfigurationState,
  ConfigurationStatistics,
} from './models';

export interface IConfigurationProvider {
  initialize(): ConfigurationHealth;
  shutdown(): ConfigurationHealth;
  restart(): ConfigurationHealth;
  health(): ConfigurationHealth;
  statistics(): ConfigurationStatistics;
  capabilities(): ConfigurationCapabilities;
  diagnostics(): ConfigurationDiagnostics;
  state(): ConfigurationState;
  configuration(): ConfigurationConfiguration;
  context(): ConfigurationContext;
}

export interface IConfigurationRuntime {
  initialize(): ConfigurationHealth;
  shutdown(): ConfigurationHealth;
  restart(): ConfigurationHealth;
  provider(): IConfigurationProvider;
  health(): ConfigurationHealth;
  statistics(): ConfigurationStatistics;
  diagnostics(): ConfigurationDiagnostics;
  state(): ConfigurationState;
}
