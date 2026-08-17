import { AlertingTelemetryPolicy } from '../models/policy';
import { AlertingTelemetryPolicyError } from '../errors/AlertingTelemetryErrors';
import { freezeDeepSafe } from '../../../models/monitoring';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export class AlertingTelemetryPolicyRegistry {
  private readonly _policies = new Map<string, AlertingTelemetryPolicy>();

  public registerPolicy(policy: AlertingTelemetryPolicy): void {
    if (!policy.id || typeof policy.id !== 'string' || policy.id.trim() === '') {
      throw new AlertingTelemetryPolicyError('Policy ID is missing or invalid.');
    }
    if (this._policies.has(policy.id)) {
      throw new AlertingTelemetryPolicyError(`Policy with ID '${policy.id}' is already registered.`);
    }
    if (policy.priority === undefined || typeof policy.priority !== 'number') {
      throw new AlertingTelemetryPolicyError('Policy priority is missing or invalid.');
    }
    if (!policy.telemetryType || typeof policy.telemetryType !== 'string' || policy.telemetryType.trim() === '') {
      throw new AlertingTelemetryPolicyError('Policy telemetryType is missing or invalid.');
    }

    const redactedMetadata = policy.metadata ? safeNormalizeAndRedact(policy.metadata) : undefined;
    const redactedAttributes = policy.staticAttributes ? safeNormalizeAndRedact(policy.staticAttributes) : undefined;

    const policyToSave: AlertingTelemetryPolicy = {
      ...policy,
      metadata: redactedMetadata,
      staticAttributes: redactedAttributes
    };

    this._policies.set(policy.id, freezeDeepSafe(policyToSave) as AlertingTelemetryPolicy);
  }

  public unregisterPolicy(policyId: string): void {
    if (!this._policies.has(policyId)) {
      throw new AlertingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    this._policies.delete(policyId);
  }

  public getPolicy(policyId: string): AlertingTelemetryPolicy | null {
    const policy = this._policies.get(policyId);
    return policy ? (freezeDeepSafe({ ...policy }) as AlertingTelemetryPolicy) : null;
  }

  public listPolicies(): ReadonlyArray<AlertingTelemetryPolicy> {
    const sorted = Array.from(this._policies.values());

    sorted.sort((a, b) => {
      const specA = this.getSpecificity(a);
      const specB = this.getSpecificity(b);

      if (specB !== specA) {
        return specB - specA;
      }

      if (b.priority !== a.priority) {
        return b.priority - a.priority;
      }

      return a.id.localeCompare(b.id);
    });

    return freezeDeepSafe(sorted) as ReadonlyArray<AlertingTelemetryPolicy>;
  }

  private getSpecificity(policy: AlertingTelemetryPolicy): number {
    if (policy.alertId !== undefined && policy.alertId !== '*') {
      return 7;
    }
    if (policy.fingerprint !== undefined && policy.fingerprint !== '*') {
      return 6;
    }
    if (policy.ruleId !== undefined && policy.ruleId !== '*') {
      return 5;
    }
    if (policy.sourceId !== undefined && policy.sourceId !== '*') {
      return 4;
    }
    if (policy.severity !== undefined && (policy.severity as string) !== '*') {
      return 3;
    }
    if (
      (policy.status !== undefined && policy.status !== '*') ||
      (policy.lifecycleState !== undefined && (policy.lifecycleState as string) !== '*') ||
      (policy.orchestrationStatus !== undefined && policy.orchestrationStatus !== '*') ||
      (policy.notificationStatus !== undefined && policy.notificationStatus !== '*')
    ) {
      return 2;
    }
    return 1;
  }

  public enablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new AlertingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: true };
    this._policies.set(policyId, freezeDeepSafe(updated) as AlertingTelemetryPolicy);
  }

  public disablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new AlertingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: false };
    this._policies.set(policyId, freezeDeepSafe(updated) as AlertingTelemetryPolicy);
  }

  public clear(): void {
    this._policies.clear();
  }

  public getPolicyCount(): number {
    return this._policies.size;
  }
}
