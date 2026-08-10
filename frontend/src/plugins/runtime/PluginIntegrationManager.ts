import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';
import type { IPluginLoader } from '../interfaces/plugin-loader';
import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginCapabilityManager, IPluginExtensionManager } from '../interfaces/plugin-capability';
import type { IPluginSecurityManager, IPluginSandboxManager } from '../interfaces/plugin-security';
import type { IPluginConfigurationManager } from '../interfaces/plugin-configuration';
import type { IPluginIntegrationManager } from '../interfaces/plugin-integration';
import {
  type PluginIntegrationResult,
  type PluginIntegrationRecord,
  type PluginIntegrationStatistics,
  type PluginIntegrationHealth,
  type PluginIntegrationDiagnostics,
  type PluginIntegrationOptions,
  PluginIntegrationPhase,
  type PluginIntegrationPhaseValue,
  createPluginIntegrationResult,
  createPluginIntegrationRecord,
  createPluginIntegrationStatistics,
  createPluginIntegrationHealth,
  createPluginIntegrationDiagnostics
} from '../models/integration';
import { PluginState } from '../models/plugin-state';
import { freezeDeepSafe } from '../models/dependency';
import { PluginSandboxError } from '../errors/PluginErrors';
import { PluginManifestValidator } from './PluginManifestValidator';
import {
  PluginIntegrationValidationError,
  PluginIntegrationDependencyError,
  PluginIntegrationSecurityError,
  PluginIntegrationConfigurationError,
  PluginIntegrationLoadError
} from '../errors/PluginErrors';

export class PluginIntegrationManager implements IPluginIntegrationManager {
  private readonly integrationStatuses = new Map<string, PluginIntegrationResult>();
  private readonly inFlightIntegrations = new Map<string, Promise<PluginIntegrationResult>>();
  private readonly currentlyIntegratingSet = new Set<string>();
  private readonly historyRecords: PluginIntegrationRecord[] = [];
  private readonly durations: number[] = [];

  private totalAttemptsCount = 0;
  private successfulIntegrationsCount = 0;
  private failedIntegrationsCount = 0;
  private rolledBackIntegrationsCount = 0;
  private reloadCount = 0;
  private dependencyFailuresCount = 0;
  private securityRejectionsCount = 0;
  private configurationFailuresCount = 0;
  private loadingFailuresCount = 0;
  private lifecycleFailuresCount = 0;
  private capabilityFailuresCount = 0;
  private sandboxFailuresCount = 0;
  private startupDuration = 0;
  private shutdownDuration = 0;

  constructor(
    private readonly discoveryManager: IPluginDiscoveryManager,
    private readonly dependencyResolver: IPluginDependencyResolver,
    private readonly pluginLoader: IPluginLoader,
    private readonly lifecycleManager: IPluginLifecycleManager,
    private readonly capabilityManager: IPluginCapabilityManager,
    private readonly extensionManager: IPluginExtensionManager,
    private readonly securityManager: IPluginSecurityManager,
    private readonly sandboxManager: IPluginSandboxManager,
    private readonly configManager: IPluginConfigurationManager
  ) {}

