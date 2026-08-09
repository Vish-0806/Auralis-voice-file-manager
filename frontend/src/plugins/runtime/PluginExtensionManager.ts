import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginCapabilityManager } from '../interfaces/plugin-capability';
import type { IPluginExtensionManager } from '../interfaces/plugin-capability';
import {
  type ExtensionPoint,
  type ExtensionRegistration,
  type ExtensionResult,
  type ExtensionStatistics,
  type ExtensionHealth,
  createExtensionResult
} from '../models/capability';
import { PluginState } from '../models/plugin-state';
import {
  PluginExtensionError,
  PluginExtensionRegistrationError,
  PluginExtensionConflictError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginExtensionManager implements IPluginExtensionManager {
  private readonly extensionPoints = new Map<string, ExtensionPoint>();
  private readonly extensionPointOwners = new Map<string, string>(); // pointId -> pluginId
  private readonly extensions = new Map<string, ExtensionRegistration>();
  
  private registeredPointsCount = 0;
  private removedPointsCount = 0;
  private registeredExtsCount = 0;
  private removedExtsCount = 0;
  private failRegistrations = 0;
  private dupAttempts = 0;
  private conflictAttempts = 0;
  private lookups = 0;

  constructor(
    private readonly lifecycleManager: IPluginLifecycleManager,
    private readonly capabilityManager: IPluginCapabilityManager
  ) {
    this.lifecycleManager.addDeactivateListener((pluginId) => this.unregisterPluginExtensions(pluginId));
    this.lifecycleManager.addDisposeListener((pluginId) => {
      this.unregisterPluginExtensions(pluginId);
      // Clean up extension points owned by this plugin
      for (const [pointId, owner] of this.extensionPointOwners.entries()) {
        if (owner === pluginId) {
          this.extensionPoints.delete(pointId);
          this.extensionPointOwners.delete(pointId);
          this.removedPointsCount += 1;
        }
      }
    });
  }

  private isActivePlugin(pluginId: string): boolean {
    const state = this.lifecycleManager.getLifecycleState(pluginId);
    return state === PluginState.ACTIVE || state === PluginState.READY;
  }

  public registerExtensionPoint(pluginId: string, point: Omit<ExtensionPoint, 'enabled'>): void {
    if (!pluginId || !point.id) {
      throw new PluginExtensionRegistrationError(`pluginId and extension point id are required.`, pluginId);
    }

    if (this.extensionPoints.has(point.id)) {
      throw new PluginExtensionConflictError(`Extension point '${point.id}' is already registered.`, pluginId);
    }

    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state !== PluginState.ACTIVE && state !== PluginState.READY) {
      throw new PluginExtensionRegistrationError(
        `Cannot register extension point for plugin '${pluginId}' because its state is not ACTIVE/READY (status: ${state}).`,
        pluginId
      );
    }

    const cardinality = point.cardinality;
    if (cardinality !== 'SINGLE' && cardinality !== 'MANY') {
      throw new PluginExtensionRegistrationError(`Invalid cardinality '${cardinality}'. Must be SINGLE or MANY.`, pluginId);
    }

    const extensionPoint: ExtensionPoint = {
      ...point,
      enabled: true
    };

    this.extensionPoints.set(point.id, extensionPoint);
    this.extensionPointOwners.set(point.id, pluginId);
    this.registeredPointsCount += 1;
  }

  public unregisterExtensionPoint(pluginId: string, pointId: string): void {
    const owner = this.extensionPointOwners.get(pointId);
    if (!owner || owner !== pluginId) {
      throw new PluginExtensionError(`Extension point '${pointId}' does not belong to plugin '${pluginId}'.`, pluginId);
    }

    this.extensionPoints.delete(pointId);
    this.extensionPointOwners.delete(pointId);
    this.removedPointsCount += 1;

    // Orphan extensions are cleaned up
    for (const [key, ext] of this.extensions.entries()) {
      if (ext.extensionPointId === pointId) {
        this.extensions.delete(key);
        this.removedExtsCount += 1;
      }
    }
  }

  public findExtensionPoint(pointId: string): ExtensionPoint | null {
    const pt = this.extensionPoints.get(pointId);
    if (pt && pt.enabled && this.isActivePlugin(this.extensionPointOwners.get(pointId) || '')) {
      return freezeDeepSafe(pt);
    }
    return null;
  }

  public listExtensionPoints(): ReadonlyArray<ExtensionPoint> {
    const results: ExtensionPoint[] = [];
    for (const pt of this.extensionPoints.values()) {
      const owner = this.extensionPointOwners.get(pt.id) || '';
      if (pt.enabled && this.isActivePlugin(owner)) {
        results.push(pt);
      }
    }
    return Object.freeze(results.map(p => freezeDeepSafe(p)));
  }

  public registerExtension(pluginId: string, extension: Omit<ExtensionRegistration, 'pluginId' | 'enabled' | 'registeredAt'>): ExtensionResult {
    const extId = extension.extensionId;
    const pointId = extension.extensionPointId;

    if (!pluginId || !extId || !pointId) {
      this.failRegistrations += 1;
      throw new PluginExtensionRegistrationError(`pluginId, extensionId, and extensionPointId are required.`, pluginId);
    }

    // Verify plugin active state
    const state = this.lifecycleManager.getLifecycleState(pluginId);
    if (state !== PluginState.ACTIVE && state !== PluginState.READY) {
      this.failRegistrations += 1;
      throw new PluginExtensionRegistrationError(
        `Cannot register extension for plugin '${pluginId}' because its state is not ACTIVE/READY (status: ${state}).`,
        pluginId
      );
    }

    // Verify extension point exists
    const extensionPoint = this.findExtensionPoint(pointId);
    if (!extensionPoint) {
      this.failRegistrations += 1;
      throw new PluginExtensionRegistrationError(`Extension point '${pointId}' not found or not active.`, pluginId);
    }

    // Verify extension ID uniqueness
    if (this.extensions.has(extId)) {
      this.dupAttempts += 1;
      throw new PluginExtensionConflictError(`Extension '${extId}' is already registered.`, pluginId);
    }

    // Verify capability reference if provided
    if (extension.capabilityId) {
      const cap = this.capabilityManager.findCapability(extension.capabilityId);
      if (!cap) {
        this.failRegistrations += 1;
        throw new PluginExtensionRegistrationError(`Referenced capability '${extension.capabilityId}' not found.`, pluginId);
      }

      // Verify capability ownership
      if (cap.pluginId !== pluginId) {
        this.conflictAttempts += 1;
        throw new PluginExtensionConflictError(
          `Capability '${extension.capabilityId}' does not belong to plugin '${pluginId}'.`,
          pluginId
        );
      }

      // Verify capability type compatibility
      if (!extensionPoint.acceptedTypes.includes(cap.type)) {
        this.conflictAttempts += 1;
        throw new PluginExtensionConflictError(
          `Capability type '${cap.type}' is not accepted by extension point '${pointId}'.`,
          pluginId
        );
      }
    }

    // Cardinality constraint
    if (extensionPoint.cardinality === 'SINGLE') {
      const activeExtensions = this.findExtensions(pointId);
      if (activeExtensions.length > 0) {
        this.conflictAttempts += 1;
        throw new PluginExtensionConflictError(
          `Extension point '${pointId}' has SINGLE cardinality and is already occupied.`,
          pluginId
        );
      }
    }

    const reg: ExtensionRegistration = {
      ...extension,
      pluginId,
      enabled: true,
      registeredAt: Date.now()
    };

    this.extensions.set(extId, reg);
    this.registeredExtsCount += 1;

    return createExtensionResult({
      success: true,
      extensionId: extId,
      pluginId,
      extensionPointId: pointId,
      warnings: [],
      errors: [],
      timestamp: Date.now()
    });
  }

  public unregisterExtension(pluginId: string, extensionId: string): ExtensionResult {
    const ext = this.extensions.get(extensionId);
    if (!ext) {
      throw new PluginExtensionError(`Extension '${extensionId}' not found.`, pluginId);
    }

    if (ext.pluginId !== pluginId) {
      throw new PluginExtensionError(`Extension '${extensionId}' does not belong to plugin '${pluginId}'.`, pluginId);
    }

    this.extensions.delete(extensionId);
    this.removedExtsCount += 1;

    return createExtensionResult({
      success: true,
      extensionId,
      pluginId,
      extensionPointId: ext.extensionPointId,
      warnings: [],
      errors: [],
      timestamp: Date.now()
    });
  }

  public unregisterPluginExtensions(pluginId: string): void {
    for (const [key, ext] of this.extensions.entries()) {
      if (ext.pluginId === pluginId) {
        this.extensions.delete(key);
        this.removedExtsCount += 1;
      }
    }
  }

  public findExtension(extensionId: string): ExtensionRegistration | null {
    this.lookups += 1;
    const ext = this.extensions.get(extensionId);
    if (ext && ext.enabled && this.isActivePlugin(ext.pluginId) && this.findExtensionPoint(ext.extensionPointId)) {
      return freezeDeepSafe(ext);
    }
    return null;
  }

  public findExtensions(pointId: string): ReadonlyArray<ExtensionRegistration> {
    this.lookups += 1;
    const pt = this.findExtensionPoint(pointId);
    if (!pt) {
      return Object.freeze([]);
    }

    const results: ExtensionRegistration[] = [];
    for (const ext of this.extensions.values()) {
      if (ext.extensionPointId === pointId && ext.enabled && this.isActivePlugin(ext.pluginId)) {
        results.push(ext);
      }
    }

    // Sort by priority desc, then registeredAt asc (FIFO)
    results.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.registeredAt - b.registeredAt;
    });

    return Object.freeze(results.map(e => freezeDeepSafe(e)));
  }

  public findExtensionsByPlugin(pluginId: string): ReadonlyArray<ExtensionRegistration> {
    this.lookups += 1;
    const results: ExtensionRegistration[] = [];
    for (const ext of this.extensions.values()) {
      if (ext.pluginId === pluginId && ext.enabled && this.isActivePlugin(pluginId) && this.findExtensionPoint(ext.extensionPointId)) {
        results.push(ext);
      }
    }
    return Object.freeze(results.map(e => freezeDeepSafe(e)));
  }

  public findExtensionsByPoint(pointId: string): ReadonlyArray<ExtensionRegistration> {
    return this.findExtensions(pointId);
  }

  public enableExtension(extensionId: string): void {
    const ext = this.extensions.get(extensionId);
    if (ext) {
      this.extensions.set(extensionId, { ...ext, enabled: true });
    }
  }

  public disableExtension(extensionId: string): void {
    const ext = this.extensions.get(extensionId);
    if (ext) {
      this.extensions.set(extensionId, { ...ext, enabled: false });
    }
  }

  public statistics(): ExtensionStatistics {
    const activeExts = Array.from(this.extensions.values())
      .filter(e => e.enabled && this.isActivePlugin(e.pluginId) && this.findExtensionPoint(e.extensionPointId)).length;

    return Object.freeze({
      registeredExtensions: this.registeredExtsCount,
      removedExtensions: this.removedExtsCount,
      activeExtensions: activeExts,
      failedRegistrations: this.failRegistrations,
      duplicateAttempts: this.dupAttempts,
      conflictAttempts: this.conflictAttempts,
      extensionLookups: this.lookups
    });
  }

  public health(): ExtensionHealth {
    const pluginCount = new Set(Array.from(this.extensions.values()).map(e => e.pluginId)).size;
    const totalOps = this.registeredExtsCount + this.failRegistrations;
    const failureRate = totalOps > 0 ? this.failRegistrations / totalOps : 0;
    const healthy = failureRate === 0;

    return Object.freeze({
      healthy,
      extensionCount: this.extensions.size,
      extensionPointCount: this.extensionPoints.size,
      pluginCount,
      failureRate,
      conflictCount: this.conflictAttempts,
      message: healthy ? 'Extension registry healthy' : `Extension failure rate is ${(failureRate * 100).toFixed(1)}%`
    });
  }

  public diagnostics(): Record<string, any> {
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health()
    });
  }

  public reset(): void {
    this.extensionPoints.clear();
    this.extensionPointOwners.clear();
    this.extensions.clear();
    this.registeredPointsCount = 0;
    this.removedPointsCount = 0;
    this.registeredExtsCount = 0;
    this.removedExtsCount = 0;
    this.failRegistrations = 0;
    this.dupAttempts = 0;
    this.conflictAttempts = 0;
    this.lookups = 0;
  }
}
