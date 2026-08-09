import type {
  PluginDiscoverySourceDescriptor,
  PluginManifest,
  PluginDiscoveryResult,
  PluginDiscoveryStatistics,
  PluginDiscoveryHealth
} from '../models/manifest';

export interface IPluginDiscoverySource {
  readonly descriptor: PluginDiscoverySourceDescriptor;
  discover(): Promise<ReadonlyArray<unknown>>;
}

export interface IPluginDiscoveryManager {
  registerSource(source: IPluginDiscoverySource): void;
  unregisterSource(sourceId: string): void;
  getSources(): ReadonlyArray<IPluginDiscoverySource>;
  
  discover(): Promise<PluginDiscoveryResult>;
  discoverFromSource(sourceId: string): Promise<PluginDiscoveryResult>;
  
  find(pluginId: string): PluginManifest | null;
  findAll(): ReadonlyArray<PluginManifest>;
  contains(pluginId: string): boolean;
  remove(pluginId: string): boolean;
  clear(): void;
  
  statistics(): PluginDiscoveryStatistics;
  health(): PluginDiscoveryHealth;
  reset(): void;
}