  public async integrate(pluginId: string, _options?: PluginIntegrationOptions): Promise<PluginIntegrationResult> {
    const startTime = Date.now();

    const inFlight = this.inFlightIntegrations.get(pluginId);
    if (inFlight) {
      return inFlight;
    }

    const promise = (async () => {
      this.totalAttemptsCount += 1;
      this.currentlyIntegratingSet.add(pluginId);

      const integrationId = Math.random().toString(36).substring(2, 11);
      const errors: Array<{ message: string; stack?: string }> = [];
      const warnings: string[] = [];
      const skipped: string[] = [];
      const rollbacks: string[] = [];

      let phase: PluginIntegrationPhaseValue = PluginIntegrationPhase.DISCOVERY;

      try {
        // STEP 1 — Discovery
        phase = PluginIntegrationPhase.DISCOVERY;
        const manifest = this.discoveryManager.find(pluginId);
        if (!manifest) {
          throw new PluginIntegrationValidationError(`Plugin '${pluginId}' not found in discovery registry.`);
        }

        // STEP 2 — Manifest Validation
        phase = PluginIntegrationPhase.VALIDATION;
        const validation = PluginManifestValidator.validate(manifest);
        if (!validation.valid) {
          const errMsg = validation.issues.map(i => i.message).join('; ');
          throw new PluginIntegrationValidationError(`Manifest validation failed: ${errMsg}`);
        }

        // STEP 3 — Dependency Resolution
        phase = PluginIntegrationPhase.DEPENDENCY_RESOLUTION;
        const resolution = this.dependencyResolver.resolvePlugin(pluginId);
        if (resolution.plan === null || resolution.plan === undefined || resolution.status === 'FAILED') {
          const errMsg = resolution.issues.map(i => i.message).join('; ');
          this.dependencyFailuresCount += 1;
          throw new PluginIntegrationDependencyError(`Dependency resolution failed: ${errMsg}`);
        }

        // STEP 4 — Security Preflight
        phase = PluginIntegrationPhase.SECURITY_PREFLIGHT;
        const securityProfile = this.securityManager.getSecurityProfile(pluginId);
        if (!securityProfile) {
          throw new PluginIntegrationSecurityError(`Security profile not registered for plugin '${pluginId}'.`);
        }
        if (!securityProfile.enabled) {
          this.securityRejectionsCount += 1;
          throw new PluginIntegrationSecurityError(`Security profile is disabled for plugin '${pluginId}'.`);
        }

        // STEP 5 — Configuration Initialization
        phase = PluginIntegrationPhase.CONFIGURATION_INITIALIZATION;
        const schema = this.configManager.getSchema(pluginId);
        if (schema) {
          let config = this.configManager.getConfiguration(pluginId);
          if (!config) {
            try {
              config = this.configManager.createConfiguration(pluginId, {});
            } catch (err: any) {
              this.configurationFailuresCount += 1;
              throw new PluginIntegrationConfigurationError(`Configuration creation failed: ${err.message}`);
            }
          }
          const configVal = this.configManager.validateConfiguration(pluginId, config.values);
          if (!configVal.valid) {
            const errMsg = configVal.issues.map(i => i.message).join('; ');
            this.configurationFailuresCount += 1;
            throw new PluginIntegrationConfigurationError(`Configuration validation failed: ${errMsg}`);
          }
        }

        // STEP 6 — Loading
        phase = PluginIntegrationPhase.LOADING;
        if (!this.pluginLoader.isLoaded(pluginId)) {
          const loadRes = await this.pluginLoader.load(pluginId);
          if (!loadRes.success) {
            this.loadingFailuresCount += 1;
            throw new PluginIntegrationLoadError(loadRes.error?.message || 'Load failed.');
          }
        }

        // STEP 7 — Sandbox Initialization
        phase = PluginIntegrationPhase.SANDBOX_INITIALIZATION;
        let sandbox = this.sandboxManager.getSandbox(pluginId);
        if (!sandbox) {
          try {
            sandbox = this.sandboxManager.createSandbox(pluginId);
          } catch (err: any) {
            this.sandboxFailuresCount += 1;
            throw new PluginSandboxError(err.message);
          }
        }

        // STEP 8 — Lifecycle Initialization
        phase = PluginIntegrationPhase.LIFECYCLE_INITIALIZATION;
        const currentLifeState = this.lifecycleManager.getLifecycleState(pluginId);
        if (currentLifeState === PluginState.LOADED || currentLifeState === PluginState.REGISTERED) {
          try {
            await this.lifecycleManager.initializePlugin(pluginId);
          } catch (err: any) {
            this.lifecycleFailuresCount += 1;
            throw err;
          }
        }

        // STEP 10 — Activation (Lifecycle activate before registering capabilities)
        phase = PluginIntegrationPhase.ACTIVATION;
        const lifeState = this.lifecycleManager.getLifecycleState(pluginId);
        if (lifeState === PluginState.DEACTIVATED || lifeState === PluginState.INITIALIZING) {
          try {
            await this.lifecycleManager.activatePlugin(pluginId);
          } catch (err: any) {
            this.lifecycleFailuresCount += 1;
            throw err;
          }
        }

        // STEP 9 — Capability & Extension Registration
        phase = PluginIntegrationPhase.CAPABILITY_REGISTRATION;
        const capRegistered: string[] = [];
        const extRegistered: string[] = [];
        for (const capDecl of manifest.capabilities) {
          try {
            this.capabilityManager.registerCapability(pluginId, {
              id: capDecl.type,
              name: capDecl.type,
              type: capDecl.type as any,
              version: manifest.version,
              description: String(capDecl.properties.description || ''),
              metadata: capDecl.properties
            });
            capRegistered.push(capDecl.type);
          } catch (err: any) {
            this.capabilityFailuresCount += 1;
            throw new PluginIntegrationValidationError(`Failed to register capability '${capDecl.type}': ${err.message}`);
          }
        }

        // STEP 11 — READY
        phase = PluginIntegrationPhase.READY;
        this.successfulIntegrationsCount += 1;

        const duration = Date.now() - startTime;
        this.durations.push(duration);

        const res = createPluginIntegrationResult({
          pluginId,
          success: true,
          phase: PluginIntegrationPhase.READY,
          currentState: this.lifecycleManager.getLifecycleState(pluginId),
          timestamp: Date.now(),
          duration,
          errors: [],
          warnings: [],
          skipped: [],
          sandboxStatus: this.sandboxManager.getSandbox(pluginId)?.state,
          configurationStatus: this.configManager.getConfiguration(pluginId) ? 'valid' : undefined,
          capabilitiesRegistered: capRegistered,
          extensionsRegistered: extRegistered
        });

        this.recordHistory(integrationId, pluginId, true, startTime, Date.now(), PluginIntegrationPhase.READY, [], []);
        this.integrationStatuses.set(pluginId, res);
        return res;

      } catch (err: any) {
        this.failedIntegrationsCount += 1;
        errors.push({ message: err.message, stack: err.stack });

        // ROLLBACK previously completed steps
        this.rolledBackIntegrationsCount += 1;

        try {
          this.capabilityManager.unregisterPluginCapabilities(pluginId);
          rollbacks.push('UNREGISTER_CAPABILITIES');
        } catch (rollErr: any) {
          warnings.push(`Rollback UNREGISTER_CAPABILITIES failed: ${rollErr.message}`);
        }

        try {
          this.extensionManager.unregisterPluginExtensions(pluginId);
          rollbacks.push('UNREGISTER_EXTENSIONS');
        } catch (rollErr: any) {
          warnings.push(`Rollback UNREGISTER_EXTENSIONS failed: ${rollErr.message}`);
        }

        const stateBeforeRollback = this.lifecycleManager.getLifecycleState(pluginId);
        if (stateBeforeRollback === PluginState.ACTIVE || stateBeforeRollback === PluginState.READY) {
          try {
            await this.lifecycleManager.deactivatePlugin(pluginId);
            rollbacks.push('DEACTIVATE');
          } catch (rollErr: any) {
            warnings.push(`Rollback DEACTIVATE failed: ${rollErr.message}`);
          }
        }

        const stateAfterDeactivate = this.lifecycleManager.getLifecycleState(pluginId);
        if (stateAfterDeactivate !== PluginState.UNLOADED && stateAfterDeactivate !== PluginState.DISPOSED) {
          try {
            await this.lifecycleManager.disposePlugin(pluginId);
            rollbacks.push('DISPOSE');
          } catch (rollErr: any) {
            warnings.push(`Rollback DISPOSE failed: ${rollErr.message}`);
          }
        }

        try {
          this.sandboxManager.destroySandbox(pluginId);
          rollbacks.push('DESTROY_SANDBOX');
        } catch (rollErr: any) {
          warnings.push(`Rollback DESTROY_SANDBOX failed: ${rollErr.message}`);
        }

        if (this.pluginLoader.isLoaded(pluginId)) {
          try {
            this.pluginLoader.unload(pluginId);
            rollbacks.push('UNLOAD');
          } catch (rollErr: any) {
            warnings.push(`Rollback UNLOAD failed: ${rollErr.message}`);
          }
        }

        if ((this.lifecycleManager as any).pluginStates) {
          (this.lifecycleManager as any).pluginStates.delete(pluginId);
        }

        const duration = Date.now() - startTime;
        this.durations.push(duration);

        const res = createPluginIntegrationResult({
          pluginId,
          success: false,
          phase,
          currentState: this.lifecycleManager.getLifecycleState(pluginId),
          timestamp: Date.now(),
          duration,
          errors,
          warnings,
          skipped,
          sandboxStatus: undefined,
          configurationStatus: undefined,
          capabilitiesRegistered: [],
          extensionsRegistered: []
        });

        this.recordHistory(integrationId, pluginId, false, startTime, Date.now(), phase, errors, rollbacks);
        this.integrationStatuses.set(pluginId, res);
        return res;

      } finally {
        this.currentlyIntegratingSet.delete(pluginId);
        this.inFlightIntegrations.delete(pluginId);
      }
    })();

    this.inFlightIntegrations.set(pluginId, promise);
    return promise;
  }

