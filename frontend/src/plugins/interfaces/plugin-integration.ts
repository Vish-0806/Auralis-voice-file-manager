import type {
  PluginIntegrationResult,
  PluginIntegrationRecord,
  PluginIntegrationStatistics,
  PluginIntegrationHealth,
  PluginIntegrationDiagnostics,
  PluginIntegrationOptions
} from '../models/integration';

export interface IPluginIntegrationManager {
  integrate(pluginId: string, options?: PluginIntegrationOptions): Promise<PluginIntegrationResult>;
  integrateMany(pluginIds: ReadonlyArray<string>, options?: PluginIntegrationOptions): Promise<ReadonlyArray<PluginIntegrationResult>>;
  activate(pluginId: string): Promise<PluginIntegrationResult>;
  deactivate(pluginId: string): Promise<PluginIntegrationResult>;
  unload(pluginId: string): Promise<PluginIntegrationResult>;
  reload(pluginId: string, options?: PluginIntegrationOptions): Promise<PluginIntegrationResult>;
  startup(options?: PluginIntegrationOptions): Promise<ReadonlyArray<PluginIntegrationResult>>;
  shutdown(): Promise<ReadonlyArray<PluginIntegrationResult>>;
  getIntegrationStatus(pluginId: string): PluginIntegrationResult | null;
  integrationHistory(): ReadonlyArray<PluginIntegrationRecord>;
  statistics(): PluginIntegrationStatistics;
  health(): PluginIntegrationHealth;
  diagnostics(): PluginIntegrationDiagnostics;
  reset(): void;
}
