import { DiagnosticsTelemetryPolicy } from '../models/policy';
import { DiagnosticsTelemetryPolicyError } from '../errors/DiagnosticsTelemetryErrors';
import { freezeDeepSafe } from '../../../models/monitoring';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export class DiagnosticsTelemetryPolicyRegistry {
  private readonly _policies = new Map<string, DiagnosticsTelemetryPolicy>();

  public registerPolicy(policy: DiagnosticsTelemetryPolicy): void {
    if (!policy.id || typeof policy.id !== 'string' || policy.id.trim() === '') {
      throw new DiagnosticsTelemetryPolicyError('Policy ID is missing or invalid.');
    }
    if (this._policies.has(policy.id)) {
      throw new DiagnosticsTelemetryPolicyError(`Policy with ID '${policy.id}' is already registered.`);
    }
    if (policy.priority === undefined || typeof policy.priority !== 'number') {
      throw new DiagnosticsTelemetryPolicyError('Policy priority is missing or invalid.');
    }
    if (!policy.telemetryType || typeof policy.telemetryType !== 'string' || policy.telemetryType.trim() === '') {
      throw new DiagnosticsTelemetryPolicyError('Policy telemetryType is missing or invalid.');
    }
    if (policy.level !== 'RUN' && policy.level !== 'RESULT') {
      throw new DiagnosticsTelemetryPolicyError('Policy level must be RUN or RESULT.');
    }

    const redactedMetadata = policy.metadata ? safeNormalizeAndRedact(policy.metadata) : undefined;
    const redactedAttributes = policy.staticAttributes ? safeNormalizeAndRedact(policy.staticAttributes) : undefined;

    const policyToSave = {
      ...policy,
      metadata: redactedMetadata,
      staticAttributes: redactedAttributes
    };

    this._policies.set(policy.id, freezeDeepSafe(policyToSave) as DiagnosticsTelemetryPolicy);
  }

  public unregisterPolicy(policyId: string): void {
    if (!this._policies.has(policyId)) {
      throw new DiagnosticsTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    this._policies.delete(policyId);
  }

  public getPolicy(policyId: string): DiagnosticsTelemetryPolicy | null {
    const policy = this._policies.get(policyId);
    return policy ? (freezeDeepSafe({ ...policy }) as DiagnosticsTelemetryPolicy) : null;
  }

  public listPolicies(): ReadonlyArray<DiagnosticsTelemetryPolicy> {
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

    return freezeDeepSafe(sorted) as ReadonlyArray<DiagnosticsTelemetryPolicy>;
  }

  private getSpecificity(policy: DiagnosticsTelemetryPolicy): number {
    if (policy.checkId && policy.checkId !== '*') {
      return 6;
    }
    if (policy.sourceId && policy.sourceId !== '*') {
      return 5;
    }
    if (policy.category) {
      return 4;
    }
    if (policy.severity) {
      return 3;
    }
    if (policy.status) {
      return 2;
    }
    return 1;
  }

  public enablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new DiagnosticsTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: true };
    this._policies.set(policyId, freezeDeepSafe(updated) as DiagnosticsTelemetryPolicy);
  }

  public disablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new DiagnosticsTelemetryPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: false };
    this._policies.set(policyId, freezeDeepSafe(updated) as DiagnosticsTelemetryPolicy);
  }

  public clear(): void {
    this._policies.clear();
  }

  public getPolicyCount(): number {
    return this._policies.size;
  }
}
