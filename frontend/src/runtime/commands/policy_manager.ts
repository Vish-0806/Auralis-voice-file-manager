/**
 * Policy Manager Implementation (Phase 16.6.5).
 *
 * Implements IPolicyManager managing execution policies, environment restriction evaluation,
 * time-based policy constraints, custom policy predicates, policy decision telemetry,
 * statistics, and health reporting.
 */

import {
  CommandExecutionContext,
  CommandExecutionRequest,
  ExecutionPolicy,
  PolicyDecision,
  PolicyDiagnostics,
  PolicyHealth,
  PolicyStatistics,
  createExecutionPolicy,
  createPolicyDecision,
  createPolicyDiagnostics,
  createPolicyHealth,
  createPolicyStatistics,
} from './models';
import { CommandProviderException } from './exceptions';
import { IPolicyManager } from './interfaces';

export class PolicyManager implements IPolicyManager {
  private readonly _policies = new Map<string, ExecutionPolicy>();

  private _totalEvaluations = 0;
  private _allowedEvaluations = 0;
  private _deniedEvaluations = 0;
  private _evaluationTimes: number[] = [];

  public registerPolicy(
    policy: Partial<ExecutionPolicy> & {
      name: string;
      evaluate: ExecutionPolicy['evaluate'];
    },
  ): ExecutionPolicy {
    if (!policy) {
      throw new CommandProviderException('Policy registration cannot be null or undefined.');
    }
    if (!policy.name || !policy.name.trim()) {
      throw new CommandProviderException('Policy name cannot be empty.');
    }
    if (!policy.evaluate) {
      throw new CommandProviderException('Policy evaluate function cannot be null or undefined.');
    }

    const frozen = createExecutionPolicy({
      policyId: policy.policyId,
      name: policy.name.trim(),
      description: policy.description,
      enabled: policy.enabled ?? true,
      evaluate: policy.evaluate,
    });

    this._policies.set(frozen.policyId, frozen);
    return frozen;
  }

  public removePolicy(policyId: string): boolean {
    if (!policyId || !policyId.trim()) {
      return false;
    }
    return this._policies.delete(policyId.trim());
  }

  public listPolicies(): ReadonlyArray<ExecutionPolicy> {
    return Object.freeze(Array.from(this._policies.values()));
  }

  public async evaluatePolicy(
    request: CommandExecutionRequest,
    context?: CommandExecutionContext,
  ): Promise<PolicyDecision> {
    this._totalEvaluations++;
    const start = performance ? performance.now() : Date.now();

    const activePolicies = Array.from(this._policies.values()).filter((p) => p.enabled);

    for (const policy of activePolicies) {
      try {
        const decision = await policy.evaluate(request, context);
        if (!decision.allowed) {
          this._deniedEvaluations++;
          const end = performance ? performance.now() : Date.now();
          this.recordTiming(Math.max(0, Math.round((end - start) * 100) / 100));

          return createPolicyDecision({
            allowed: false,
            policyId: policy.policyId,
            reason: decision.reason ?? `Execution denied by policy '${policy.name}'.`,
          });
        }
      } catch (err: any) {
        this._deniedEvaluations++;
        const end = performance ? performance.now() : Date.now();
        this.recordTiming(Math.max(0, Math.round((end - start) * 100) / 100));

        return createPolicyDecision({
          allowed: false,
          policyId: policy.policyId,
          reason: `Policy '${policy.name}' evaluation failed: ${err?.message ?? 'Unknown error'}.`,
        });
      }
    }

    const end = performance ? performance.now() : Date.now();
    this.recordTiming(Math.max(0, Math.round((end - start) * 100) / 100));
    this._allowedEvaluations++;

    return createPolicyDecision({
      allowed: true,
    });
  }

  public statistics(): PolicyStatistics {
    const totalMs = this._evaluationTimes.reduce((a, b) => a + b, 0);
    const avgMs = this._evaluationTimes.length > 0 ? totalMs / this._evaluationTimes.length : 0;

    return createPolicyStatistics({
      totalEvaluations: this._totalEvaluations,
      allowedEvaluations: this._allowedEvaluations,
      deniedEvaluations: this._deniedEvaluations,
      averageEvaluationMs: Math.round(avgMs * 100) / 100,
    });
  }

  public health(): PolicyHealth {
    const allowedRate =
      this._totalEvaluations > 0
        ? Math.round((this._allowedEvaluations / this._totalEvaluations) * 100)
        : 100;
    const healthy = true;

    return createPolicyHealth({
      healthy,
      allowedRate,
      activePolicies: Array.from(this._policies.values()).filter((p) => p.enabled).length,
      message: 'Policy manager is operational.',
    });
  }

  public diagnostics(): PolicyDiagnostics {
    return createPolicyDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      policyCount: this._policies.size,
    });
  }

  public clear(): void {
    this._policies.clear();
    this._totalEvaluations = 0;
    this._allowedEvaluations = 0;
    this._deniedEvaluations = 0;
    this._evaluationTimes.length = 0;
  }

  private recordTiming(durationMs: number): void {
    this._evaluationTimes.push(durationMs);
    if (this._evaluationTimes.length > 1000) {
      this._executionTimesShift();
    }
  }

  private _executionTimesShift(): void {
    this._evaluationTimes.shift();
  }
}
