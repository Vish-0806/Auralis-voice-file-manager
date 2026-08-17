import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import {
  AlertingTelemetryPolicy,
  AlertingTelemetryResult,
  AlertingTelemetryTrigger
} from './models';
import {
  AlertingTelemetryDispatchError
} from './errors/AlertingTelemetryErrors';
import { buildRequest } from './factories/alertingTelemetryFactories';
import { freezeDeepSafe } from '../../models/monitoring';
import { TelemetryRecord } from '../../telemetry/models/telemetry';

export function policyMatchesTrigger(policy: AlertingTelemetryPolicy, trigger: AlertingTelemetryTrigger): boolean {
  if (!policy.enabled) return false;

  if (policy.alertId !== undefined && policy.alertId !== '*' && policy.alertId !== trigger.alertId) {
    return false;
  }
  if (policy.fingerprint !== undefined && policy.fingerprint !== '*' && policy.fingerprint !== trigger.fingerprint) {
    return false;
  }
  if (policy.ruleId !== undefined && policy.ruleId !== '*' && policy.ruleId !== trigger.ruleId) {
    return false;
  }
  if (policy.sourceId !== undefined && policy.sourceId !== '*' && policy.sourceId !== trigger.sourceId) {
    return false;
  }
  if (policy.lifecycleState !== undefined && (policy.lifecycleState as string) !== '*' && policy.lifecycleState !== trigger.lifecycleState) {
    return false;
  }
  if (policy.severity !== undefined && (policy.severity as string) !== '*' && policy.severity !== trigger.severity) {
    return false;
  }
  if (policy.status !== undefined && policy.status !== '*' && policy.status !== trigger.status) {
    return false;
  }
  if (policy.orchestrationStatus !== undefined && policy.orchestrationStatus !== '*' && policy.orchestrationStatus !== trigger.orchestrationStatus) {
    return false;
  }
  if (policy.notificationStatus !== undefined && policy.notificationStatus !== '*' && policy.notificationStatus !== trigger.notificationStatus) {
    return false;
  }

  return true;
}

export function findMatchingPolicy(
  policies: ReadonlyArray<AlertingTelemetryPolicy>,
  trigger: AlertingTelemetryTrigger
): AlertingTelemetryPolicy | null {
  const matched = policies.filter(p => policyMatchesTrigger(p, trigger));
  if (matched.length === 0) return null;
  return matched[0];
}

export class AlertingTelemetryAdapter {
  public static async adapt(options: {
    trigger: AlertingTelemetryTrigger;
    policy: AlertingTelemetryPolicy;
    telemetryRuntime: ITelemetryRuntime;
  }): Promise<AlertingTelemetryResult> {
    const { trigger, policy, telemetryRuntime } = options;
    const timestamp = Date.now();
    const startTime = performance.now();

    // 1. Sampling check
    const isError = trigger.severity === 'CRITICAL' || trigger.severity === 'ERROR';
    const bypassSampling = isError && policy.bypassSamplingOnError;
    if (!bypassSampling && policy.samplingRate !== undefined && policy.samplingRate < 1.0) {
      if (Math.random() > policy.samplingRate) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Alerting telemetry integration was sampled out (sampling rate: ${policy.samplingRate}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as AlertingTelemetryResult;
      }
    }

    // 2. Severity mapping
    let severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL' = 'INFO';
    if (trigger.severity === 'CRITICAL') {
      severity = 'FATAL';
    } else if (trigger.severity === 'ERROR') {
      severity = 'ERROR';
    } else if (trigger.severity === 'WARNING') {
      severity = 'WARN';
    } else {
      severity = 'INFO';
    }

    // Combine static policy attributes with dynamic trigger attributes
    const attributesToSend: Record<string, unknown> = {
      ...(trigger.metadata ?? {}),
      ...(policy.staticAttributes ?? {}),
      kind: trigger.kind,
      alertId: trigger.alertId,
      fingerprint: trigger.fingerprint,
      ruleId: trigger.ruleId,
      sourceId: trigger.sourceId,
      lifecycleState: trigger.lifecycleState,
      alertSeverity: trigger.severity,
      status: trigger.status,
      orchestrationStatus: trigger.orchestrationStatus,
      notificationStatus: trigger.notificationStatus,
    };

    if (trigger.payload !== undefined) {
      attributesToSend.payload = trigger.payload;
    }

    // 3. Build Request
    const request = buildRequest({
      telemetryType: policy.telemetryType,
      alertId: trigger.alertId,
      fingerprint: trigger.fingerprint,
      ruleId: trigger.ruleId,
      sourceId: trigger.sourceId,
      correlationId: trigger.correlationId,
      requestId: trigger.requestId,
      operationId: trigger.operationId,
      traceId: trigger.traceId,
      name: `Alerting Event: ${trigger.kind} - ${trigger.alertId || trigger.ruleId || 'global'}`,
      severity,
      attributes: attributesToSend,
      metadata: policy.metadata,
      source: 'alerting-telemetry-integration',
      policy
    });

    try {
      // 4. Record via telemetry runtime
      const record: TelemetryRecord = {
        id: request.recordId,
        timestamp: request.timestamp,
        type: request.telemetryType,
        source: request.source,
        name: request.name,
        severity: request.severity,
        attributes: request.attributes,
        metadata: request.metadata,
        traceId: request.traceId,
        spanId: request.fingerprint,
        correlationId: request.correlationId,
        requestId: request.requestId
      };

      telemetryRuntime.record(record);

      return freezeDeepSafe({
        status: 'ACCEPTED',
        triggerId: trigger.triggerId,
        recordId: request.recordId,
        telemetryType: policy.telemetryType,
        duration: performance.now() - startTime,
        timestamp
      }) as AlertingTelemetryResult;
    } catch (err: any) {
      throw new AlertingTelemetryDispatchError(
        `Failed to submit telemetry observation: ${err.message}`
      );
    }
  }
}
