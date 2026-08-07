/**
 * Plugin Runtime Interfaces (Phase 16.7).
 *
 * Defines contract specifications for IPluginRegistry, IPluginManifestLoader,
 * IPluginLoader, IPluginLifecycleManager, IDependencyResolver, ICapabilityManager,
 * IServiceRegistry, IExtensionAPI, IPermissionManager, ISandboxManager,
 * IPluginValidator, IPluginDiagnostics, IPluginCertifier, IPluginProvider,
 * and IPluginRuntime.
 */

import {
  PluginManifest,
  PluginDescriptor,
  PluginState,
  PluginConfiguration,
  PluginHealth,
  PluginStatistics,
  PluginDiagnostics,
  PluginSnapshot,
  PluginActivation,
  PluginDeactivation,
  PluginLoadResult,
  PluginUnloadResult,
  PluginRegistration,
  PluginValidationResult,
  PluginCompatibilityResult,
  PluginResolutionResult,
  PluginCapability,
  PluginPermission,
  PluginSandbox,
  PluginService,
  PluginLifecycleRecord,
  PluginTelemetry,
  PluginCertification,
  CertificationReport,
  CertificationStatistics,
  CertificationHealth,
} from './models';

export interface IPluginRegistry {
  registerPlugin(manifest: PluginManifest, details?: Partial<PluginDescriptor>): PluginRegistration;
  removePlugin(pluginId: string): PluginUnloadResult;
  updatePluginState(pluginId: string, updates: Partial<PluginState>): PluginState;
  findPlugin(pluginId: string): PluginDescriptor | undefined;
  containsPlugin(pluginId: string): boolean;
  listPlugins(): ReadonlyArray<PluginDescriptor>;
  listStates(): ReadonlyArray<PluginState>;
  findPluginsByCategory(category: string): ReadonlyArray<PluginDescriptor>;
  findPluginsByTag(tag: string): ReadonlyArray<PluginDescriptor>;
  search(query: string): ReadonlyArray<PluginDescriptor>;
  statistics(): Record<string, number>;
  health(): PluginHealth;
  clear(): void;
}

export interface IPluginManifestLoader {
  parse(rawJson: string): PluginManifest;
  validate(manifest: PluginManifest): PluginValidationResult;
  verifyCompatibility(manifest: PluginManifest, engineVersion: string): PluginCompatibilityResult;
}

export interface IPluginLoader {
  load(plugin: PluginDescriptor, context: unknown): Promise<PluginLoadResult>;
  unload(pluginId: string): Promise<PluginUnloadResult>;
  reload(plugin: PluginDescriptor, context: unknown): Promise<PluginLoadResult>;
  isLoaded(pluginId: string): boolean;
  statistics(): Record<string, number>;
}

export interface IPluginLifecycleManager {
  initializePlugin(pluginId: string, context: unknown): Promise<PluginState>;
  activatePlugin(pluginId: string): Promise<PluginActivation>;
  deactivatePlugin(pluginId: string): Promise<PluginDeactivation>;
  disposePlugin(pluginId: string): Promise<PluginState>;
  getHistory(pluginId?: string): ReadonlyArray<PluginLifecycleRecord>;
  recordState(pluginId: string, state: PluginState, desc?: string): void;
}

export interface IDependencyResolver {
  resolveDependencies(plugins: ReadonlyArray<PluginDescriptor>): PluginResolutionResult;
  checkCircular(pluginId: string, pluginsMap: Map<string, PluginDescriptor>, visited: Set<string>, stack: Set<string>): boolean;
  topologicalSort(pluginId: string, pluginsMap: Map<string, PluginDescriptor>, visited: Set<string>, result: string[]): void;
}

export interface ICapabilityManager {
  registerCapability(pluginId: string, capability: PluginCapability): void;
  removeCapability(pluginId: string, capabilityName: string): boolean;
  listCapabilities(pluginId?: string): ReadonlyArray<PluginCapability>;
  resolveCapability(name: string): PluginCapability | undefined;
  clear(): void;
}

export interface IServiceRegistry {
  registerService(pluginId: string, service: PluginService, instanceFactory: () => unknown): void;
  resolveService<T = unknown>(interfaceName: string): T | undefined;
  replaceService(pluginId: string, service: PluginService, instanceFactory: () => unknown): void;
  clear(): void;
}

export interface IExtensionAPI {
  getConfiguration(pluginId: string): PluginConfiguration;
  dispatchEvent(eventName: string, payload: unknown): void;
  executeCommand(commandId: string, args: unknown): Promise<unknown>;
  log(pluginId: string, level: string, message: string): void;
  registerCapability(pluginId: string, capability: PluginCapability): void;
  resolveService<T = unknown>(interfaceName: string): T | undefined;
}

export interface IPermissionManager {
  grantPermission(pluginId: string, permission: PluginPermission): void;
  revokePermission(pluginId: string, scope: string): boolean;
  evaluatePermission(pluginId: string, scope: string): boolean;
  listPermissions(pluginId: string): ReadonlyArray<PluginPermission>;
  clear(): void;
}

export interface ISandboxManager {
  applySandbox(pluginId: string, sandbox: PluginSandbox): void;
  getSandbox(pluginId: string): PluginSandbox | undefined;
  validateAction(pluginId: string, actionType: string): boolean;
  clear(): void;
}

export interface IPluginValidator {
  validateManifest(manifest: PluginManifest): PluginValidationResult;
  validateCapabilities(pluginId: string, capabilities: ReadonlyArray<PluginCapability>): PluginValidationResult;
  validatePermissions(pluginId: string, permissions: ReadonlyArray<PluginPermission>): PluginValidationResult;
}

export interface IPluginDiagnostics {
  getDiagnostics(pluginId: string): PluginDiagnostics;
  getSnapshot(pluginId: string): PluginSnapshot;
  aggregateDiagnostics(): ReadonlyArray<PluginDiagnostics>;
  telemetry(pluginId: string): PluginTelemetry;
  recordTelemetry(pluginId: string, executionDurationMs: number, success: boolean, log?: string): void;
}

export interface IPluginCertifier {
  certifyPlugin(pluginId: string): Promise<CertificationReport>;
  statistics(): CertificationStatistics;
  health(): CertificationHealth;
  clear(): void;
}

export interface IPluginProvider {
  initialize(): void;
  shutdown(): void;
  registry(): IPluginRegistry;
  manifestLoader(): IPluginManifestLoader;
  loader(): IPluginLoader;
  lifecycleManager(): IPluginLifecycleManager;
  dependencyResolver(): IDependencyResolver;
  capabilityManager(): ICapabilityManager;
  serviceRegistry(): IServiceRegistry;
  permissionManager(): IPermissionManager;
  sandboxManager(): ISandboxManager;
  validator(): IPluginValidator;
  diagnostics(): IPluginDiagnostics;
  certifier(): IPluginCertifier;
}

export interface IPluginRuntime {
  initialize(): void;
  shutdown(): void;
  getRegistry(): IPluginRegistry;
  getLoader(): IPluginLoader;
  getLifecycleManager(): IPluginLifecycleManager;
  getDependencyResolver(): IDependencyResolver;
  getCapabilityManager(): ICapabilityManager;
  getServiceRegistry(): IServiceRegistry;
  getPermissionManager(): IPermissionManager;
  getSandboxManager(): ISandboxManager;
  getValidator(): IPluginValidator;
  getDiagnostics(): IPluginDiagnostics;
  getCertifier(): IPluginCertifier;
}
