import type { IPluginSandboxManager, IPluginSecurityManager } from '../interfaces/plugin-security';
import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import {
  type PluginSandboxSnapshot,
  type PluginResourceLimits,
  createSandboxSnapshot
} from '../models/security';
import {
  PluginSandboxError,
  PluginResourceLimitError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginSandboxManager implements IPluginSandboxManager {
  private readonly sandboxes = new Map<string, PluginSandboxSnapshot>();
  private readonly usageCounts = new Map<string, Map<keyof PluginResourceLimits, number>>();

  private createdCount = 0;
  private destroyedCount = 0;
  private validationFailuresCount = 0;
  private limitViolationsCount = 0;

  constructor(
    private readonly lifecycleManager: IPluginLifecycleManager,
    private readonly securityManager: IPluginSecurityManager
  ) {
    this.lifecycleManager.addActivateListener((pluginId) => {
      // Validate security profile on activation and initialize sandbox
      const profile = this.securityManager.getSecurityProfile(pluginId);
      if (!profile) {
        throw new PluginSandboxError(`Cannot activate plugin '${pluginId}': Security profile not defined.`, pluginId);
      }
      if (!this.sandboxes.has(pluginId)) {
        this.createSandbox(pluginId);
      }
      this.updateSandboxState(pluginId, 'ACTIVE');
    });

    this.lifecycleManager.addDeactivateListener((pluginId) => {
      this.updateSandboxState(pluginId, 'SUSPENDED');
    });

    this.lifecycleManager.addDisposeListener((pluginId) => {
      this.destroySandbox(pluginId);
    });
  }

  public createSandbox(pluginId: string, securityProfileId?: string): PluginSandboxSnapshot {
    if (this.sandboxes.has(pluginId)) {
      throw new PluginSandboxError(`Sandbox for plugin '${pluginId}' already exists.`, pluginId);
    }

    const profile = this.securityManager.getSecurityProfile(pluginId);
    const limits = profile?.resourceLimits || {};
    const allowed = profile?.allowedCapabilities || [];
    const denied = profile?.deniedCapabilities || [];

    const sandbox = createSandboxSnapshot({
      sandboxId: Math.random().toString(36).substring(2, 11),
      pluginId,
      state: 'CREATED',
      securityProfileId: securityProfileId || (profile ? 'default' : undefined),
      createdAt: Date.now(),
      resourceLimits: limits,
      allowedCapabilities: allowed,
      deniedCapabilities: denied
    });

    this.sandboxes.set(pluginId, sandbox);
    this.usageCounts.set(pluginId, new Map<keyof PluginResourceLimits, number>());
    this.createdCount += 1;

    return sandbox;
  }

  public destroySandbox(pluginId: string): void {
    if (this.sandboxes.has(pluginId)) {
      this.sandboxes.delete(pluginId);
      this.usageCounts.delete(pluginId);
      this.destroyedCount += 1;
    }
  }

  public getSandbox(pluginId: string): PluginSandboxSnapshot | null {
    const sandbox = this.sandboxes.get(pluginId);
    return sandbox ? freezeDeepSafe(sandbox) : null;
  }

  public listSandboxes(): ReadonlyArray<PluginSandboxSnapshot> {
    const list = Array.from(this.sandboxes.values());
    return Object.freeze(list.map(s => freezeDeepSafe(s)));
  }

  public updateSandboxState(pluginId: string, state: PluginSandboxSnapshot['state']): void {
    const existing = this.sandboxes.get(pluginId);
    if (!existing) {
      throw new PluginSandboxError(`Sandbox for plugin '${pluginId}' not found.`, pluginId);
    }

    // Validate transition
    const current = existing.state;
    let valid = false;

    if (current === 'CREATED' && (state === 'ACTIVE' || state === 'TERMINATED')) valid = true;
    else if (current === 'ACTIVE' && (state === 'SUSPENDED' || state === 'TERMINATED' || state === 'VIOLATION')) valid = true;
    else if (current === 'SUSPENDED' && (state === 'ACTIVE' || state === 'TERMINATED')) valid = true;
    else if (current === 'VIOLATION' && state === 'TERMINATED') valid = true;
    else if (current === 'TERMINATED' && state === 'ACTIVE') valid = false; // Cannot revive terminated sandbox directly

    if (!valid && current !== state) {
      throw new PluginSandboxError(`Invalid sandbox state transition from ${current} to ${state}.`, pluginId);
    }

    const updated = createSandboxSnapshot({
      ...existing,
      state
    });
    this.sandboxes.set(pluginId, updated);
  }

  public validateOperation(pluginId: string, capabilityId: string, metadata?: Record<string, unknown>): boolean {
    const sandbox = this.sandboxes.get(pluginId);
    if (!sandbox) {
      this.validationFailuresCount += 1;
      return false;
    }

    if (sandbox.state !== 'ACTIVE') {
      this.validationFailuresCount += 1;
      return false;
    }

    // Validate capability restrictions
    if (sandbox.deniedCapabilities.includes(capabilityId)) {
      this.validationFailuresCount += 1;
      this.securityManager.recordViolation(
        pluginId,
        capabilityId,
        `Blocked execution of explicitly denied capability '${capabilityId}' in sandbox.`,
        'HIGH',
        metadata
      );
      return false;
    }

    if (sandbox.allowedCapabilities.length > 0 && !sandbox.allowedCapabilities.includes(capabilityId)) {
      this.validationFailuresCount += 1;
      this.securityManager.recordViolation(
        pluginId,
        capabilityId,
        `Blocked execution of undeclared capability '${capabilityId}' in sandbox.`,
        'HIGH',
        metadata
      );
      return false;
    }

    return true;
  }

  public incrementUsage(pluginId: string, limitType: keyof PluginResourceLimits): void {
    const sandbox = this.sandboxes.get(pluginId);
    if (!sandbox) {
      throw new PluginSandboxError(`Sandbox for plugin '${pluginId}' not found.`, pluginId);
    }

    const counts = this.usageCounts.get(pluginId);
    if (!counts) {
      throw new PluginSandboxError(`Usage counts not initialized for plugin '${pluginId}'.`, pluginId);
    }

    const currentVal = counts.get(limitType) || 0;
    const limit = sandbox.resourceLimits[limitType];

    if (limit !== undefined && currentVal >= limit) {
      this.limitViolationsCount += 1;
      this.updateSandboxState(pluginId, 'VIOLATION');
      this.securityManager.recordViolation(
        pluginId,
        'RESOURCE_LIMIT_EXCEEDED',
        `Resource limit exceeded for limit type '${limitType}': ${currentVal} >= ${limit}.`,
        'HIGH'
      );
      throw new PluginResourceLimitError(`Resource limit exceeded for '${limitType}': ${limit}.`, pluginId);
    }

    counts.set(limitType, currentVal + 1);
  }

  public decrementUsage(pluginId: string, limitType: keyof PluginResourceLimits): void {
    const counts = this.usageCounts.get(pluginId);
    if (!counts) {
      throw new PluginSandboxError(`Usage counts not initialized for plugin '${pluginId}'.`, pluginId);
    }
    const currentVal = counts.get(limitType) || 0;
    if (currentVal > 0) {
      counts.set(limitType, currentVal - 1);
    }
  }

  public resourceUsage(pluginId: string): PluginResourceLimits {
    const counts = this.usageCounts.get(pluginId);
    if (!counts) {
      return {};
    }
    const limits: Record<string, number> = {};
    for (const [key, val] of counts.entries()) {
      limits[key] = val;
    }
    return Object.freeze(limits as PluginResourceLimits);
  }

  public statistics(): Record<string, any> {
    return Object.freeze({
      createdSandboxes: this.createdCount,
      destroyedSandboxes: this.destroyedCount,
      activeSandboxes: this.sandboxes.size,
      validationFailures: this.validationFailuresCount,
      limitViolations: this.limitViolationsCount
    });
  }

  public health(): Record<string, any> {
    const hasViolations = Array.from(this.sandboxes.values()).some(s => s.state === 'VIOLATION');
    return Object.freeze({
      healthy: !hasViolations,
      activeSandboxCount: this.sandboxes.size,
      message: hasViolations ? 'Unhealthy sandboxes detected' : 'Sandbox manager healthy'
    });
  }

  public diagnostics(): Record<string, any> {
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health()
    });
  }

  public reset(): void {
    this.sandboxes.clear();
    this.usageCounts.clear();
    this.createdCount = 0;
    this.destroyedCount = 0;
    this.validationFailuresCount = 0;
    this.limitViolationsCount = 0;
  }
}
