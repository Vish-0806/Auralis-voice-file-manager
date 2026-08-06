/**
 * State Management Runtime Interfaces (Phase 16.5).
 *
 * Defines explicit contracts for IStateContainer, IStore, IStateRegistry,
 * IActionDispatcher, IReducerEngine, IMiddlewareManager, ISelectorEngine,
 * ISubscriptionManager, IHistoryManager, IPersistenceManager, ISynchronizer,
 * IStateCertifier, IStateProvider, and IStateRuntime.
 */

import {
  Action,
  CertificationReport,
  MiddlewareExecution,
  PersistenceRecord,
  Reducer,
  ReducerExecution,
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
  StateHistory,
  StateSnapshot,
  StateStatistics,
  StoreHealth,
  StoreSnapshot,
  StoreStatistics,
  Subscription,
  SynchronizationRecord,
  UndoRecord,
} from './models';

export interface IStateContainer<T = unknown> {
  getState(): T;
  setState(newState: T): StateContainer<T>;
  replaceState(newState: T): StateContainer<T>;
  mergeState(partialState: Partial<T>): StateContainer<T>;
  resetState(): StateContainer<T>;
  cloneState(): T;
  freezeState(): T;
  getContainer(): StateContainer<T>;
}

export interface IStore {
  createContainer<T = unknown>(name: string, initialState: T): StateContainer<T>;
  getContainer<T = unknown>(name: string): StateContainer<T> | undefined;
  removeContainer(name: string): boolean;
  listContainers(): ReadonlyArray<StateContainer>;
  snapshotStore(): StoreSnapshot;
  statistics(): StoreStatistics;
  health(): StoreHealth;
}

export interface IStateRegistry {
  registerStore(storeId: string, store: IStore): void;
  unregisterStore(storeId: string): boolean;
  getStore(storeId: string): IStore | undefined;
  listStores(): ReadonlyArray<string>;
  registerContainer<T = unknown>(container: StateContainer<T>): void;
  unregisterContainer(name: string): boolean;
  getContainer<T = unknown>(name: string): StateContainer<T> | undefined;
  listContainers(): ReadonlyArray<StateContainer>;
  clear(): void;
}

export interface IActionDispatcher {
  registerAction(type: string): void;
  dispatch<T = unknown>(action: Action<T>): Action<T>;
  dispatchAsync<T = unknown>(action: Action<T>): Promise<Action<T>>;
  listActions(): ReadonlyArray<string>;
  history(): ReadonlyArray<Action>;
  clearHistory(): void;
}

export interface IReducerEngine {
  registerReducer<S = unknown, A = Action>(reducer: Reducer<S, A>): void;
  removeReducer(reducerId: string): boolean;
  executeReducers<S = unknown, A = Action>(state: S, action: A): { newState: S; executions: ReadonlyArray<ReducerExecution> };
  listReducers(): ReadonlyArray<Reducer>;
}

export interface IMiddlewareManager {
  registerBefore(id: string, fn: (action: Action) => void | Promise<void>): void;
  registerAfter(id: string, fn: (action: Action) => void | Promise<void>): void;
  registerError(id: string, fn: (action: Action, error: Error) => void): void;
  executeBefore(action: Action): ReadonlyArray<MiddlewareExecution>;
  executeAfter(action: Action): ReadonlyArray<MiddlewareExecution>;
  executeError(action: Action, error: Error): ReadonlyArray<MiddlewareExecution>;
}

export interface ISelectorEngine {
  registerSelector<S = unknown, R = unknown>(selector: Selector<S, R>): void;
  evaluate<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R>;
  clearCache(): void;
}

export interface ISubscriptionManager {
  subscribe<T = unknown>(containerId: string, handler: (state: T) => void | Promise<void>): Subscription;
  unsubscribe(subscriptionId: string): boolean;
  notify<T = unknown>(containerId: string, state: T): void;
  listSubscriptions(containerId?: string): ReadonlyArray<Subscription>;
  clear(): void;
}

