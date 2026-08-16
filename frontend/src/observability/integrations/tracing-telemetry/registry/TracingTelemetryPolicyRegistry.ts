import { TracingTelemetryPolicy } from '../models/policy';
import { TracingTelemetryPolicyError } from '../errors/TracingTelemetryErrors';
import { freezeDeepSafe } from '../../../models/monitoring';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export class TracingTelemetryPolicyRegistry {
  private readonly _policies = new Map<string, TracingTelemetryPolicy>();

  public registerPolicy(policy: TracingTelemetryPolicy): void {
    if (!policy.id || typeof policy.id !== 'string' || policy.id.trim() === '') {
      throw new TracingTelemetryPolicyError('Policy ID is missing or invalid.');
    }
    if (this._policies.has(policy.id)) {
      throw new TracingTelemetryPolicyError(`Policy with ID '${policy.id}' is already registered.`);
    }
    if (policy.priority === undefined || typeof policy.priority !== 'number') {
      throw new TracingTelemetryPolicyError('Policy priority is missing or invalid.');
    }
    if (!policy.telemetryType || typeof policy.telemetryType !== 'string' || policy.telemetryType.trim() === '') {
      throw new TracingTelemetryPolicyError('Policy telemetryType is missing or invalid.');
    }

    const redactedMetadata = policy.metadata ? safeNormalizeAndRedact(policy.metadata) : undefined;
    const redactedAttributes = policy.staticAttributes ? safeNormalizeAndRedact(policy.staticAttributes) : undefined;
    
    const policyToSave = {
      ...policy,
      metadata: redactedMetadata,
      staticAttributes: redactedAttributes
    };

    this._policies.set(policy.id, freezeDeepSafe(policyToSave) as TracingTelemetryPolicy);
  }

  public unregisterPolicy(policyId: string): void {
    if (!this._policies.has(policyId)) {
      throw new TracingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    this._policies.delete(policyId);
  }

  public getPolicy(policyId: string): TracingTelemetryPolicy | null {
    const policy = this._policies.get(policyId);
    return policy ? (freezeDeepSafe({ ...policy }) as TracingTelemetryPolicy) : null;
  }

  public listPolicies(): ReadonlyArray<TracingTelemetryPolicy> {
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

    return freezeDeepSafe(sorted) as ReadonlyArray<TracingTelemetryPolicy>;
  }

  private getSpecificity(policy: TracingTelemetryPolicy): number {
    if (policy.spanName && policy.spanName !== '*') {
      return 5;
    }
    if (policy.traceName && policy.traceName !== '*') {
      return 4;
    }
    if (policy.statusFilter && policy.statusFilter.length > 0) {
      return 3;
    }
    if (policy.spanKind) {
      return 2;
    }
    return 1;
  }

  public enablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new TracingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: true };
    this._policies.set(policyId, freezeDeepSafe(updated) as TracingTelemetryPolicy);
  }

  public disablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new TracingTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: false };
    this._policies.set(policyId, freezeDeepSafe(updated) as TracingTelemetryPolicy);
  }

  public clear(): void {
    this._policies.clear();
  }

  public getPolicyCount(): number {
    return this._policies.size;
  }
}
