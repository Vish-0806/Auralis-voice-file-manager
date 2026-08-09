import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';
import type { IPluginLoader, IPluginModuleLoader } from '../interfaces/plugin-loader';
import {
  type PluginLoadResult,
  type PluginModule,
  type PluginLoaderStatistics,
  type PluginLoaderHealth,
  type PluginLoadRecord,
  PluginLoadStatus,
  type PluginLoadStatusValue
} from '../models/loader';
import { PluginLoadError, PluginModuleValidationError, PluginStateError } from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class DefaultPluginModuleLoader implements IPluginModuleLoader {
  public async load(entryPoint: string): Promise<unknown> {
    // Dynamic import compliant with Vite
    return import(/* @vite-ignore */ entryPoint);
  }
}

export class PluginLoader implements IPluginLoader {
  private readonly loadedModules = new Map<string, PluginModule>();
  private readonly loadStatuses = new Map<string, PluginLoadStatusValue>();
  private readonly inFlightLoads = new Map<string, Promise<PluginLoadResult>>();
  private readonly loadHistoryRecords: PluginLoadRecord[] = [];
  private readonly loadDurations: number[] = [];

  private loadAttemptsCount = 0;
  private successfulLoadsCount = 0;
  private failedLoadsCount = 0;
  private unloadAttemptsCount = 0;
  private successfulUnloadsCount = 0;
  private failedUnloadsCount = 0;
  private duplicateLoadAttemptsCount = 0;
  private maxHistorySize = 100;

  constructor(
    private readonly discoveryManager: IPluginDiscoveryManager,
    private readonly dependencyResolver: IPluginDependencyResolver,
    private readonly moduleLoader: IPluginModuleLoader = new DefaultPluginModuleLoader(),
    options?: { maxHistorySize?: number }
  ) {
    if (options?.maxHistorySize !== undefined) {
      this.maxHistorySize = options.maxHistorySize;
    }
  }

  public async load(pluginId: string): Promise<PluginLoadResult> {
    const startTime = Date.now();
    this.loadAttemptsCount += 1;

    // 1. Duplicate load prevention
    if (this.isLoaded(pluginId)) {
      this.duplicateLoadAttemptsCount += 1;
      const duration = Date.now() - startTime;
      const result: PluginLoadResult = {
        pluginId,
        status: PluginLoadStatus.LOADED,
        success: false,
        loadDuration: duration,
        error: {
          message: `Plugin '${pluginId}' is already loaded.`
        },
        warnings: [],
        timestamp: Date.now()
      };
      this.recordLoadHistory(pluginId, PluginLoadStatus.LOADED, startTime, Date.now(), false, result.error);
      return freezeDeepSafe(result);
    }

    // 2. Concurrent loading protection
    if (this.loadStatuses.get(pluginId) === PluginLoadStatus.LOADING) {
      const inFlight = this.inFlightLoads.get(pluginId);
      if (inFlight) {
        return inFlight;
      }
    }

    this.loadStatuses.set(pluginId, PluginLoadStatus.LOADING);

    const loadPromise = (async () => {
      try {
        const manifest = this.discoveryManager.find(pluginId);
        if (!manifest) {
          throw new PluginLoadError(`Plugin '${pluginId}' not found in discovery scanner.`, pluginId);
        }

        if (!manifest.entryPoint) {
          throw new PluginLoadError(`Plugin '${pluginId}' manifest does not specify an entryPoint.`, pluginId);
        }

        // Dependency validation
        for (const dep of manifest.dependencies) {
          if (!dep.optional) {
            const depStatus = this.getLoadStatus(dep.id);
            if (depStatus !== PluginLoadStatus.LOADED) {
              throw new PluginLoadError(`Cannot load plugin '${pluginId}' because required dependency '${dep.id}' is not loaded (status: ${depStatus}).`, pluginId);
            }
          }
        }

        const rawModule = await this.moduleLoader.load(manifest.entryPoint);
        if (!rawModule || (typeof rawModule !== 'object' && typeof rawModule !== 'function')) {
          throw new PluginModuleValidationError(`Plugin '${pluginId}' entryPoint did not return a valid module object.`, pluginId);
        }

        const endTime = Date.now();
        const duration = endTime - startTime;
        this.loadDurations.push(duration);

        const pluginModule: PluginModule = {
          pluginId,
          version: manifest.version,
          entryPoint: manifest.entryPoint,
          loadedAt: endTime,
          module: rawModule
        };

        this.loadedModules.set(pluginId, pluginModule);
        this.loadStatuses.set(pluginId, PluginLoadStatus.LOADED);
        this.successfulLoadsCount += 1;

        const result: PluginLoadResult = {
          pluginId,
          status: PluginLoadStatus.LOADED,
          success: true,
          loadDuration: duration,
          warnings: [],
          resolvedEntryPoint: manifest.entryPoint,
          timestamp: endTime
        };

        this.recordLoadHistory(pluginId, PluginLoadStatus.LOADED, startTime, endTime, true);
        return freezeDeepSafe(result);

      } catch (err: any) {
        const endTime = Date.now();
        const duration = endTime - startTime;
        this.loadStatuses.set(pluginId, PluginLoadStatus.FAILED);
        this.failedLoadsCount += 1;

        const errorMsg = err instanceof Error ? err.message : String(err);
        const errorStack = err instanceof Error ? err.stack : undefined;

        const result: PluginLoadResult = {
          pluginId,
          status: PluginLoadStatus.FAILED,
          success: false,
          loadDuration: duration,
          error: {
            message: errorMsg,
            stack: errorStack
          },
          warnings: [],
          timestamp: endTime
        };

        this.recordLoadHistory(pluginId, PluginLoadStatus.FAILED, startTime, endTime, false, result.error);
        return freezeDeepSafe(result);
      } finally {
        this.inFlightLoads.delete(pluginId);
      }
    })();

    this.inFlightLoads.set(pluginId, loadPromise);
    return loadPromise;
  }

