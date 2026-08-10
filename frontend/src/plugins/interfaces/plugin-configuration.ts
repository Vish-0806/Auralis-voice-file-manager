import type {
  PluginConfigurationSchema,
  PluginConfiguration,
  PluginConfigurationProfile,
  PluginConfigurationOverride,
  PluginConfigurationChange,
  PluginConfigurationValidationResult,
  PluginConfigurationStatistics,
  PluginConfigurationHealth,
  PluginConfigurationDiagnostics
} from '../models/configuration';

export interface IPluginConfigurationStore {
  read(pluginId: string): Promise<PluginConfiguration | null>;
  write(pluginId: string, config: PluginConfiguration): Promise<void>;
  remove(pluginId: string): Promise<void>;
  exists(pluginId: string): Promise<boolean>;
}

export interface IPluginConfigurationManager {
  registerSchema(pluginId: string, schema: Omit<PluginConfigurationSchema, 'pluginId' | 'createdAt' | 'updatedAt'>): PluginConfigurationSchema;
  removeSchema(pluginId: string): void;
  getSchema(pluginId: string): PluginConfigurationSchema | null;
  listSchemas(): ReadonlyArray<PluginConfigurationSchema>;
  
  createConfiguration(pluginId: string, values: Record<string, any>): PluginConfiguration;
  getConfiguration(pluginId: string): PluginConfiguration | null;
  updateConfiguration(pluginId: string, values: Record<string, any>): PluginConfiguration;
  resetConfiguration(pluginId: string): void;
  validateConfiguration(pluginId: string, values: Record<string, any>): PluginConfigurationValidationResult;
  
  getConfigurationValue(pluginId: string, key: string): any;
  setConfigurationValue(pluginId: string, key: string, value: any): void;
  removeConfigurationValue(pluginId: string, key: string): void;
  
  createProfile(pluginId: string, profile: Omit<PluginConfigurationProfile, 'pluginId' | 'createdAt' | 'updatedAt'>): PluginConfigurationProfile;
  removeProfile(pluginId: string, profileId: string): void;
  activateProfile(pluginId: string, profileId: string): void;
  getProfile(pluginId: string, profileId: string): PluginConfigurationProfile | null;
  listProfiles(pluginId: string): ReadonlyArray<PluginConfigurationProfile>;
  
  registerOverride(pluginId: string, override: Omit<PluginConfigurationOverride, 'overrideId' | 'pluginId' | 'createdAt'>): PluginConfigurationOverride;
  removeOverride(pluginId: string, overrideId: string): void;
  listOverrides(pluginId: string): ReadonlyArray<PluginConfigurationOverride>;
  
  resolveConfiguration(pluginId: string): Record<string, any>;
  configurationHistory(pluginId?: string): ReadonlyArray<PluginConfigurationChange>;
  
  importConfiguration(pluginId: string, payload: Record<string, any>, options?: { allowSensitive?: boolean }): void;
  exportConfiguration(pluginId: string, options?: { allowSensitive?: boolean }): Record<string, any>;
  
  statistics(): PluginConfigurationStatistics;
  health(): PluginConfigurationHealth;
  diagnostics(): PluginConfigurationDiagnostics;
  reset(): void;
}
