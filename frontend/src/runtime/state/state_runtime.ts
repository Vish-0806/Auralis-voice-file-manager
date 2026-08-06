/**
 * State Runtime Coordinator Implementation (Phase 16.5).
 *
 * Implements IStateRuntime acting as central coordinator delegating to IStateProvider.
 */

import {
  Action,
  CertificationReport,
  PersistenceRecord,
  RedoRecord,
  Selector,
  SelectorResult,
  StateCapabilities,
  StateCertification,
  StateContainer,
  StateDiagnostics,
  StateHealth,
  StateStatistics,
  Subscription,
  SynchronizationRecord,
  UndoRecord,
} from './models';
import { IStateProvider, IStateRuntime } from './interfaces';
import { StateProvider } from './state_provider';

export class StateRuntime implements IStateRuntime {
  private readonly _provider: IStateProvider;

  constructor(provider?: IStateProvider) {
    this._provider = provider ?? new StateProvider();
  }

  public initialize(): StateHealth {
    return this._provider.initialize();
  }

  public shutdown(): StateHealth {
    return this._provider.shutdown();
  }

  public restart(): StateHealth {
    return this._provider.restart();
  }

  public provider(): IStateProvider {
    return this._provider;
  }

  public health(): StateHealth {
    return this._provider.health();
  }

  public statistics(): StateStatistics {
    return this._provider.statistics();
  }

  public capabilities(): StateCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): StateDiagnostics {
    return this._provider.diagnostics();
  }

  public createContainer<T = unknown>(name: string, initialState: T): StateContainer<T> {
    return this._provider.createContainer<T>(name, initialState);
  }

  public getContainer<T = unknown>(name: string): StateContainer<T> | undefined {
    return this._provider.getContainer<T>(name);
  }

  public setState<T = unknown>(name: string, state: T): StateContainer<T> {
    return this._provider.setState<T>(name, state);
  }

  public getState<T = unknown>(name: string): T | undefined {
    return this._provider.getState<T>(name);
  }

  public subscribe<T = unknown>(containerName: string, handler: (state: T) => void | Promise<void>): Subscription {
    return this._provider.subscribe<T>(containerName, handler);
  }

  public unsubscribe(subscriptionId: string): boolean {
    return this._provider.unsubscribe(subscriptionId);
  }

  public dispatch<T = unknown>(type: string, payload: T): Action<T> {
    return this._provider.dispatch<T>(type, payload);
  }

  public registerReducer<S = unknown, A = Action>(name: string, reduce: (state: S, action: A) => S): void {
    this._provider.registerReducer<S, A>(name, reduce);
  }

  public registerSelector<S = unknown, R = unknown>(name: string, select: (state: S) => R): Selector<S, R> {
    return this._provider.registerSelector<S, R>(name, select);
  }

  public select<S = unknown, R = unknown>(selectorId: string, state: S): SelectorResult<R> {
    return this._provider.select<S, R>(selectorId, state);
  }

  public undo<T = unknown>(): UndoRecord<T> | undefined {
    return this._provider.undo<T>();
  }

  public redo<T = unknown>(): RedoRecord<T> | undefined {
    return this._provider.redo<T>();
  }

  public save(containerName: string, key: string): PersistenceRecord {
    return this._provider.save(containerName, key);
  }

  public load<T = unknown>(containerName: string, key: string): T | undefined {
    return this._provider.load<T>(containerName, key);
  }

  public synchronize(sourceName: string, targetName: string): SynchronizationRecord {
    return this._provider.synchronize(sourceName, targetName);
  }

  public certify(): StateCertification {
    return this._provider.certify();
  }

  public runCertification(): CertificationReport {
    return this._provider.runCertification();
  }

  public certificationReport(): CertificationReport {
    return this._provider.certificationReport();
  }
}
