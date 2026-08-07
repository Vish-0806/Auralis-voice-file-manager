/**
 * Global Plugin Runtime Singleton Accessors (Phase 16.7).
 *
 * Provides lazy singleton instances and lifecycle reset helpers for
 * IPluginRuntime and IPluginProvider.
 */

import { IPluginProvider, IPluginRuntime } from './interfaces';
import { PluginProvider } from './plugin_provider';
import { PluginRuntime } from './plugin_runtime';

let globalPluginProvider: IPluginProvider | null = null;
let globalPluginRuntime: IPluginRuntime | null = null;

export function getPluginProvider(): IPluginProvider {
  if (!globalPluginProvider) {
    globalPluginProvider = new PluginProvider();
  }
  return globalPluginProvider;
}

export function setPluginProvider(provider: IPluginProvider): void {
  globalPluginProvider = provider;
}

export function resetPluginProvider(): void {
  if (globalPluginProvider) {
    globalPluginProvider.shutdown();
  }
  globalPluginProvider = null;
}

export function getPluginRuntime(): IPluginRuntime {
  if (!globalPluginRuntime) {
    globalPluginRuntime = new PluginRuntime(getPluginProvider());
  }
  return globalPluginRuntime;
}

export function setPluginRuntime(runtime: IPluginRuntime): void {
  globalPluginRuntime = runtime;
}

export function resetPluginRuntime(): void {
  if (globalPluginRuntime) {
    globalPluginRuntime.shutdown();
  }
  globalPluginRuntime = null;
  resetPluginProvider();
}
