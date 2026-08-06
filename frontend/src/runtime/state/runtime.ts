/**
 * State Runtime Lazy Singleton Accessors (Phase 16.5).
 *
 * Provides global singleton instance management for IStateRuntime and IStateProvider.
 */

import { IStateProvider, IStateRuntime } from './interfaces';
import { StateProvider } from './state_provider';
import { StateRuntime } from './state_runtime';

let globalStateProvider: IStateProvider | null = null;
let globalStateRuntime: IStateRuntime | null = null;

export function getStateProvider(): IStateProvider {
  if (!globalStateProvider) {
    globalStateProvider = new StateProvider();
  }
  return globalStateProvider;
}

export function setStateProvider(provider: IStateProvider): void {
  globalStateProvider = provider;
  if (globalStateRuntime) {
    globalStateRuntime = new StateRuntime(provider);
  }
}

export function resetStateProvider(): void {
  globalStateProvider = null;
}

export function getStateRuntime(): IStateRuntime {
  if (!globalStateRuntime) {
    globalStateRuntime = new StateRuntime(getStateProvider());
  }
  return globalStateRuntime;
}

export function setStateRuntime(runtime: IStateRuntime): void {
  globalStateRuntime = runtime;
  globalStateProvider = runtime.provider();
}

export function resetStateRuntime(): void {
  globalStateRuntime = null;
  globalStateProvider = null;
}