  public async integrateMany(
    pluginIds: ReadonlyArray<string>,
    options?: PluginIntegrationOptions
  ): Promise<ReadonlyArray<PluginIntegrationResult>> {
    const resolution = this.dependencyResolver.resolveAll();
    const order = resolution.plan ? resolution.plan.order : [];

    const sortedTargetIds = order.filter(id => pluginIds.includes(id));

    const results: PluginIntegrationResult[] = [];
    const failedIds = new Set<string>();

    for (const pluginId of sortedTargetIds) {
      const manifest = this.discoveryManager.find(pluginId);
      let depFailed = false;
      if (manifest) {
        for (const dep of manifest.dependencies) {
          if (!dep.optional && failedIds.has(dep.id)) {
            depFailed = true;
            break;
          }
        }
      }

      if (depFailed) {
        const duration = 0;
        const res = createPluginIntegrationResult({
          pluginId,
          success: false,
          phase: PluginIntegrationPhase.DEPENDENCY_RESOLUTION,
          currentState: PluginState.FAILED,
          timestamp: Date.now(),
          duration,
          errors: [{ message: `Required dependency failed to integrate.` }],
          warnings: [],
          skipped: [],
          capabilitiesRegistered: [],
          extensionsRegistered: []
        });
        results.push(res);
        failedIds.add(pluginId);
        this.integrationStatuses.set(pluginId, res);
      } else {
        const res = await this.integrate(pluginId, options);
        results.push(res);
        if (!res.success) {
          failedIds.add(pluginId);
        }
      }
    }

    return Object.freeze(results);
  }

