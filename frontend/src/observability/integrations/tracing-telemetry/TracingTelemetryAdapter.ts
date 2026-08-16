import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import { Span } from '../../tracing/models/span';
import {
  TracingTelemetryPolicy,
  TracingTelemetryResult
} from './models';
import {
  TracingTelemetryDispatchError
} from './errors/TracingTelemetryErrors';
import {
  buildTrigger,
  buildRequest
} from './factories/tracingTelemetryFactories';
import { freezeDeepSafe } from '../../models/monitoring';
import { TelemetryRecord } from '../../telemetry/models/telemetry';

export class TracingTelemetryAdapter {
  public static async adapt(options: {
    span: Span;
    policy: TracingTelemetryPolicy;
    telemetryRuntime: ITelemetryRuntime;
  }): Promise<TracingTelemetryResult> {
    const { span, policy, telemetryRuntime } = options;
    const timestamp = Date.now();
    const startTime = performance.now();

    // 1. Duration filter
    const duration = span.duration ?? (span.endTime ? span.endTime - span.startTime : 0);
    if (policy.minDuration !== undefined && duration < policy.minDuration) {
      return freezeDeepSafe({
        status: 'SKIPPED',
        reason: `Span duration (${duration}ms) is below policy minimum (${policy.minDuration}ms).`,
        duration: performance.now() - startTime,
        timestamp
      }) as TracingTelemetryResult;
    }

    // 2. Status filter
    if (policy.statusFilter && policy.statusFilter.length > 0) {
      if (!policy.statusFilter.includes(span.status)) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Span status (${span.status}) does not match policy status filter.`,
          duration: performance.now() - startTime,
          timestamp
        }) as TracingTelemetryResult;
      }
    }

    // 3. Span kind filter
    if (policy.spanKind && policy.spanKind !== span.kind) {
      return freezeDeepSafe({
        status: 'SKIPPED',
        reason: `Span kind (${span.kind}) does not match policy kind (${policy.spanKind}).`,
        duration: performance.now() - startTime,
        timestamp
      }) as TracingTelemetryResult;
    }

    // 4. Trace name match
    if (policy.traceName && policy.traceName !== '*') {
      const traceName = (span.attributes as any)?.traceName;
      if (traceName && traceName !== policy.traceName) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Trace name (${traceName}) does not match policy selector (${policy.traceName}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as TracingTelemetryResult;
      }
    }

    // 5. Span name match
    if (policy.spanName && policy.spanName !== '*') {
      if (policy.spanName !== span.name) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Span name (${span.name}) does not match policy selector (${policy.spanName}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as TracingTelemetryResult;
      }
    }

    // 6. Sampling check
    const isError = span.status === 'ERROR';
    const bypassSampling = isError && policy.bypassSamplingOnError;
    if (!bypassSampling && policy.samplingRate !== undefined && policy.samplingRate < 1.0) {
      if (Math.random() > policy.samplingRate) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Span integration was sampled out (sampling rate: ${policy.samplingRate}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as TracingTelemetryResult;
      }
    }

    // 7. Status/Severity mapping
    let severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL' = 'INFO';
    if (isError) {
      severity = (policy.metadata?.errorSeverity as any) ?? 'ERROR';
    } else {
      severity = (policy.metadata?.defaultSeverity as any) ?? 'INFO';
    }

    // 8. Trigger creation
    const trigger = buildTrigger(span);

    // Combine static policy attributes with dynamic span attributes
    const attributesToSend: Record<string, unknown> = {
      ...trigger.attributes,
      ...(policy.staticAttributes ?? {}),
      events: trigger.events
    };

    // 9. Build Request
    const request = buildRequest({
      telemetryType: policy.telemetryType,
      traceId: span.traceId,
      spanId: span.spanId,
      correlationId: trigger.correlationId,
      requestId: trigger.requestId,
      name: span.name,
      duration,
      severity,
      attributes: attributesToSend,
      metadata: policy.metadata,
      source: 'tracing-telemetry-integration'
    });

    try {
      // 10. Record via telemetry runtime
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
        spanId: request.spanId,
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
      }) as TracingTelemetryResult;
    } catch (err: any) {
      throw new TracingTelemetryDispatchError(
        `Failed to submit telemetry observation: ${err.message}`
      );
    }
  }
}
