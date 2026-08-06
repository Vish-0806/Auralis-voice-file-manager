/**
 * Selector Engine (Phase 16.5).
 *
 * Implements ISelectorEngine managing memoized and derived selector registration,
 * state dependency evaluation, cache invalidation, and selector result telemetry.
 */

import { createSelectorResult, Selector, SelectorResult } from './models';
import { SelectorException, StateValidationException } from './exceptions';
import { ISelectorEngine } from './interfaces';

export class SelectorEngine implements ISelectorEngine {
  private readonly _selectors = new Map<string, Selector>();
  private readonly _cache = new Map<string, { lastState: unknown; result: unknown }>();

  public registerSelector<S = unknown, R = unknown>(selector: Selector<S, R>): void {
    if (!selector) {
      throw new StateValidationException('Selector cannot be null or undefined.');
    }
    if (!selector.name || !selector.name.trim()) {
      throw new StateValidationException('Selector name cannot be empty.');
    }
    if (!selector.select) {
      throw new StateValidationException('Selector select function cannot be undefined.');
    }
    if (this._selectors.has(selector.selectorId)) {
      throw new SelectorException(`Selector ID '${selector.selectorId}' is already registered.`);
    }

    this._selectors.set(selector.selectorId, selector as any);
  }

  public evaluate<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R> {
    const id = selectorId ? selectorId.trim() : '';
    const selector = this._selectors.get(id);

    if (!selector) {
      throw new SelectorException(`Selector ID '${id}' is not registered.`);
    }

    const cached = this._cache.get(id);
    if (cached && cached.lastState === state) {
      return createSelectorResult<R>({
        value: cached.result as R,
        memoized: true,
        durationMs: 0,
      });
    }

    const start = performance ? performance.now() : Date.now();
    const value = selector.select(state) as R;
    const end = performance ? performance.now() : Date.now();

    this._cache.set(id, { lastState: state, result: value });

    return createSelectorResult<R>({
      value,
      memoized: false,
      durationMs: Math.max(0, Math.round((end - start) * 100) / 100),
    });
  }

  public clearCache(): void {
    this._cache.clear();
  }
}
