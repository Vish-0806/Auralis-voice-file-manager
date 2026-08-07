/**
 * Global Command Runtime Singleton Accessors (Phase 16.6.1).
 *
 * Provides lazy singleton instances and lifecycle reset helpers for
 * ICommandRuntime and ICommandProvider.
 */

import { ICommandProvider, ICommandRuntime } from './interfaces';
import { CommandProvider } from './command_provider';
import { CommandRuntime } from './command_runtime';

let globalCommandProvider: ICommandProvider | null = null;
let globalCommandRuntime: ICommandRuntime | null = null;

export function getCommandProvider(): ICommandProvider {
  if (!globalCommandProvider) {
    globalCommandProvider = new CommandProvider();
  }
  return globalCommandProvider;
}

export function setCommandProvider(provider: ICommandProvider): void {
  globalCommandProvider = provider;
}

export function resetCommandProvider(): void {
  if (globalCommandProvider) {
    globalCommandProvider.shutdown();
  }
  globalCommandProvider = null;
}

export function getCommandRuntime(): ICommandRuntime {
  if (!globalCommandRuntime) {
    globalCommandRuntime = new CommandRuntime(getCommandProvider());
  }
  return globalCommandRuntime;
}

export function setCommandRuntime(runtime: ICommandRuntime): void {
  globalCommandRuntime = runtime;
}

export function resetCommandRuntime(): void {
  if (globalCommandRuntime) {
    globalCommandRuntime.shutdown();
  }
  globalCommandRuntime = null;
  resetCommandProvider();
}
