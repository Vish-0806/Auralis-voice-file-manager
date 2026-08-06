/**
 * Global Event Runtime Singleton Accessors (Phase 16.4.1).
 *
 * Provides lazy singleton instances and lifecycle reset helpers for IEventRuntime and IEventProvider.
 */

import { IEventProvider, IEventRuntime } from './interfaces';
import { EventProvider } from './event_provider';
import { EventRuntime } from './event_runtime';

let globalEventProvider: IEventProvider | null = null;
let globalEventRuntime: IEventRuntime | null = null;

export function getEventProvider(): IEventProvider {
  if (!globalEventProvider) {
    globalEventProvider = new EventProvider();
  }
  return globalEventProvider;
}

export function setEventProvider(provider: IEventProvider): void {
  globalEventProvider = provider;
}

export function resetEventProvider(): void {
  if (globalEventProvider) {
    globalEventProvider.shutdown();
  }
  globalEventProvider = null;
}

export function getEventRuntime(): IEventRuntime {
  if (!globalEventRuntime) {
    globalEventRuntime = new EventRuntime(getEventProvider());
  }
  return globalEventRuntime;
}

export function setEventRuntime(runtime: IEventRuntime): void {
  globalEventRuntime = runtime;
}

export function resetEventRuntime(): void {
  if (globalEventRuntime) {
    globalEventRuntime.shutdown();
  }
  globalEventRuntime = null;
  resetEventProvider();
}
