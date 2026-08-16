import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import {
  DiagnosticsTelemetryPolicy,
  DiagnosticsTelemetryResult,
  DiagnosticsTelemetryTrigger
} from './models';
import {
  DiagnosticsTelemetryDispatchError
} from './errors/DiagnosticsTelemetryErrors';
import { buildRequest } from './factories/diagnosticsTelemetryFactories';
import { freezeDeepSafe } from '../../models/monitoring';
import { TelemetryRecord } from '../../telemetry/models/telemetry';

export class DiagnosticsTelemetryAdapter {
  public static async adapt(options: {
    trigger: DiagnosticsTelemetryTrigger;
    policy: DiagnosticsTelemetryPolicy;
    telemetryRuntime: ITelemetryRuntime;
  }): Promise<DiagnosticsTelemetryResult> {
    const { trigger, policy, telemetryRuntime } = options;
    const timestamp = Date.now();
    const startTime = performance.now();

    // 1. Duration filter if applicable
    const duration = trigger.duration ?? 0;
    if (policy.minDuration !== undefined && duration < policy.minDuration) {
      return freezeDeepSafe({
        status: 'SKIPPED',
        reason: `Diagnostic duration (${duration}ms) is below policy minimum (${policy.minDuration}ms).`,
        duration: performance.now() - startTime,
        timestamp
      }) as DiagnosticsTelemetryResult;
    }

    // 2. Sampling check
    const isError = trigger.diagnosticSeverity === 'CRITICAL' || trigger.diagnosticSeverity === 'ERROR';
    const bypassSampling = isError && policy.bypassSamplingOnError;
    if (!bypassSampling && policy.samplingRate !== undefined && policy.samplingRate < 1.0) {
      if (Math.random() > policy.samplingRate) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Diagnostic integration was sampled out (sampling rate: ${policy.samplingRate}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as DiagnosticsTelemetryResult;
      }
    }

    // 3. Severity mapping
    let severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL' = 'INFO';
    if (trigger.diagnosticSeverity === 'CRITICAL') {
      severity = 'FATAL';
    } else if (trigger.diagnosticSeverity === 'ERROR') {
      severity = 'ERROR';
    } else if (trigger.diagnosticSeverity === 'WARNING') {
      severity = 'WARN';
    } else {
      severity = 'INFO';
    }

    // Combine static policy attributes with dynamic diagnostic attributes
    const attributesToSend: Record<string, unknown> = {
      ...trigger.metadata,
      ...(policy.staticAttributes ?? {}),
      duration,
      message: trigger.message,
      diagnosticStatus: trigger.diagnosticStatus,
      diagnosticSeverity: trigger.diagnosticSeverity,
      sourceId: trigger.sourceId,
      level: policy.level
    };

    if (trigger.error) {
      attributesToSend.error = trigger.error;
    }

    // 4. Build Request
    const request = buildRequest({
      telemetryType: policy.telemetryType,
      diagnosticRunId: trigger.diagnosticRunId,
      resultId: trigger.resultId,
      sourceId: trigger.sourceId,
      checkId: trigger.checkId,
      correlationId: trigger.correlationId,
      requestId: trigger.requestId,
      operationId: trigger.operationId,
      traceId: trigger.traceId,
      name: trigger.sourceName + (trigger.checkName ? ` - ${trigger.checkName}` : ''),
      severity,
      status: trigger.diagnosticStatus,
      attributes: attributesToSend,
      metadata: policy.metadata,
      source: 'diagnostics-telemetry-integration'
    });

    try {
      // 5. Record via telemetry runtime
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
        spanId: request.resultId,
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
      }) as DiagnosticsTelemetryResult;
    } catch (err: any) {
      throw new DiagnosticsTelemetryDispatchError(
        `Failed to submit telemetry observation: ${err.message}`
      );
    }
  }
}
