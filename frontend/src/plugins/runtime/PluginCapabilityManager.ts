import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginCapabilityManager } from '../interfaces/plugin-capability';
import {
  type PluginCapability,
  type PluginCapabilityRegistration,
  type PluginCapabilityResult,
  type PluginCapabilityTypeValue,
  type CapabilityStatistics,
  type CapabilityHealth,
  type CapabilityDiagnostics,
  createCapabilityResult
} from '../models/capability';
import { PluginState } from '../models/plugin-state';
import {
  PluginCapabilityError,
  PluginCapabilityRegistrationError,
  PluginCapabilityConflictError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginCapabilityManager implements IPluginCapabilityManager {
  private readonly registry = new Map<string, PluginCapability>();
  
  private registeredCount = 0;
  private removedCount = 0;
  private failRegistrations = 0;
  private dupAttempts = 0;
  private conflictAttempts = 0;
  private lookups = 0;
  
  private lastMetadata?: {
    readonly pluginId: string;
    readonly id: string;
    readonly type: 'capability' | 'extension' | 'extensionPoint';
    readonly timestamp: number;
  };

  constructor(private readonly lifecycleManager: IPluginLifecycleManager) {
    // Integrate with lifecycle transitions
    this.lifecycleManager.addDeactivateListener((pluginId) => this.unregisterPluginCapabilities(pluginId));
    this.lifecycleManager.addDisposeListener((pluginId) => this.unregisterPluginCapabilities(pluginId));
  }

  private getCanonicalId(pluginId: string, id: string): string {
    return `${pluginId}:${id}`;
  }

  private isActivePlugin(pluginId: string): boolean {
    const state = this.lifecycleManager.getLifecycleState(pluginId);
    return state === PluginState.ACTIVE || state === PluginState.READY;
  }

  public registerCapability(pluginId: string, registration: PluginCapabilityRegistration): PluginCapabilityResult {
    const id = registration.id;
    if (!pluginId || !id) {
      this.failRegistrations += 1;
      throw new PluginCapabilityRegistrationError(`pluginId and capability registration id are required.`, pluginId);
    }

    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state !== PluginState.ACTIVE && state !== PluginState.READY) {
      this.failRegistrations += 1;
      throw new PluginCapabilityRegistrationError(
        `Cannot register capability for plugin '${pluginId}' because its state is not ACTIVE/READY (status: ${state}).`,
        pluginId
      );
    }

    const canonicalId = this.getCanonicalId(pluginId, id);
    if (this.registry.has(canonicalId)) {
      this.dupAttempts += 1;
      throw new PluginCapabilityConflictError(`Capability '${id}' is already registered for plugin '${pluginId}'.`, pluginId);
    }

    const capability: PluginCapability = {
      id,
      pluginId,
      name: registration.name,
      type: registration.type,
      version: registration.version,
      description: registration.description,
      metadata: registration.metadata || {},
      enabled: true,
      registeredAt: Date.now()
    };

    this.registry.set(canonicalId, capability);
    this.registeredCount += 1;
    this.lastMetadata = {
      pluginId,
      id,
      type: 'capability',
      timestamp: Date.now()
    };

    return createCapabilityResult({
      success: true,
      capabilityId: id,
      pluginId,
      currentState: 'registered',
      warnings: [],
      errors: [],
      timestamp: Date.now()
    });
  }

  public unregisterCapability(pluginId: string, capabilityId: string): PluginCapabilityResult {
    const canonicalId = this.getCanonicalId(pluginId, capabilityId);
    const existing = this.registry.get(canonicalId);
    if (!existing) {
      throw new PluginCapabilityError(`Capability '${capabilityId}' not found for plugin '${pluginId}'.`, pluginId);
    }

    this.registry.delete(canonicalId);
    this.removedCount += 1;

    return createCapabilityResult({
      success: true,
      capabilityId,
      pluginId,
      currentState: 'unregistered',
      warnings: [],
      errors: [],
      timestamp: Date.now()
    });
  }

  public unregisterPluginCapabilities(pluginId: string): void {
    for (const [key, cap] of this.registry.entries()) {
      if (cap.pluginId === pluginId) {
        this.registry.delete(key);
        this.removedCount += 1;
      }
    }
  }

  public findCapability(capabilityId: string): PluginCapability | null {
    this.lookups += 1;
    for (const cap of this.registry.values()) {
      // Find matching capability by ID if owned by active plugin
      if (cap.id === capabilityId && cap.enabled && this.isActivePlugin(cap.pluginId)) {
        return freezeDeepSafe(cap);
      }
    }
    return null;
  }

  public findCapabilitiesByPlugin(pluginId: string): ReadonlyArray<PluginCapability> {
    this.lookups += 1;
    const results: PluginCapability[] = [];
    for (const cap of this.registry.values()) {
      if (cap.pluginId === pluginId && cap.enabled && this.isActivePlugin(pluginId)) {
        results.push(cap);
      }
    }
    return Object.freeze(results.map(c => freezeDeepSafe(c)));
  }

  public findCapabilitiesByType(type: PluginCapabilityTypeValue): ReadonlyArray<PluginCapability> {
    this.lookups += 1;
    const results: PluginCapability[] = [];
    for (const cap of this.registry.values()) {
      if (cap.type === type && cap.enabled && this.isActivePlugin(cap.pluginId)) {
        results.push(cap);
      }
    }
    return Object.freeze(results.map(c => freezeDeepSafe(c)));
  }

  public containsCapability(capabilityId: string): boolean {
    return this.findCapability(capabilityId) !== null;
  }

  public listCapabilities(): ReadonlyArray<PluginCapability> {
    const results: PluginCapability[] = [];
    for (const cap of this.registry.values()) {
      if (cap.enabled && this.isActivePlugin(cap.pluginId)) {
        results.push(cap);
      }
    }
    return Object.freeze(results.map(c => freezeDeepSafe(c)));
  }

  public enableCapability(capabilityId: string): void {
    for (const [key, cap] of this.registry.entries()) {
      if (cap.id === capabilityId) {
        this.registry.set(key, { ...cap, enabled: true });
      }
    }
  }

  public disableCapability(capabilityId: string): void {
    for (const [key, cap] of this.registry.entries()) {
      if (cap.id === capabilityId) {
        this.registry.set(key, { ...cap, enabled: false });
      }
    }
  }

  public statistics(): CapabilityStatistics {
    const activeCount = Array.from(this.registry.values())
      .filter(c => c.enabled && this.isActivePlugin(c.pluginId)).length;

    return Object.freeze({
      registeredCapabilities: this.registeredCount,
      removedCapabilities: this.removedCount,
      activeCapabilities: activeCount,
      failedRegistrations: this.failRegistrations,
      duplicateAttempts: this.dupAttempts,
      conflictAttempts: this.conflictAttempts,
      capabilityLookups: this.lookups
    });
  }

  public health(): CapabilityHealth {
    const pluginCount = new Set(Array.from(this.registry.values()).map(c => c.pluginId)).size;
    const totalOps = this.registeredCount + this.failRegistrations;
    const failureRate = totalOps > 0 ? this.failRegistrations / totalOps : 0;
    const healthy = failureRate === 0;

    return Object.freeze({
      healthy,
      capabilityCount: this.registry.size,
      pluginCount,
      failureRate,
      duplicateCount: this.dupAttempts,
      conflictCount: this.conflictAttempts,
      message: healthy ? 'Capability registry healthy' : `Capability failure rate is ${(failureRate * 100).toFixed(1)}%`
    });
  }

  public diagnostics(): CapabilityDiagnostics {
    const pluginCount = new Set(Array.from(this.registry.values()).map(c => c.pluginId)).size;
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health(),
      capabilityCount: this.registry.size,
      extensionCount: 0,
      extensionPointCount: 0,
      registeredPluginCount: pluginCount,
      lastRegistrationMetadata: this.lastMetadata
    });
  }

  public reset(): void {
    this.registry.clear();
    this.registeredCount = 0;
    this.removedCount = 0;
    this.failRegistrations = 0;
    this.dupAttempts = 0;
    this.conflictAttempts = 0;
    this.lookups = 0;
    this.lastMetadata = undefined;
  }
}
