import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';
import type { IPluginLoader } from '../interfaces/plugin-loader';
import type { IPluginLifecycleManager, PluginLifecycleHooks } from '../interfaces/plugin-lifecycle';
import {
  type PluginLifecycleResult,
  type PluginLifecycleRecord,
  type PluginLifecycleStatistics,
  type PluginLifecycleHealth,
  type PluginLifecycleDiagnostics,
  type PluginLifecycleHookContext,
  PluginLifecycleOperation,
  type PluginLifecycleOperationValue
} from '../models/lifecycle';
import { PluginState, type PluginStateValue } from '../models/plugin-state';
import { PluginLoadStatus } from '../models/loader';
import {
  PluginStateError,
  PluginLifecycleError,
  PluginLifecycleTransitionError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginLifecycleManager implements IPluginLifecycleManager {
  private readonly pluginStates = new Map<string, PluginStateValue>();
  private readonly registeredHooks = new Map<string, PluginLifecycleHooks>();
  private readonly inFlightOps = new Map<string, Promise<PluginLifecycleResult>>();
  private readonly historyRecords: PluginLifecycleRecord[] = [];
  private readonly opDurations: number[] = [];

  private initializeAttempts = 0;
  private activationAttempts = 0;
  private deactivationAttempts = 0;
  private disposalAttempts = 0;
  private successOps = 0;
  private failOps = 0;
  private maxHistorySize = 100;

  constructor(
    private readonly discoveryManager: IPluginDiscoveryManager,
    private readonly dependencyResolver: IPluginDependencyResolver,
    private readonly loader: IPluginLoader,
    options?: { maxHistorySize?: number }
  ) {
    if (options?.maxHistorySize !== undefined) {
      this.maxHistorySize = options.maxHistorySize;
    }
  }

  public getLifecycleState(pluginId: string): PluginStateValue {
    const state = this.pluginStates.get(pluginId);
    if (state) {
      return state;
    }
    // Fallback to loader states
    const loadStatus = this.loader.getLoadStatus(pluginId);
    if (loadStatus === PluginLoadStatus.LOADED) {
      return PluginState.LOADED;
    }
    if (loadStatus === PluginLoadStatus.LOADING) {
      return PluginState.LOADING;
    }
    if (loadStatus === PluginLoadStatus.FAILED) {
      return PluginState.FAILED;
    }
    return PluginState.UNLOADED;
  }

  public registerHooks(pluginId: string, hooks: PluginLifecycleHooks): void {
    if (this.registeredHooks.has(pluginId)) {
      throw new PluginLifecycleError(`Hooks are already registered for plugin '${pluginId}'`, pluginId);
    }
    this.registeredHooks.set(pluginId, hooks);
  }

  public unregisterHooks(pluginId: string): void {
    this.registeredHooks.delete(pluginId);
  }

  public async initializePlugin(pluginId: string): Promise<PluginLifecycleResult> {
    return this.runOperation(pluginId, PluginLifecycleOperation.INITIALIZE, async () => {
      this.initializeAttempts += 1;
      const currentState = this.getLifecycleState(pluginId);

      // Validate transition
      if (currentState !== PluginState.LOADED && currentState !== PluginState.REGISTERED) {
        throw new PluginLifecycleTransitionError(
          `Cannot initialize plugin '${pluginId}' from state: ${currentState}`,
          pluginId,
          currentState,
          PluginState.INITIALIZING
        );
      }

      // Verify dependency resolution initialization state
      const manifest = this.discoveryManager.find(pluginId);
      if (manifest) {
        for (const dep of manifest.dependencies) {
          if (!dep.optional) {
            const depState = this.getLifecycleState(dep.id);
            if (depState !== PluginState.DEACTIVATED && depState !== PluginState.ACTIVE && depState !== PluginState.READY) {
              throw new PluginLifecycleError(
                `Cannot initialize plugin '${pluginId}' because required dependency '${dep.id}' is not initialized (status: ${depState}).`,
                pluginId,
                PluginLifecycleOperation.INITIALIZE
              );
            }
          }
        }
      }

      this.pluginStates.set(pluginId, PluginState.INITIALIZING);

      // Execute hook
      const hooks = this.registeredHooks.get(pluginId);
      if (hooks?.onInitialize) {
        const context = this.createHookContext(pluginId, PluginLifecycleOperation.INITIALIZE, PluginState.INITIALIZING);
        await hooks.onInitialize(context);
      }

      this.pluginStates.set(pluginId, PluginState.DEACTIVATED);
      return PluginState.DEACTIVATED;
    });
  }

  public async activatePlugin(pluginId: string): Promise<PluginLifecycleResult> {
    return this.runOperation(pluginId, PluginLifecycleOperation.ACTIVATE, async () => {
      this.activationAttempts += 1;
      const currentState = this.getLifecycleState(pluginId);

      if (currentState !== PluginState.DEACTIVATED && currentState !== PluginState.INITIALIZING) {
        throw new PluginLifecycleTransitionError(
          `Cannot activate plugin '${pluginId}' from state: ${currentState}`,
          pluginId,
          currentState,
          PluginState.ACTIVE
        );
      }

      // Verify dependencies are active
      const manifest = this.discoveryManager.find(pluginId);
      if (manifest) {
        for (const dep of manifest.dependencies) {
          if (!dep.optional) {
            const depState = this.getLifecycleState(dep.id);
            if (depState !== PluginState.ACTIVE && depState !== PluginState.READY) {
              throw new PluginLifecycleError(
                `Cannot activate plugin '${pluginId}' because required dependency '${dep.id}' is not active (status: ${depState}).`,
                pluginId,
                PluginLifecycleOperation.ACTIVATE
              );
            }
          }
        }
      }

      const hooks = this.registeredHooks.get(pluginId);
      if (hooks?.onActivate) {
        const context = this.createHookContext(pluginId, PluginLifecycleOperation.ACTIVATE, currentState);
        await hooks.onActivate(context);
      }

      this.pluginStates.set(pluginId, PluginState.ACTIVE);
      return PluginState.ACTIVE;
    });
  }

  public async deactivatePlugin(pluginId: string): Promise<PluginLifecycleResult> {
    return this.runOperation(pluginId, PluginLifecycleOperation.DEACTIVATE, async () => {
      this.deactivationAttempts += 1;
      const currentState = this.getLifecycleState(pluginId);

      if (currentState !== PluginState.ACTIVE && currentState !== PluginState.READY) {
        throw new PluginLifecycleTransitionError(
          `Cannot deactivate plugin '${pluginId}' from state: ${currentState}`,
          pluginId,
          currentState,
          PluginState.DEACTIVATED
        );
      }

      this.pluginStates.set(pluginId, PluginState.DEACTIVATING);

      const hooks = this.registeredHooks.get(pluginId);
      if (hooks?.onDeactivate) {
        const context = this.createHookContext(pluginId, PluginLifecycleOperation.DEACTIVATE, PluginState.DEACTIVATING);
        await hooks.onDeactivate(context);
      }

      this.pluginStates.set(pluginId, PluginState.DEACTIVATED);
      return PluginState.DEACTIVATED;
    });
  }

  public async disposePlugin(pluginId: string): Promise<PluginLifecycleResult> {
    return this.runOperation(pluginId, PluginLifecycleOperation.DISPOSE, async () => {
      this.disposalAttempts += 1;
      const currentState = this.getLifecycleState(pluginId);

      if (currentState === PluginState.DISPOSED) {
        throw new PluginStateError(`Plugin '${pluginId}' is already disposed.`);
      }

      // If active, deactivate first
      if (currentState === PluginState.ACTIVE || currentState === PluginState.READY) {
        await this.deactivatePlugin(pluginId);
      }

      this.pluginStates.set(pluginId, PluginState.DISPOSING);

      const hooks = this.registeredHooks.get(pluginId);
      if (hooks?.onDispose) {
        const context = this.createHookContext(pluginId, PluginLifecycleOperation.DISPOSE, PluginState.DISPOSING);
        await hooks.onDispose(context);
      }

      this.pluginStates.set(pluginId, PluginState.DISPOSED);
      return PluginState.DISPOSED;
    });
  }

  public async initializeAll(): Promise<ReadonlyArray<PluginLifecycleResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    if (!resolution.plan) {
      return Object.freeze([]);
    }

    const results: PluginLifecycleResult[] = [];
    for (const pluginId of resolution.plan.order) {
      try {
        const result = await this.initializePlugin(pluginId);
        results.push(result);
      } catch (err: any) {
        // Isolation: keep going unless subsequent nodes depend on this
      }
    }
    return Object.freeze(results);
  }

  public async activateAll(): Promise<ReadonlyArray<PluginLifecycleResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    if (!resolution.plan) {
      return Object.freeze([]);
    }

    const results: PluginLifecycleResult[] = [];
    for (const pluginId of resolution.plan.order) {
      try {
        const result = await this.activatePlugin(pluginId);
        results.push(result);
      } catch (err: any) {
        // Isolation
      }
    }
    return Object.freeze(results);
  }

  public async deactivateAll(): Promise<ReadonlyArray<PluginLifecycleResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    if (!resolution.plan) {
      return Object.freeze([]);
    }

    // Reverse topological order
    const reverseOrder = [...resolution.plan.order].reverse();
    const results: PluginLifecycleResult[] = [];
    for (const pluginId of reverseOrder) {
      try {
        if (this.getLifecycleState(pluginId) === PluginState.ACTIVE || this.getLifecycleState(pluginId) === PluginState.READY) {
          const result = await this.deactivatePlugin(pluginId);
          results.push(result);
        }
      } catch (err: any) {
        // Isolation
      }
    }
    return Object.freeze(results);
  }

  public async disposeAll(): Promise<ReadonlyArray<PluginLifecycleResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    if (!resolution.plan) {
      return Object.freeze([]);
    }

    const reverseOrder = [...resolution.plan.order].reverse();
    const results: PluginLifecycleResult[] = [];
    for (const pluginId of reverseOrder) {
      try {
        const result = await this.disposePlugin(pluginId);
        results.push(result);
      } catch (err: any) {
        // Isolation
      }
    }
    return Object.freeze(results);
  }

  public history(): ReadonlyArray<PluginLifecycleRecord> {
    return Object.freeze([...this.historyRecords]);
  }

  public clearHistory(): void {
    this.historyRecords.length = 0;
  }

  public statistics(): PluginLifecycleStatistics {
    const avg = this.opDurations.length > 0
      ? this.opDurations.reduce((a, b) => a + b, 0) / this.opDurations.length
      : 0;
    const max = this.opDurations.length > 0 ? Math.max(...this.opDurations) : 0;
    const min = this.opDurations.length > 0 ? Math.min(...this.opDurations) : 0;

    const activeCount = Array.from(this.pluginStates.values())
      .filter(s => s === PluginState.ACTIVE || s === PluginState.READY).length;
    const disposedCount = Array.from(this.pluginStates.values())
      .filter(s => s === PluginState.DISPOSED).length;
    const failedCount = Array.from(this.pluginStates.values())
      .filter(s => s === PluginState.FAILED).length;

    return Object.freeze({
      initializeCount: this.initializeAttempts,
      activationCount: this.activationAttempts,
      deactivationCount: this.deactivationAttempts,
      disposalCount: this.disposalAttempts,
      successfulOperations: this.successOps,
      failedOperations: this.failOps,
      activePlugins: activeCount,
      disposedPlugins: disposedCount,
      failedPlugins: failedCount,
      averageLifecycleTime: avg,
      minimumLifecycleTime: min,
      maximumLifecycleTime: max,
      lifecycleHistorySize: this.historyRecords.length
    });
  }

  public health(): PluginLifecycleHealth {
    const totalOps = this.successOps + this.failOps;
    const successRate = totalOps > 0 ? this.successOps / totalOps : 1;
    const failureRate = totalOps > 0 ? this.failOps / totalOps : 0;

    const failedCount = Array.from(this.pluginStates.values())
      .filter(s => s === PluginState.FAILED).length;
    const activeCount = Array.from(this.pluginStates.values())
      .filter(s => s === PluginState.ACTIVE || s === PluginState.READY).length;

    const healthy = failedCount === 0 && failureRate === 0;

    return Object.freeze({
      healthy,
      successRate,
      failureRate,
      activePluginCount: activeCount,
      failedPluginCount: failedCount,
      message: healthy ? 'Lifecycle engine healthy' : `Lifecycle engine failure rate is ${(failureRate * 100).toFixed(1)}%`
    });
  }

  public diagnostics(): PluginLifecycleDiagnostics {
    const lastRec = this.historyRecords[this.historyRecords.length - 1];
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health(),
      currentActivePluginCount: this.statistics().activePlugins,
      lifecycleHistoryDepth: this.historyRecords.length,
      registeredLifecycleHookCount: this.registeredHooks.size,
      lastLifecycleOperationMetadata: lastRec ? {
        pluginId: lastRec.pluginId,
        operation: lastRec.operation,
        success: lastRec.success,
        timestamp: lastRec.completedAt
      } : undefined
    });
  }

  public reset(): void {
    this.pluginStates.clear();
    this.registeredHooks.clear();
    this.inFlightOps.clear();
    this.historyRecords.length = 0;
    this.opDurations.length = 0;
    this.initializeAttempts = 0;
    this.activationAttempts = 0;
    this.deactivationAttempts = 0;
    this.disposalAttempts = 0;
    this.successOps = 0;
    this.failOps = 0;
  }

  private async runOperation(
    pluginId: string,
    operation: PluginLifecycleOperationValue,
    action: () => Promise<PluginStateValue>
  ): Promise<PluginLifecycleResult> {
    const key = `${pluginId}:${operation}`;
    const inFlight = this.inFlightOps.get(key);
    if (inFlight) {
      return inFlight;
    }

    const promise = (async () => {
      const startTime = Date.now();
      const previousState = this.getLifecycleState(pluginId);
      const executionId = Math.random().toString(36).substring(2, 11);

      try {
        const resultingState = await action();
        const endTime = Date.now();
        const duration = endTime - startTime;
        this.opDurations.push(duration);
        this.successOps += 1;

        const result: PluginLifecycleResult = {
          pluginId,
          operation,
          previousState,
          currentState: resultingState,
          success: true,
          loadDuration: duration, // compatibility name
          warnings: [],
          timestamp: endTime
        } as any; // Cast as result has loadDuration mapped to duration

        this.recordHistory(executionId, pluginId, operation, previousState, resultingState, startTime, endTime, true);
        return freezeDeepSafe(result);
      } catch (err: any) {
        const endTime = Date.now();
        const duration = endTime - startTime;
        this.opDurations.push(duration);
        this.failOps += 1;
        this.pluginStates.set(pluginId, PluginState.FAILED);

        const errorMsg = err instanceof Error ? err.message : String(err);
        const errorStack = err instanceof Error ? err.stack : undefined;

        const result: PluginLifecycleResult = {
          pluginId,
          operation,
          previousState,
          currentState: PluginState.FAILED,
          success: false,
          loadDuration: duration,
          error: {
            message: errorMsg,
            stack: errorStack
          },
          warnings: [],
          timestamp: endTime
        } as any;

        this.recordHistory(executionId, pluginId, operation, previousState, PluginState.FAILED, startTime, endTime, false, result.error);
        throw err; // throw so hooks/chains can isolate
      } finally {
        this.inFlightOps.delete(key);
      }
    })();

    this.inFlightOps.set(key, promise);
    return promise;
  }

  private createHookContext(pluginId: string, operation: PluginLifecycleOperationValue, currentState: PluginStateValue): PluginLifecycleHookContext {
    const manifest = this.discoveryManager.find(pluginId);
    return freezeDeepSafe({
      pluginId,
      pluginVersion: manifest?.version || '0.0.0',
      currentLifecycleState: currentState,
      requestedOperation: operation,
      timestamp: Date.now(),
      executionId: Math.random().toString(36).substring(2, 11),
      dependencyInformation: manifest ? manifest.dependencies.map(d => d.id) : []
    });
  }

  private recordHistory(
    executionId: string,
    pluginId: string,
    operation: PluginLifecycleOperationValue,
    previousState: PluginStateValue,
    currentState: PluginStateValue,
    startedAt: number,
    completedAt: number,
    success: boolean,
    error?: { message: string }
  ): void {
    const record: PluginLifecycleRecord = {
      executionId,
      pluginId,
      operation,
      previousState,
      currentState,
      startedAt,
      completedAt,
      duration: completedAt - startedAt,
      success,
      error
    };
    this.historyRecords.push(Object.freeze(record));
    if (this.historyRecords.length > this.maxHistorySize) {
      this.historyRecords.shift();
    }
  }
}
