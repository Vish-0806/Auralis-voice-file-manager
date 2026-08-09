import type {
  PluginLoadResult,
  PluginModule,
  PluginLoadStatusValue,
  PluginLoaderStatistics,
  PluginLoaderHealth,
  PluginLoadRecord
} from '../models/loader';

export interface IPluginModuleLoader {
  load(entryPoint: string): Promise<unknown>;
}

export interface IPluginLoader {
  load(pluginId: string): Promise<PluginLoadResult>;
  loadAll(): Promise<ReadonlyArray<PluginLoadResult>>;
  unload(pluginId: string): PluginLoadResult;
  unloadAll(): ReadonlyArray<PluginLoadResult>;
  isLoaded(pluginId: string): boolean;
  getLoaded(pluginId: string): PluginModule | null;
  getLoadStatus(pluginId: string): PluginLoadStatusValue;
  listLoaded(): ReadonlyArray<PluginModule>;
  statistics(): PluginLoaderStatistics;
  health(): PluginLoaderHealth;
  diagnostics(): Record<string, any>;
  loadHistory(): ReadonlyArray<PluginLoadRecord>;
  clearLoadHistory(): void;
  reset(): void;
}
