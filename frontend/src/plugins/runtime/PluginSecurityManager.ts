import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginSecurityManager } from '../interfaces/plugin-security';
import { PluginPolicyManager } from './PluginPolicyManager';
import {
  type PluginPermission,
  type PluginPermissionActionValue,
  type PluginPermissionScopeValue,
  type PluginSecurityProfile,
  type PluginSecurityDecision,
  type PluginSecurityViolation,
  type PluginAuditRecord,
  type PluginSecurityStatistics,
  type PluginSecurityHealth,
  type PluginSecurityDiagnostics,
  createSecurityDecision,
  createSecurityViolation,
  createAuditRecord
} from '../models/security';
import {
  PluginPermissionError,
  PluginSecurityProfileError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginSecurityManager implements IPluginSecurityManager {
  private readonly permissions = new Map<string, PluginPermission>();
  private readonly profiles = new Map<string, PluginSecurityProfile>();
  private readonly auditRecords: PluginAuditRecord[] = [];
  private readonly violationsRecords: PluginSecurityViolation[] = [];

  private totalDecisionsCount = 0;
  private allowedDecisionsCount = 0;
  private deniedDecisionsCount = 0;
  private totalViolationsCount = 0;
  private criticalViolationsCount = 0;
  private policyDenialsCount = 0;
  private permissionDenialsCount = 0;
  private capabilityDenialsCount = 0;
  private sandboxDenialsCount = 0;

  private maxAuditHistorySize = 100;
  private evalTimes: number[] = [];

  constructor(
    private readonly lifecycleManager: IPluginLifecycleManager,
    private readonly policyManager: PluginPolicyManager,
    options?: { maxAuditHistorySize?: number }
  ) {
    if (options?.maxAuditHistorySize !== undefined) {
      this.maxAuditHistorySize = options.maxAuditHistorySize;
    }

    this.lifecycleManager.addDisposeListener((pluginId) => {
      this.removeSecurityProfile(pluginId);
      // Revoke all permissions for the plugin
      for (const [key, perm] of this.permissions.entries()) {
        if (perm.pluginId === pluginId) {
          this.permissions.delete(key);
        }
      }
    });
  }

  private getCanonicalPermissionId(pluginId: string, id: string): string {
    return `${pluginId}:${id}`;
  }

  public registerPermission(
    pluginId: string,
    action: PluginPermissionActionValue,
    scope: PluginPermissionScopeValue,
    description?: string
  ): PluginPermission {
    if (!pluginId || !action || !scope) {
      throw new PluginPermissionError(`pluginId, action, and scope are required.`, pluginId);
    }

    const id = Math.random().toString(36).substring(2, 11);
    const canonicalId = this.getCanonicalPermissionId(pluginId, id);

    const permission: PluginPermission = {
      id,
      pluginId,
      action,
      scope,
      granted: true,
      description,
      createdAt: Date.now()
    };

    this.permissions.set(canonicalId, permission);
    return freezeDeepSafe(permission);
  }

  public revokePermission(pluginId: string, permissionId: string): void {
    const canonicalId = this.getCanonicalPermissionId(pluginId, permissionId);
    if (!this.permissions.has(canonicalId)) {
      throw new PluginPermissionError(`Permission '${permissionId}' not found for plugin '${pluginId}'.`, pluginId);
    }
    this.permissions.delete(canonicalId);
  }

  public getPermission(pluginId: string, permissionId: string): PluginPermission | null {
    const canonicalId = this.getCanonicalPermissionId(pluginId, permissionId);
    const perm = this.permissions.get(canonicalId);
    return perm ? freezeDeepSafe(perm) : null;
  }

  public listPermissions(pluginId?: string): ReadonlyArray<PluginPermission> {
    const list = Array.from(this.permissions.values());
    if (pluginId) {
      return Object.freeze(list.filter(p => p.pluginId === pluginId).map(p => freezeDeepSafe(p)));
    }
    return Object.freeze(list.map(p => freezeDeepSafe(p)));
  }

  public checkPermission(pluginId: string, action: PluginPermissionActionValue, scope: PluginPermissionScopeValue): boolean {
    const decision = this.evaluate(pluginId, action, scope);
    return decision.allowed;
  }

  public evaluate(pluginId: string, action: PluginPermissionActionValue, scope: PluginPermissionScopeValue): PluginSecurityDecision {
    const startTime = Date.now();
    this.totalDecisionsCount += 1;
    const decisionId = Math.random().toString(36).substring(2, 11);

    const failClosed = (reason: string, matchedPolicyId?: string, matchedPermissionId?: string): PluginSecurityDecision => {
      this.deniedDecisionsCount += 1;
      this.evalTimes.push(Date.now() - startTime);
      const dec = createSecurityDecision({
        decisionId,
        pluginId,
        action,
        scope,
        allowed: false,
        reason,
        matchedPolicyId,
        matchedPermissionId,
        timestamp: Date.now()
      });
      this.logAudit(pluginId, 'EVALUATE', action, false, reason);
      return dec;
    };

    try {
      // 1. Check if security profile exists and is enabled
      const profile = this.profiles.get(pluginId);
      if (!profile) {
        return failClosed(`Denied: Security profile does not exist for plugin '${pluginId}'.`);
      }
      if (!profile.enabled) {
        return failClosed(`Denied: Security profile is disabled for plugin '${pluginId}'.`);
      }

      // 2. Evaluate capability exclusions if applicable
      if (profile.deniedCapabilities.includes(action as string)) {
        this.capabilityDenialsCount += 1;
        return failClosed(`Denied: Capability '${action}' is explicitly denied in security profile.`);
      }

      // 3. Evaluate matching permissions (DENY overrides ALLOW)
      let permissionAllowed = false;
      let matchedPermissionId: string | undefined;

      const pluginPerms = this.listPermissions(pluginId);
      for (const perm of pluginPerms) {
        const matches = (perm.action === '*' || perm.action === action) && perm.scope === scope;
        if (matches) {
          if (!perm.granted) {
            this.permissionDenialsCount += 1;
            return failClosed(`Denied: Explicit DENY permission matched.`, undefined, perm.id);
          }
          permissionAllowed = true;
          matchedPermissionId = perm.id;
        }
      }

      // 4. Evaluate Policy Manager rules
      const policyEval = this.policyManager.evaluate(action, scope, pluginId);
      if (policyEval.effect === 'DENY') {
        this.policyDenialsCount += 1;
        return failClosed(`Denied: Explicit policy DENY rule matched (policy: ${policyEval.policyId}).`, policyEval.policyId);
      }

      // 5. Final Decision Logic (ALLOW must be explicitly matched)
      const allowed = permissionAllowed || policyEval.effect === 'ALLOW';
      const reason = allowed
        ? `Allowed: Explicit permission or policy matched.`
        : `Denied: Default Deny. No matching ALLOW rule found.`;

      if (allowed) {
        this.allowedDecisionsCount += 1;
        this.evalTimes.push(Date.now() - startTime);
        const dec = createSecurityDecision({
          decisionId,
          pluginId,
          action,
          scope,
          allowed: true,
          reason,
          matchedPolicyId: policyEval.policyId,
          matchedPermissionId,
          timestamp: Date.now()
        });
        this.logAudit(pluginId, 'EVALUATE', action, true, reason);
        return dec;
      } else {
        this.deniedDecisionsCount += 1;
        this.evalTimes.push(Date.now() - startTime);
        const dec = createSecurityDecision({
          decisionId,
          pluginId,
          action,
          scope,
          allowed: false,
          reason,
          matchedPolicyId: policyEval.policyId,
          matchedPermissionId,
          timestamp: Date.now()
        });
        this.logAudit(pluginId, 'EVALUATE', action, false, reason);
        return dec;
      }

    } catch (err: any) {
      return failClosed(`Denied: Internal evaluation failure: ${err.message}`);
    }
  }

  public createSecurityProfile(
    pluginId: string,
    profile: Omit<PluginSecurityProfile, 'pluginId' | 'createdAt' | 'updatedAt'>
  ): PluginSecurityProfile {
    if (!pluginId) {
      throw new PluginSecurityProfileError(`pluginId is required.`);
    }

    if (this.profiles.has(pluginId)) {
      throw new PluginSecurityProfileError(`Security profile for plugin '${pluginId}' already exists.`);
    }

    const securityProfile: PluginSecurityProfile = {
      ...profile,
      pluginId,
      createdAt: Date.now(),
      updatedAt: Date.now()
    };

    this.profiles.set(pluginId, securityProfile);
    this.logAudit(pluginId, 'PROFILE_CREATE', '*', true, `Created security profile`);
    return freezeDeepSafe(securityProfile);
  }

  public getSecurityProfile(pluginId: string): PluginSecurityProfile | null {
    const profile = this.profiles.get(pluginId);
    return profile ? freezeDeepSafe(profile) : null;
  }

  public updateSecurityProfile(
    pluginId: string,
    profile: Partial<Omit<PluginSecurityProfile, 'pluginId' | 'createdAt' | 'updatedAt'>>
  ): PluginSecurityProfile {
    const existing = this.profiles.get(pluginId);
    if (!existing) {
      throw new PluginSecurityProfileError(`Security profile for plugin '${pluginId}' not found.`);
    }

    const updated: PluginSecurityProfile = {
      ...existing,
      ...profile,
      updatedAt: Date.now()
    };

    this.profiles.set(pluginId, updated);
    this.logAudit(pluginId, 'PROFILE_UPDATE', '*', true, `Updated security profile`);
    return freezeDeepSafe(updated);
  }

  public removeSecurityProfile(pluginId: string): void {
    if (this.profiles.has(pluginId)) {
      this.profiles.delete(pluginId);
      this.logAudit(pluginId, 'PROFILE_DELETE', '*', true, `Deleted security profile`);
    }
  }

  public recordViolation(
    pluginId: string,
    action: PluginPermissionActionValue,
    reason: string,
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    metadata?: Record<string, unknown>
  ): PluginSecurityViolation {
    this.totalViolationsCount += 1;
    if (severity === 'CRITICAL') {
      this.criticalViolationsCount += 1;
    }

    const violationId = Math.random().toString(36).substring(2, 11);
    const violation = createSecurityViolation({
      violationId,
      pluginId,
      action,
      reason,
      severity,
      timestamp: Date.now(),
      metadata: metadata || {}
    });

    this.violationsRecords.push(violation);
    this.logAudit(pluginId, 'VIOLATION', action, false, `Violation recorded (severity: ${severity}): ${reason}`, metadata);
    return violation;
  }

  public auditHistory(): ReadonlyArray<PluginAuditRecord> {
    return Object.freeze([...this.auditRecords]);
  }

  public statistics(): PluginSecurityStatistics {
    return Object.freeze({
      totalDecisions: this.totalDecisionsCount,
      allowedDecisions: this.allowedDecisionsCount,
      deniedDecisions: this.deniedDecisionsCount,
      violations: this.totalViolationsCount,
      criticalViolations: this.criticalViolationsCount,
      policyDenials: this.policyDenialsCount,
      permissionDenials: this.permissionDenialsCount,
      capabilityDenials: this.capabilityDenialsCount,
      sandboxDenials: this.sandboxDenialsCount
    });
  }

  public health(): PluginSecurityHealth {
    const totalOps = this.totalDecisionsCount;
    const denialRate = totalOps > 0 ? this.deniedDecisionsCount / totalOps : 0;
    const violationRate = totalOps > 0 ? this.totalViolationsCount / totalOps : 0;
    
    // Healthy if no critical violations and violation rate under 5%
    const healthy = this.criticalViolationsCount === 0 && violationRate < 0.05;

    return Object.freeze({
      healthy,
      permissionCount: this.permissions.size,
      policyCount: this.policyManager.listPolicies().length,
      activeSandboxCount: 0, // Injected downstream if sandbox manager active
      violationRate,
      denialRate,
      message: healthy ? 'Security system healthy' : `Unhealthy security status: ${this.criticalViolationsCount} critical violations.`
    });
  }

  public diagnostics(): PluginSecurityDiagnostics {
    const avg = this.evalTimes.length > 0 ? this.evalTimes.reduce((a, b) => a + b, 0) / this.evalTimes.length : 0;
    const max = this.evalTimes.length > 0 ? Math.max(...this.evalTimes) : 0;
    const min = this.evalTimes.length > 0 ? Math.min(...this.evalTimes) : 0;

    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health(),
      registeredPermissions: this.permissions.size,
      registeredPolicies: this.policyManager.listPolicies().length,
      securityProfiles: this.profiles.size,
      activeSandboxes: 0,
      auditHistorySize: this.auditRecords.length,
      averageEvaluationTime: avg,
      maximumEvaluationTime: max,
      minimumEvaluationTime: min
    });
  }

  public reset(): void {
    this.permissions.clear();
    this.profiles.clear();
    this.auditRecords.length = 0;
    this.violationsRecords.length = 0;
    this.evalTimes.length = 0;
    this.totalDecisionsCount = 0;
    this.allowedDecisionsCount = 0;
    this.deniedDecisionsCount = 0;
    this.totalViolationsCount = 0;
    this.criticalViolationsCount = 0;
    this.policyDenialsCount = 0;
    this.permissionDenialsCount = 0;
    this.capabilityDenialsCount = 0;
    this.sandboxDenialsCount = 0;
    this.policyManager.reset();
  }

  private logAudit(
    pluginId: string,
    eventType: string,
    action: PluginPermissionActionValue,
    allowed: boolean,
    reason: string,
    metadata?: Record<string, unknown>
  ): void {
    const auditId = Math.random().toString(36).substring(2, 11);
    const record = createAuditRecord({
      auditId,
      pluginId,
      eventType,
      action,
      allowed,
      reason,
      timestamp: Date.now(),
      metadata: metadata || {}
    });

    this.auditRecords.push(record);
    if (this.auditRecords.length > this.maxAuditHistorySize) {
      this.auditRecords.shift();
    }
  }
}