  public async activate(pluginId: string): Promise<PluginIntegrationResult> {
    const startTime = Date.now();
    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state !== PluginState.ACTIVE && state !== PluginState.READY) {
      await this.lifecycleManager.activatePlugin(pluginId);
    }

    const duration = Date.now() - startTime;
    return createPluginIntegrationResult({
      pluginId,
      success: true,
      phase: PluginIntegrationPhase.ACTIVATION,
      currentState: this.lifecycleManager.getLifecycleState(pluginId),
      timestamp: Date.now(),
      duration,
      errors: [],
      warnings: [],
      skipped: [],
      capabilitiesRegistered: [],
      extensionsRegistered: []
    });
  }

  public async deactivate(pluginId: string): Promise<PluginIntegrationResult> {
    const startTime = Date.now();
    this.capabilityManager.unregisterPluginCapabilities(pluginId);
    this.extensionManager.unregisterPluginExtensions(pluginId);

    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state === PluginState.ACTIVE || state === PluginState.READY) {
      await this.lifecycleManager.deactivatePlugin(pluginId);
    }

    const duration = Date.now() - startTime;
    return createPluginIntegrationResult({
      pluginId,
      success: true,
      phase: PluginIntegrationPhase.DEACTIVATION,
      currentState: this.lifecycleManager.getLifecycleState(pluginId),
      timestamp: Date.now(),
      duration,
      errors: [],
      warnings: [],
      skipped: [],
      capabilitiesRegistered: [],
      extensionsRegistered: []
    });
  }

  public async unload(pluginId: string): Promise<PluginIntegrationResult> {
    const startTime = Date.now();

    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state !== PluginState.UNLOADED && state !== PluginState.DISPOSED) {
      await this.lifecycleManager.disposePlugin(pluginId);
    }

    this.sandboxManager.destroySandbox(pluginId);

    if (this.pluginLoader.isLoaded(pluginId)) {
      this.pluginLoader.unload(pluginId);
    }

    if ((this.lifecycleManager as any).pluginStates) {
      (this.lifecycleManager as any).pluginStates.delete(pluginId);
    }

    const duration = Date.now() - startTime;
    return createPluginIntegrationResult({
      pluginId,
      success: true,
      phase: PluginIntegrationPhase.UNLOADING,
      currentState: this.lifecycleManager.getLifecycleState(pluginId),
      timestamp: Date.now(),
      duration,
      errors: [],
      warnings: [],
      skipped: [],
      capabilitiesRegistered: [],
      extensionsRegistered: []
    });
  }

  public async reload(pluginId: string, options?: PluginIntegrationOptions): Promise<PluginIntegrationResult> {
    this.reloadCount += 1;

    const profile = this.securityManager.getSecurityProfile(pluginId);
    const permissions = this.securityManager.listPermissions(pluginId);

    await this.deactivate(pluginId);
    await this.unload(pluginId);

    if (profile) {
      this.securityManager.createSecurityProfile(pluginId, {
        enabled: profile.enabled,
        permissions: [],
        policies: profile.policies || [],
        resourceLimits: profile.resourceLimits || {},
        allowedCapabilities: profile.allowedCapabilities || [],
        deniedCapabilities: profile.deniedCapabilities || []
      });
    }
    for (const perm of permissions) {
      this.securityManager.registerPermission(pluginId, perm.action, perm.scope, perm.description);
    }

    return this.integrate(pluginId, options);
  }

  public async startup(options?: PluginIntegrationOptions): Promise<ReadonlyArray<PluginIntegrationResult>> {
    const startTime = Date.now();
    await this.discoveryManager.discover();
    const manifests = this.discoveryManager.findAll();
    const ids = manifests.map(m => m.id);
    const results = await this.integrateMany(ids, options);
    this.startupDuration = Date.now() - startTime;
    return results;
  }

  public async shutdown(): Promise<ReadonlyArray<PluginIntegrationResult>> {
    const startTime = Date.now();
    const resolution = this.dependencyResolver.resolveAll();
    const order = resolution.plan ? resolution.plan.order : [];

    const reverseOrder = [...order].reverse();
    const results: PluginIntegrationResult[] = [];

    for (const pluginId of reverseOrder) {
      const state = this.lifecycleManager.getLifecycleState(pluginId);
      if (state !== PluginState.UNLOADED && state !== PluginState.DISPOSED) {
        await this.deactivate(pluginId);
        const unloadRes = await this.unload(pluginId);
        results.push(unloadRes);
      }
    }

    this.shutdownDuration = Date.now() - startTime;
    return Object.freeze(results);
  }

  public getIntegrationStatus(pluginId: string): PluginIntegrationResult | null {
    const res = this.integrationStatuses.get(pluginId);
    return res ? freezeDeepSafe(res) : null;
  }

  public integrationHistory(): ReadonlyArray<PluginIntegrationRecord> {
    return Object.freeze([...this.historyRecords]);
  }

  public statistics(): PluginIntegrationStatistics {
    const avg = this.durations.length > 0
      ? this.durations.reduce((a, b) => a + b, 0) / this.durations.length
      : 0;
    const max = this.durations.length > 0 ? Math.max(...this.durations) : 0;
    const min = this.durations.length > 0 ? Math.min(...this.durations) : 0;

    const list = Array.from(this.integrationStatuses.values());
    const readyCount = list.filter(r => r.currentState === PluginState.ACTIVE || r.currentState === PluginState.READY).length;
    const failedCount = list.filter(r => r.currentState === PluginState.FAILED || r.phase === PluginIntegrationPhase.FAILED).length;

    return createPluginIntegrationStatistics({
      totalAttempts: this.totalAttemptsCount,
      successfulIntegrations: this.successfulIntegrationsCount,
      failedIntegrations: this.failedIntegrationsCount,
      rolledBackIntegrations: this.rolledBackIntegrationsCount,
      currentlyIntegrating: this.currentlyIntegratingSet.size,
      readyPlugins: readyCount,
      failedPlugins: failedCount,
      averageDuration: avg,
      maxDuration: max,
      minDuration: min,
      startupDuration: this.startupDuration,
      shutdownDuration: this.shutdownDuration,
      reloadCount: this.reloadCount,
      dependencyFailures: this.dependencyFailuresCount,
      securityRejections: this.securityRejectionsCount,
      configurationFailures: this.configurationFailuresCount,
      loadingFailures: this.loadingFailuresCount,
      lifecycleFailures: this.lifecycleFailuresCount,
      capabilityFailures: this.capabilityFailuresCount,
      sandboxFailures: this.sandboxFailuresCount
    });
  }

  public health(): PluginIntegrationHealth {
    const stats = this.statistics();
    const total = stats.successfulIntegrations + stats.failedIntegrations;
    const failureRate = total > 0 ? stats.failedIntegrations / total : 0;
    const healthy = stats.failedIntegrations === 0 && stats.dependencyFailures === 0;

    return createPluginIntegrationHealth({
      healthy,
      readyPluginCount: stats.readyPlugins,
      failedIntegrationCount: stats.failedIntegrations,
      securityRejectionCount: stats.securityRejections,
      dependencyFailureCount: stats.dependencyFailures,
      activeIntegrationCount: stats.currentlyIntegrating,
      rollbackCount: stats.rolledBackIntegrations,
      failureRate,
      message: healthy ? 'Integration engine healthy' : `Integration engine has ${stats.failedIntegrations} failed integrations.`
    });
  }

  public diagnostics(): PluginIntegrationDiagnostics {
    return createPluginIntegrationDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      activeIntegrations: Array.from(this.currentlyIntegratingSet),
      historyDepth: this.historyRecords.length,
      lastIntegrationRecord: this.historyRecords[this.historyRecords.length - 1]
    });
  }

  public reset(): void {
    this.integrationStatuses.clear();
    this.inFlightIntegrations.clear();
    this.currentlyIntegratingSet.clear();
    this.historyRecords.length = 0;
    this.durations.length = 0;
    this.totalAttemptsCount = 0;
    this.successfulIntegrationsCount = 0;
    this.failedIntegrationsCount = 0;
    this.rolledBackIntegrationsCount = 0;
    this.reloadCount = 0;
    this.dependencyFailuresCount = 0;
    this.securityRejectionsCount = 0;
    this.configurationFailuresCount = 0;
    this.loadingFailuresCount = 0;
    this.lifecycleFailuresCount = 0;
    this.capabilityFailuresCount = 0;
    this.sandboxFailuresCount = 0;
    this.startupDuration = 0;
    this.shutdownDuration = 0;
  }

  private recordHistory(
    integrationId: string,
    pluginId: string,
    success: boolean,
    startedAt: number,
    completedAt: number,
    finalPhase: typeof PluginIntegrationPhase[keyof typeof PluginIntegrationPhase],
    errors: Array<{ message: string; stack?: string }>,
    rollbacks: string[]
  ): void {
    const record = createPluginIntegrationRecord({
      integrationId,
      pluginId,
      success,
      startedAt,
      completedAt,
      duration: completedAt - startedAt,
      finalPhase,
      errors,
      rollbacks
    });
    this.historyRecords.push(record);
  }
}