  public async loadAll(): Promise<ReadonlyArray<PluginLoadResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    if (!resolution.plan) {
      return Object.freeze([]);
    }

    const results: PluginLoadResult[] = [];
    for (const pluginId of resolution.plan.order) {
      const result = await this.load(pluginId);
      results.push(result);
    }

    return Object.freeze(results);
  }

  public unload(pluginId: string): PluginLoadResult {
    const startTime = Date.now();
    this.unloadAttemptsCount += 1;

    if (!this.isLoaded(pluginId)) {
      this.failedUnloadsCount += 1;
      throw new PluginStateError(`Plugin '${pluginId}' is not loaded.`);
    }

    this.loadStatuses.set(pluginId, PluginLoadStatus.UNLOADING);
    this.loadedModules.delete(pluginId);
    this.loadStatuses.set(pluginId, PluginLoadStatus.UNLOADED);
    this.successfulUnloadsCount += 1;

    const duration = Date.now() - startTime;
    const result: PluginLoadResult = {
      pluginId,
      status: PluginLoadStatus.UNLOADED,
      success: true,
      loadDuration: duration,
      warnings: [],
      timestamp: Date.now()
    };

    this.recordLoadHistory(pluginId, PluginLoadStatus.UNLOADED, startTime, Date.now(), true);
    return freezeDeepSafe(result);
  }

  public unloadAll(): ReadonlyArray<PluginLoadResult> {
    const loadedIds = Array.from(this.loadedModules.keys());
    const results: PluginLoadResult[] = [];
    for (const id of loadedIds) {
      results.push(this.unload(id));
    }
    return Object.freeze(results);
  }

  public isLoaded(pluginId: string): boolean {
    return this.loadedModules.has(pluginId);
  }

  public getLoaded(pluginId: string): PluginModule | null {
    return this.loadedModules.get(pluginId) || null;
  }

  public getLoadStatus(pluginId: string): PluginLoadStatusValue {
    return this.loadStatuses.get(pluginId) || PluginLoadStatus.NOT_LOADED;
  }

  public listLoaded(): ReadonlyArray<PluginModule> {
    return Object.freeze(Array.from(this.loadedModules.values()));
  }

  public statistics(): PluginLoaderStatistics {
    const avg = this.loadDurations.length > 0
      ? this.loadDurations.reduce((a, b) => a + b, 0) / this.loadDurations.length
      : 0;
    const max = this.loadDurations.length > 0
      ? Math.max(...this.loadDurations)
      : 0;
    const min = this.loadDurations.length > 0
      ? Math.min(...this.loadDurations)
      : 0;

    return Object.freeze({
      loadAttempts: this.loadAttemptsCount,
      successfulLoads: this.successfulLoadsCount,
      failedLoads: this.failedLoadsCount,
      unloadAttempts: this.unloadAttemptsCount,
      successfulUnloads: this.successfulUnloadsCount,
      failedUnloads: this.failedUnloadsCount,
      duplicateLoadAttempts: this.duplicateLoadAttemptsCount,
      activeLoadedPlugins: this.loadedModules.size,
      averageLoadTime: avg,
      maximumLoadTime: max,
      minimumLoadTime: min
    });
  }

  public health(): PluginLoaderHealth {
    const totalFinishedLoads = this.successfulLoadsCount + this.failedLoadsCount;
    const failureRate = totalFinishedLoads > 0
      ? this.failedLoadsCount / totalFinishedLoads
      : 0;
    const failedPlugins = Array.from(this.loadStatuses.entries())
      .filter(([_, status]) => status === PluginLoadStatus.FAILED).length;

    const healthy = failedPlugins === 0;

    return Object.freeze({
      healthy,
      loadedPlugins: this.loadedModules.size,
      failedPlugins,
      activeLoads: this.inFlightLoads.size,
      failureRate,
      message: healthy
        ? 'Loader healthy'
        : `Loader has ${failedPlugins} failed plugins.`
    });
  }

  public diagnostics(): Record<string, any> {
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health(),
      loadStatuses: Object.fromEntries(this.loadStatuses),
      loadedPluginIds: Array.from(this.loadedModules.keys())
    });
  }

  public loadHistory(): ReadonlyArray<PluginLoadRecord> {
    return Object.freeze([...this.loadHistoryRecords]);
  }

  public clearLoadHistory(): void {
    this.loadHistoryRecords.length = 0;
  }

  public reset(): void {
    this.loadedModules.clear();
    this.loadStatuses.clear();
    this.inFlightLoads.clear();
    this.loadHistoryRecords.length = 0;
    this.loadAttemptsCount = 0;
    this.successfulLoadsCount = 0;
    this.failedLoadsCount = 0;
    this.unloadAttemptsCount = 0;
    this.successfulUnloadsCount = 0;
    this.failedUnloadsCount = 0;
    this.duplicateLoadAttemptsCount = 0;
    this.loadDurations.length = 0;
  }

  private recordLoadHistory(
    pluginId: string,
    status: PluginLoadStatusValue,
    startedAt: number,
    completedAt: number,
    success: boolean,
    error?: { message: string }
  ): void {
    const record: PluginLoadRecord = {
      pluginId,
      status,
      startedAt,
      completedAt,
      duration: completedAt - startedAt,
      success,
      error
    };
    this.loadHistoryRecords.push(Object.freeze(record));
    if (this.loadHistoryRecords.length > this.maxHistorySize) {
      this.loadHistoryRecords.shift();
    }
  }
}