export interface IHistoryManager<T = unknown> {
  pushSnapshot(containerId: string, state: T): StateSnapshot<T>;
  undo(): UndoRecord<T> | undefined;
  redo(): RedoRecord<T> | undefined;
  canUndo(): boolean;
  canRedo(): boolean;
  history(): StateHistory<T>;
  clearHistory(): void;
}

export interface IPersistenceManager {
  save<T = unknown>(containerId: string, key: string, state: T): PersistenceRecord;
  load<T = unknown>(containerId: string, key: string): T | undefined;
  clear(containerId?: string): void;
  snapshot(): ReadonlyArray<PersistenceRecord>;
}

export interface ISynchronizer {
  synchronize<T = unknown>(source: StateContainer<T>, target: StateContainer<T>): SynchronizationRecord;
}

export interface IStateCertifier {
  certify(provider: IStateProvider): StateCertification;
  runCertification(provider: IStateProvider): CertificationReport;
  certificationReport(provider: IStateProvider): CertificationReport;
}

export interface IStateProvider {
  initialize(): StateHealth;
  shutdown(): StateHealth;
  restart(): StateHealth;
  health(): StateHealth;
  statistics(): StateStatistics;
  capabilities(): StateCapabilities;
  diagnostics(): StateDiagnostics;
  configuration(): StateConfiguration;
  context(): StateContext;

  createContainer<T = unknown>(name: string, initialState: T): StateContainer<T>;
  getContainer<T = unknown>(name: string): StateContainer<T> | undefined;
  setState<T = unknown>(name: string, state: T): StateContainer<T>;
  getState<T = unknown>(name: string): T | undefined;
  subscribe<T = unknown>(containerName: string, handler: (state: T) => void | Promise<void>): Subscription;
  unsubscribe(subscriptionId: string): boolean;

  dispatch<T = unknown>(type: string, payload: T): Action<T>;
  registerReducer<S = unknown, A = Action>(name: string, reduce: (state: S, action: A) => S): void;
  registerSelector<S = unknown, R = unknown>(name: string, select: (state: S) => R): Selector<S, R>;
  select<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R>;

  undo<T = unknown>(): UndoRecord<T> | undefined;
  redo<T = unknown>(): RedoRecord<T> | undefined;
  save(containerName: string, key: string): PersistenceRecord;
  load<T = unknown>(containerName: string, key: string): T | undefined;

  synchronize(sourceName: string, targetName: string): SynchronizationRecord;

  certify(): StateCertification;
  runCertification(): CertificationReport;
  certificationReport(): CertificationReport;
}

export interface IStateRuntime {
  initialize(): StateHealth;
  shutdown(): StateHealth;
  restart(): StateHealth;
  provider(): IStateProvider;
  health(): StateHealth;
  statistics(): StateStatistics;
  capabilities(): StateCapabilities;
  diagnostics(): StateDiagnostics;

  createContainer<T = unknown>(name: string, initialState: T): StateContainer<T>;
  getContainer<T = unknown>(name: string): StateContainer<T> | undefined;
  setState<T = unknown>(name: string, state: T): StateContainer<T>;
  getState<T = unknown>(name: string): T | undefined;
  subscribe<T = unknown>(containerName: string, handler: (state: T) => void | Promise<void>): Subscription;
  unsubscribe(subscriptionId: string): boolean;

  dispatch<T = unknown>(type: string, payload: T): Action<T>;
  registerReducer<S = unknown, A = Action>(name: string, reduce: (state: S, action: A) => S): void;
  registerSelector<S = unknown, R = unknown>(name: string, select: (state: S) => R): Selector<S, R>;
  select<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R>;

  undo<T = unknown>(): UndoRecord<T> | undefined;
  redo<T = unknown>(): RedoRecord<T> | undefined;
  save(containerName: string, key: string): PersistenceRecord;
  load<T = unknown>(containerName: string, key: string): T | undefined;

  synchronize(sourceName: string, targetName: string): SynchronizationRecord;

  certify(): StateCertification;
  runCertification(): CertificationReport;
  certificationReport(): CertificationReport;
}
