import {
  type PluginSecurityPolicy,
  type PluginPermissionActionValue,
  type PluginPermissionScopeValue
} from '../models/security';
import { PluginPolicyError } from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

export class PluginPolicyManager {
  private readonly policies = new Map<string, PluginSecurityPolicy>();
  private readonly registrationTimes = new Map<string, number>();

  private registeredCount = 0;
  private removedCount = 0;
  private evaluationsCount = 0;
  private denyMatchesCount = 0;
  private allowMatchesCount = 0;

  public registerPolicy(policy: PluginSecurityPolicy): void {
    if (!policy.id || !policy.name) {
      throw new PluginPolicyError(`policy id and name are required.`);
    }

    if (this.policies.has(policy.id)) {
      throw new PluginPolicyError(`Policy with id '${policy.id}' is already registered.`);
    }

    this.policies.set(policy.id, policy);
    this.registrationTimes.set(policy.id, Date.now());
    this.registeredCount += 1;
  }

  public removePolicy(policyId: string): void {
    if (!this.policies.has(policyId)) {
      throw new PluginPolicyError(`Policy '${policyId}' not found.`);
    }
    this.policies.delete(policyId);
    this.registrationTimes.delete(policyId);
    this.removedCount += 1;
  }

  public getPolicy(policyId: string): PluginSecurityPolicy | null {
    const policy = this.policies.get(policyId);
    return policy ? freezeDeepSafe(policy) : null;
  }

  public listPolicies(): ReadonlyArray<PluginSecurityPolicy> {
    const list = Array.from(this.policies.values());
    return Object.freeze(list.map(p => freezeDeepSafe(p)));
  }

  public enablePolicy(policyId: string): void {
    const existing = this.policies.get(policyId);
    if (existing) {
      this.policies.set(policyId, { ...existing, enabled: true });
    }
  }

  public disablePolicy(policyId: string): void {
    const existing = this.policies.get(policyId);
    if (existing) {
      this.policies.set(policyId, { ...existing, enabled: false });
    }
  }

  public evaluate(
    action: PluginPermissionActionValue,
    scope: PluginPermissionScopeValue,
    targetPluginId?: string
  ): { effect: 'ALLOW' | 'DENY' | 'NEUTRAL'; policyId?: string } {
    this.evaluationsCount += 1;

    const matches: PluginSecurityPolicy[] = [];
    for (const policy of this.policies.values()) {
      if (!policy.enabled) continue;

      const actionMatch = policy.action === '*' || policy.action === action;
      const scopeMatch = policy.scopes.includes(scope);
      const pluginMatch = !policy.targetPluginId || policy.targetPluginId === targetPluginId;

      if (actionMatch && scopeMatch && pluginMatch) {
        matches.push(policy);
      }
    }

    if (matches.length === 0) {
      return { effect: 'NEUTRAL' };
    }

    // Sort by priority desc, then registration time asc (FIFO)
    matches.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      const timeA = this.registrationTimes.get(a.id) || 0;
      const timeB = this.registrationTimes.get(b.id) || 0;
      return timeA - timeB;
    });

    // Check for explicit DENY first (DENY wins)
    const denyMatch = matches.find(m => m.effect === 'DENY');
    if (denyMatch) {
      this.denyMatchesCount += 1;
      return { effect: 'DENY', policyId: denyMatch.id };
    }

    // Otherwise, check for ALLOW
    const allowMatch = matches.find(m => m.effect === 'ALLOW');
    if (allowMatch) {
      this.allowMatchesCount += 1;
      return { effect: 'ALLOW', policyId: allowMatch.id };
    }

    return { effect: 'NEUTRAL' };
  }

  public statistics(): Record<string, any> {
    return Object.freeze({
      registeredPolicies: this.registeredCount,
      removedPolicies: this.removedCount,
      activePolicies: this.policies.size,
      evaluations: this.evaluationsCount,
      denyMatches: this.denyMatchesCount,
      allowMatches: this.allowMatchesCount
    });
  }

  public health(): Record<string, any> {
    return Object.freeze({
      healthy: true,
      policyCount: this.policies.size,
      message: 'Policy manager healthy'
    });
  }

  public diagnostics(): Record<string, any> {
    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health()
    });
  }

  public reset(): void {
    this.policies.clear();
    this.registrationTimes.clear();
    this.registeredCount = 0;
    this.removedCount = 0;
    this.evaluationsCount = 0;
    this.denyMatchesCount = 0;
    this.allowMatchesCount = 0;
  }
}
