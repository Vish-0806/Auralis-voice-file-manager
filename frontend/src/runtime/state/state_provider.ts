/**
 * State Provider Implementation (Phase 16.5).
 *
 * Implements IStateProvider owning runtime state transitions, state store management,
 * container registry, action dispatching, reducer execution, middleware management,
 * memoized selectors, subscriptions, undo/redo history, abstract persistence,
 * state synchronization, and diagnostics aggregation.
 */

import {
  Action,
  CertificationReport,
  createAction,
  createReducer,
  createSelector,
  createStateCapabilities,
  createStateConfiguration,
  createStateContext,
  createStateDiagnostics,
  createStateHealth,
  createStateStatistics,
  createSubscription,
  PersistenceRecord,
  RedoRecord,
  Selector,
  SelectorResult,
  StateCapabilities,
  StateCertification,
  StateConfiguration,
  StateContainer,
  StateContext,
  StateDiagnostics,
  StateHealth,
  StateRuntimeState,
  StateStatistics,
  Subscription,
  SynchronizationRecord,
  UndoRecord,
} from './models';
import { StateValidationException } from './exceptions';
import { IStateProvider } from './interfaces';
import { StateStore } from './store';
import { StateRegistry } from './state_registry';
import { ActionDispatcher } from './state_action';
import { ReducerEngine } from './state_reducer';
import { MiddlewareManager } from './middleware_manager';
import { SelectorEngine } from './state_selector';
import { HistoryManager } from './state_history';
import { PersistenceManager } from './persistence_manager';
import { StateSynchronizer } from './state_synchronizer';
import { StateCertifier } from './state_certifier';

export class StateProvider implements IStateProvider {
  private _runtimeState: StateRuntimeState = StateRuntimeState.UNINITIALIZED;
  private readonly _config: StateConfiguration;
  private readonly _capabilities: StateCapabilities;
  private readonly _context: StateContext;

  private readonly _store: StateStore;
  private readonly _registry: StateRegistry;
  private readonly _actionDispatcher: ActionDispatcher;
  private readonly _reducerEngine: ReducerEngine;
  private readonly _middlewareManager: MiddlewareManager;
  private readonly _selectorEngine: SelectorEngine;
  private readonly _historyManager: HistoryManager;
  private readonly _persistenceManager: PersistenceManager;
  private readonly _synchronizer: StateSynchronizer;
  private readonly _certifier: StateCertifier;

