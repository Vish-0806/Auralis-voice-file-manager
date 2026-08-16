import { MonitoringAlertPolicy } from '../models/policy';
import { MonitoringAlertingPolicyError } from '../errors/MonitoringAlertingErrors';
import { freezeDeepSafe } from '../../../models/monitoring';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export class MonitoringAlertPolicyRegistry {
  private readonly _policies = new Map<string, MonitoringAlertPolicy>();

  public registerPolicy(policy: MonitoringAlertPolicy): void {
    if (!policy.id || typeof policy.id !== 'string' || policy.id.trim() === '') {
      throw new MonitoringAlertingPolicyError('Policy ID is missing or invalid.');
    }
    if (this._policies.has(policy.id)) {
      throw new MonitoringAlertingPolicyError(`Policy with ID '${policy.id}' is already registered.`);
    }
    if (!policy.ruleId || typeof policy.ruleId !== 'string' || policy.ruleId.trim() === '') {
      throw new MonitoringAlertingPolicyError('Policy ruleId is missing or invalid.');
    }
    const redactedMetadata = policy.metadata ? safeNormalizeAndRedact(policy.metadata) : undefined;
    const policyToSave = { ...policy, metadata: redactedMetadata };
    this._policies.set(policy.id, freezeDeepSafe(policyToSave) as MonitoringAlertPolicy);
  }

  public unregisterPolicy(policyId: string): void {
    if (!this._policies.has(policyId)) {
      throw new MonitoringAlertingPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    this._policies.delete(policyId);
  }

  public getPolicy(policyId: string): MonitoringAlertPolicy | null {
    const policy = this._policies.get(policyId);
    return policy ? (freezeDeepSafe({ ...policy }) as MonitoringAlertPolicy) : null;
  }

  public listPolicies(): ReadonlyArray<MonitoringAlertPolicy> {
    return freezeDeepSafe(Array.from(this._policies.values())) as ReadonlyArray<MonitoringAlertPolicy>;
  }

  public enablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new MonitoringAlertingPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: true };
    this._policies.set(policyId, freezeDeepSafe(updated) as MonitoringAlertPolicy);
  }

  public disablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new MonitoringAlertingPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: false };
    this._policies.set(policyId, freezeDeepSafe(updated) as MonitoringAlertPolicy);
  }

  public clear(): void {
    this._policies.clear();
  }

  public getPolicyCount(): number {
    return this._policies.size;
  }
}
