import type { PluginManifest } from '../models/manifest';
import type {
  PluginDependencyGraph,
  DependencyResolutionResult,
  DependencyResolutionStatistics,
  DependencyResolutionHealth
} from '../models/dependency';

export interface IPluginDependencyResolver {
  resolve(manifests: ReadonlyArray<PluginManifest>): DependencyResolutionResult;
  resolveAll(): DependencyResolutionResult;
  resolvePlugin(pluginId: string): DependencyResolutionResult;
  
  graph(): PluginDependencyGraph;
  dependenciesOf(pluginId: string): ReadonlyArray<string>;
  dependentsOf(pluginId: string): ReadonlyArray<string>;
  
  statistics(): DependencyResolutionStatistics;
  health(): DependencyResolutionHealth;
  reset(): void;
}
