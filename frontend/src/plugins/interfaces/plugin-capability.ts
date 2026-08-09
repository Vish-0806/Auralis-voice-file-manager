import type {
  PluginCapability,
  PluginCapabilityRegistration,
  PluginCapabilityResult,
  PluginCapabilityTypeValue,
  ExtensionPoint,
  ExtensionRegistration,
  ExtensionResult,
  CapabilityStatistics,
  CapabilityHealth,
  CapabilityDiagnostics,
  ExtensionStatistics,
  ExtensionHealth
} from '../models/capability';

export interface IPluginCapabilityManager {
  registerCapability(pluginId: string, registration: PluginCapabilityRegistration): PluginCapabilityResult;
  unregisterCapability(pluginId: string, capabilityId: string): PluginCapabilityResult;
  unregisterPluginCapabilities(pluginId: string): void;
  findCapability(capabilityId: string): PluginCapability | null;
  findCapabilitiesByPlugin(pluginId: string): ReadonlyArray<PluginCapability>;
  findCapabilitiesByType(type: PluginCapabilityTypeValue): ReadonlyArray<PluginCapability>;
  containsCapability(capabilityId: string): boolean;
  listCapabilities(): ReadonlyArray<PluginCapability>;
  enableCapability(capabilityId: string): void;
  disableCapability(capabilityId: string): void;
  statistics(): CapabilityStatistics;
  health(): CapabilityHealth;
  diagnostics(): CapabilityDiagnostics;
  reset(): void;
}

export interface IPluginExtensionManager {
  registerExtensionPoint(pluginId: string, point: Omit<ExtensionPoint, 'enabled'>): void;
  unregisterExtensionPoint(pluginId: string, pointId: string): void;
  findExtensionPoint(pointId: string): ExtensionPoint | null;
  listExtensionPoints(): ReadonlyArray<ExtensionPoint>;
  
  registerExtension(pluginId: string, extension: Omit<ExtensionRegistration, 'pluginId' | 'enabled' | 'registeredAt'>): ExtensionResult;
  unregisterExtension(pluginId: string, extensionId: string): ExtensionResult;
  unregisterPluginExtensions(pluginId: string): void;
  
  findExtension(extensionId: string): ExtensionRegistration | null;
  findExtensions(pointId: string): ReadonlyArray<ExtensionRegistration>;
  findExtensionsByPlugin(pluginId: string): ReadonlyArray<ExtensionRegistration>;
  findExtensionsByPoint(pointId: string): ReadonlyArray<ExtensionRegistration>;
  
  enableExtension(extensionId: string): void;
  disableExtension(extensionId: string): void;
  statistics(): ExtensionStatistics;
  health(): ExtensionHealth;
  diagnostics(): Record<string, any>;
  reset(): void;
}