  private readonly _subscribers = new Map<string, Map<string, (state: any) => void | Promise<void>>>();

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: StateConfiguration,
    capabilities?: StateCapabilities,
    context?: StateContext,
    store?: StateStore,
    registry?: StateRegistry,
    actionDispatcher?: ActionDispatcher,
    reducerEngine?: ReducerEngine,
    middlewareManager?: MiddlewareManager,
    selectorEngine?: SelectorEngine,
    historyManager?: HistoryManager,
    persistenceManager?: PersistenceManager,
    synchronizer?: StateSynchronizer,
    certifier?: StateCertifier,
  ) {
    this._config = config ?? createStateConfiguration();
    this._capabilities = capabilities ?? createStateCapabilities();
    this._context = context ?? createStateContext();

    this._store = store ?? new StateStore();
    this._registry = registry ?? new StateRegistry();
    this._actionDispatcher = actionDispatcher ?? new ActionDispatcher(this._config.maxHistorySize ?? 50);
    this._reducerEngine = reducerEngine ?? new ReducerEngine();
    this._middlewareManager = middlewareManager ?? new MiddlewareManager();
    this._selectorEngine = selectorEngine ?? new SelectorEngine();
    this._historyManager = historyManager ?? new HistoryManager(this._config.maxHistorySize ?? 50);
    this._persistenceManager = persistenceManager ?? new PersistenceManager();
    this._synchronizer = synchronizer ?? new StateSynchronizer();
    this._certifier = certifier ?? new StateCertifier();
  }

  public initialize(): StateHealth {
    if (
      this._runtimeState === StateRuntimeState.INITIALIZING ||
      this._runtimeState === StateRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = StateRuntimeState.INITIALIZING;
    this._runtimeState = StateRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): StateHealth {
    if (this._runtimeState === StateRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = StateRuntimeState.STOPPING;
    this._runtimeState = StateRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): StateHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): StateHealth {
    const healthy = this._runtimeState === StateRuntimeState.READY;
    const message = healthy
      ? 'State runtime is ready and operational.'
      : `State runtime is in state ${this._runtimeState}.`;

    return createStateHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): StateStatistics {
    const uptime =
      this._runtimeState === StateRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createStateStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): StateCapabilities {
    return this._capabilities;
  }

  public diagnostics(): StateDiagnostics {
    const containers = this._store.listContainers();

    return createStateDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      containersCount: containers.length,
      actionsCount: this._actionDispatcher.history().length,
      reducersCount: this._reducerEngine.listReducers().length,
      historySize: this._historyManager.history().snapshots.length,
      persistenceStatus: 'ACTIVE',
      timestamp: new Date().toISOString(),
    });
  }

  public configuration(): StateConfiguration {
    return this._config;
  }

  public context(): StateContext {
    return this._context;
  }

  public createContainer<T = unknown>(name: string, initialState: T): StateContainer<T> {
    const container = this._store.createContainer<T>(name, initialState);
    this._registry.registerContainer(container);
    this._historyManager.pushSnapshot(container.containerId, initialState);
    return container;
  }

  public getContainer<T = unknown>(name: string): StateContainer<T> | undefined {
    return this._store.getContainer<T>(name);
  }

  public setState<T = unknown>(name: string, state: T): StateContainer<T> {
    const engine = this._store.getContainerEngine<T>(name);
    if (!engine) {
      throw new StateValidationException(`State container '${name}' does not exist.`);
    }

    const updated = engine.setState(state);
    this._historyManager.pushSnapshot(updated.containerId, state);
    this.notifySubscribers(name, state);

    return updated;
  }

  public getState<T = unknown>(name: string): T | undefined {
    const engine = this._store.getContainerEngine<T>(name);
    return engine ? engine.getState() : undefined;
  }

  public subscribe<T = unknown>(containerName: string, handler: (state: T) => void | Promise<void>): Subscription {
    const name = containerName ? containerName.trim() : '';
    if (!name || !handler) {
      throw new StateValidationException('Container name and handler function are required for subscription.');
    }

    if (!this._subscribers.has(name)) {
      this._subscribers.set(name, new Map());
    }

    const sub = createSubscription({ containerId: name });
    this._subscribers.get(name)!.set(sub.subscriptionId, handler as any);

    return sub;
  }

  public unsubscribe(subscriptionId: string): boolean {
    const subId = subscriptionId ? subscriptionId.trim() : '';
    for (const subMap of this._subscribers.values()) {
      if (subMap.has(subId)) {
        return subMap.delete(subId);
      }
    }
    return false;
  }

  public dispatch<T = unknown>(type: string, payload: T): Action<T> {
    const act = createAction<T>({ type, payload });
    this._middlewareManager.executeBefore(act as any);

    const dispatched = this._actionDispatcher.dispatch(act);

    // Run reducers against active containers
    for (const container of this._store.listContainers()) {
      const { newState } = this._reducerEngine.executeReducers(container.state, dispatched as any);
      if (newState !== container.state) {
        this.setState(container.name, newState);
      }
    }

    this._middlewareManager.executeAfter(dispatched as any);
    return dispatched;
  }

  public registerReducer<S = unknown, A = Action>(name: string, reduce: (state: S, action: A) => S): void {
    const red = createReducer<S, A>({ name, reduce });
    this._reducerEngine.registerReducer(red);
  }

  public registerSelector<S = unknown, R = unknown>(name: string, select: (state: S) => R): Selector<S, R> {
    const sel = createSelector<S, R>({ selectorId: name, name, select });
    this._selectorEngine.registerSelector(sel);
    return sel;
  }

  public select<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R> {
    return this._selectorEngine.evaluate<S, R>(selectorId, state);
  }

  public undo<T = unknown>(): UndoRecord<T> | undefined {
    return this._historyManager.undo() as UndoRecord<T> | undefined;
  }

  public redo<T = unknown>(): RedoRecord<T> | undefined {
    return this._historyManager.redo() as RedoRecord<T> | undefined;
  }

  public save(containerName: string, key: string): PersistenceRecord {
    const state = this.getState(containerName);
    if (state === undefined) {
      throw new StateValidationException(`Cannot save non-existent state container '${containerName}'.`);
    }
    return this._persistenceManager.save(containerName, key, state);
  }

  public load<T = unknown>(containerName: string, key: string): T | undefined {
    const state = this._persistenceManager.load<T>(containerName, key);
    if (state !== undefined) {
      this.setState(containerName, state);
    }
    return state;
  }

  public synchronize(sourceName: string, targetName: string): SynchronizationRecord {
    const src = this.getContainer(sourceName);
    const tgt = this.getContainer(targetName);
    if (!src || !tgt) {
      throw new StateValidationException('Source and target containers must exist for synchronization.');
    }
    return this._synchronizer.synchronize(src, tgt);
  }

  public certify(): StateCertification {
    return this._certifier.certify(this);
  }

  public runCertification(): CertificationReport {
    return this._certifier.runCertification(this);
  }

  public certificationReport(): CertificationReport {
    return this._certifier.certificationReport(this);
  }

  private notifySubscribers<T>(containerName: string, state: T): void {
    const subMap = this._subscribers.get(containerName);
    if (subMap) {
      for (const handler of subMap.values()) {
        try {
          handler(state);
        } catch {
          // Exception isolation guarantee
        }
      }
    }
  }
}
