/**
 * Configuration Runtime Global Accessors & Singleton Helpers (Phase 16.3.1).
 *
 * Provides lazy singleton instances and management functions for IConfigurationRuntime
 * and IConfigurationProvider.
 */

import { IConfigurationProvider, IConfigurationRuntime } from './interfaces';
import { ConfigurationRuntime } from './configuration_runtime';
import { ConfigurationProvider } from './configuration_provider';

let _configurationRuntimeInstance: IConfigurationRuntime | null = null;
let _configurationProviderInstance: IConfigurationProvider | null = null;

export function getConfigurationRuntime(): IConfigurationRuntime {
  if (!_configurationRuntimeInstance) {
    _configurationRuntimeInstance = new ConfigurationRuntime(getConfigurationProvider());
  }
  return _configurationRuntimeInstance;
}

export function setConfigurationRuntime(runtime: IConfigurationRuntime): void {
  _configurationRuntimeInstance = runtime;
}

export function resetConfigurationRuntime(): void {
  _configurationRuntimeInstance = null;
}

export function getConfigurationProvider(): IConfigurationProvider {
  if (!_configurationProviderInstance) {
    _configurationProviderInstance = new ConfigurationProvider();
  }
  return _configurationProviderInstance;
}

export function setConfigurationProvider(provider: IConfigurationProvider): void {
  _configurationProviderInstance = provider;
}

export function resetConfigurationProvider(): void {
  _configurationProviderInstance = null;
}
