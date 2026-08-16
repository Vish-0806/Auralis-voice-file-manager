import { LoggingMetricsPolicy } from '../models/policy';
import { LoggingMetricsPolicyError } from '../errors/LoggingMetricsErrors';
import { freezeDeepSafe } from '../../../models/monitoring';
import { safeNormalizeAndRedact } from '../../../correlation/provider/CorrelationProvider';

export class LoggingMetricsPolicyRegistry {
  private readonly _policies = new Map<string, LoggingMetricsPolicy>();

  public registerPolicy(policy: LoggingMetricsPolicy): void {
    if (!policy.id || typeof policy.id !== 'string' || policy.id.trim() === '') {
      throw new LoggingMetricsPolicyError('Policy ID is missing or invalid.');
    }
    if (this._policies.has(policy.id)) {
      throw new LoggingMetricsPolicyError(`Policy with ID '${policy.id}' is already registered.`);
    }
    if (!policy.metricName || typeof policy.metricName !== 'string' || policy.metricName.trim() === '') {
      throw new LoggingMetricsPolicyError('Policy metricName is missing or invalid.');
    }
    if (policy.priority === undefined || typeof policy.priority !== 'number') {
      throw new LoggingMetricsPolicyError('Policy priority is missing or invalid.');
    }

    const redactedMetadata = policy.metadata ? safeNormalizeAndRedact(policy.metadata) : undefined;
    const redactedLabels = policy.labels ? safeNormalizeAndRedact(policy.labels) : undefined;
    const policyToSave = {
      ...policy,
      metadata: redactedMetadata,
      labels: redactedLabels
    };

    this._policies.set(policy.id, freezeDeepSafe(policyToSave) as LoggingMetricsPolicy);
  }

  public unregisterPolicy(policyId: string): void {
    if (!this._policies.has(policyId)) {
      throw new LoggingMetricsPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    this._policies.delete(policyId);
  }

  public getPolicy(policyId: string): LoggingMetricsPolicy | null {
    const policy = this._policies.get(policyId);
    return policy ? (freezeDeepSafe({ ...policy }) as LoggingMetricsPolicy) : null;
  }

  public listPolicies(): ReadonlyArray<LoggingMetricsPolicy> {
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

    return freezeDeepSafe(sorted) as ReadonlyArray<LoggingMetricsPolicy>;
  }

  private getSpecificity(policy: LoggingMetricsPolicy): number {
    const hasSpecificLogger = policy.loggerName && policy.loggerName !== '*';
    const hasSpecificLevel = policy.minLevel && policy.minLevel !== 'TRACE';

    if (hasSpecificLogger) {
      return 3;
    }
    if (hasSpecificLevel) {
      return 2;
    }
    return 1;
  }

  public enablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new LoggingMetricsPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: true };
    this._policies.set(policyId, freezeDeepSafe(updated) as LoggingMetricsPolicy);
  }

  public disablePolicy(policyId: string): void {
    const policy = this._policies.get(policyId);
    if (!policy) {
      throw new LoggingMetricsPolicyError(`Policy with ID '${policyId}' not found.`);
    }
    const updated = { ...policy, enabled: false };
    this._policies.set(policyId, freezeDeepSafe(updated) as LoggingMetricsPolicy);
  }

  public clear(): void {
    this._policies.clear();
  }

  public getPolicyCount(): number {
    return this._policies.size;
  }
}
