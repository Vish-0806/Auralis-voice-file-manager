import { IAlertingRuntime } from '../../alerting/interfaces/alerting-runtime';
import { ICorrelationRuntime } from '../../correlation/interfaces/correlation-runtime';
import { MonitoringResult } from '../../models/monitoring';
import {
  MonitoringAlertPolicy,
  MonitoringAlertIntegrationResult
} from './models';
import {
  MonitoringAlertingDispatchError
} from './errors/MonitoringAlertingErrors';
import { freezeDeepSafe } from '../../models/monitoring';
import { MonitorStatus } from '../../models/health';

export function findMatchingPolicy(
  policies: ReadonlyArray<MonitoringAlertPolicy>,
  result: MonitoringResult
): MonitoringAlertPolicy | null {
  const enabled = policies.filter(p => p.enabled);

  const matches = enabled.map(p => {
    let score = 0;
    
    // 1. Check-specific match
    if (p.checkId && p.checkId === result.checkId && p.componentId === result.componentId) {
      score = 4;
    }
    // 2. Component-specific match
    else if (p.componentId && p.componentId === result.componentId && !p.checkId) {
      score = 3;
    }
    // 3. Source-specific match
    else if (p.source && (result.details as any)?.source === p.source && !p.componentId && !p.checkId) {
      score = 2;
    }
    // 4. Global match
    else if (!p.componentId && !p.checkId && !p.source) {
      score = 1;
    }

    return { policy: p, score };
  }).filter(m => m.score > 0);

  if (matches.length === 0) {
    return null;
  }

  // Sort by specificity score descending, then by policy ID for determinism
  matches.sort((a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }
    return a.policy.id.localeCompare(b.policy.id);
  });

  return matches[0].policy;
}

export class MonitoringAlertingAdapter {
  public static async adapt(options: {
    result: MonitoringResult;
    policies: ReadonlyArray<MonitoringAlertPolicy>;
    alertingRuntime: IAlertingRuntime;
    correlationRuntime: ICorrelationRuntime;
  }): Promise<MonitoringAlertIntegrationResult> {
    const { result, policies, alertingRuntime, correlationRuntime } = options;
    const timestamp = Date.now();

    // 1. Policy matching
    const policy = findMatchingPolicy(policies, result);
    if (!policy) {
      return freezeDeepSafe({
        occurred: false,
        skipped: true,
        reason: 'No matching policy found.',
        timestamp
      }) as MonitoringAlertIntegrationResult;
    }

    // 2. Trigger semantics
    // Default: HEALTHY should not trigger an alert unless recovery is evaluated
    // If status is HEALTHY, it will be orchestrated to rules to see if it resolves active alerts (recovery)
    const isHealthy = result.status === MonitorStatus.HEALTHY;

    // Skip trigger if policy has custom triggers disabled or not matching severity
    if (policy.severity && policy.severity !== result.status) {
      // If we are recovering (HEALTHY), we still evaluate to allow the alert to resolve!
      if (!isHealthy) {
        return freezeDeepSafe({
          occurred: false,
          skipped: true,
          reason: `Policy severity (${policy.severity}) does not match result status (${result.status}).`,
          timestamp
        }) as MonitoringAlertIntegrationResult;
      }
    }

    // If trigger config restricts UNKNOWN but it's UNKNOWN, or restricts HEALTHY
    if (isHealthy && !policy.metadata?.allowHealthyTrigger) {
      // Wait, we still want to evaluate HEALTHY to allow rule NOT_MATCHED to resolve the alert.
      // But if there was no active alert or rule, it might just skip. Let's proceed to allow resolution.
    }

    // 3. Correlation context preservation / generation
    let correlationId = (result.details as any)?.correlationId;
    if (!correlationId) {
      try {
        const ctx = correlationRuntime.createContext({
          source: 'monitoring-alerting-integration'
        });
        correlationId = ctx.correlationId;
      } catch {
        // Fallback if correlation runtime is not ready
      }
    }



    // 5. Delegate request to existing Alerting Runtime
    const orchestrationId = `orch_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    const alertingRequest = {
      orchestrationId,
      ruleId: policy.ruleId,
      context: {
        values: {
          componentId: result.componentId,
          checkId: result.checkId || '',
          status: result.status,
          message: result.message || '',
          durationMs: result.durationMs,
          timestamp: result.completedAt
        }
      },
      correlationId
    };

    try {
      const alertingResult = await alertingRuntime.orchestrate(alertingRequest);

      return freezeDeepSafe({
        occurred: true,
        skipped: false,
        alertingResult,
        correlationId,
        timestamp
      }) as MonitoringAlertIntegrationResult;
    } catch (err: any) {
      throw new MonitoringAlertingDispatchError(
        `Failed to delegate to alerting runtime: ${err.message}`
      );
    }
  }
}
