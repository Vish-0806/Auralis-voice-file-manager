/**
 * Frontend Global Runtime Helpers (Phase 16.1).
 *
 * Provides lazy-initialized singleton accessors for global FrontendRuntime
 * and FrontendProvider instances.
 */

import { IFrontendProvider, IFrontendRuntime } from './interfaces';
import { FrontendRuntime } from './frontend_runtime';
import { FrontendProvider } from './frontend_provider';

let _globalFrontendRuntime: IFrontendRuntime | null = null;
let _globalFrontendProvider: IFrontendProvider | null = null;

export function getFrontendRuntime(): IFrontendRuntime {
  if (!_globalFrontendRuntime) {
    const provider = getFrontendProvider();
    _globalFrontendRuntime = new FrontendRuntime(provider);
  }
  return _globalFrontendRuntime;
}

export function setFrontendRuntime(runtime: IFrontendRuntime): void {
  _globalFrontendRuntime = runtime;
}

export function resetFrontendRuntime(): void {
  _globalFrontendRuntime = null;
}

export function getFrontendProvider(): IFrontendProvider {
  if (!_globalFrontendProvider) {
    _globalFrontendProvider = new FrontendProvider();
  }
  return _globalFrontendProvider;
}

export function setFrontendProvider(provider: IFrontendProvider): void {
  _globalFrontendProvider = provider;
}

export function resetFrontendProvider(): void {
  _globalFrontendProvider = null;
}
