import { IMetricsRuntime } from '../../metrics/interfaces/metrics-runtime';
import { LogRecord } from '../../logging/models/log';
import {
  LoggingMetricsPolicy,
  LoggingMetricResult
} from './models';
import {
  LoggingMetricsDispatchError
} from './errors/LoggingMetricsErrors';
import {
  normalizeLabels,
  buildTrigger,
  buildRequest
} from './factories/loggingMetricsFactories';
import { freezeDeepSafe } from '../../models/monitoring';
import { LogLevelSeverity } from '../../logging/models/log';

export class LoggingMetricsAdapter {
  public static async adapt(options: {
    record: LogRecord;
    policy: LoggingMetricsPolicy;
    metricsRuntime: IMetricsRuntime;
  }): Promise<LoggingMetricResult> {
    const { record, policy, metricsRuntime } = options;
    const timestamp = Date.now();
    const startTime = performance.now();

    // 1. Validate policy severity threshold match
    const recordSeverity = LogLevelSeverity[record.level];
    const minSeverity = LogLevelSeverity[policy.minLevel];

    if (recordSeverity < minSeverity) {
      return freezeDeepSafe({
        status: 'SKIPPED',
        reason: `Log level (${record.level}) is below policy threshold (${policy.minLevel}).`,
        duration: performance.now() - startTime,
        timestamp
      }) as LoggingMetricResult;
    }

    // Sampling configuration check
    if (policy.samplingRate !== undefined && policy.samplingRate < 1.0) {
      if (Math.random() > policy.samplingRate) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Log event was sampled out (sampling rate: ${policy.samplingRate}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as LoggingMetricResult;
      }
    }

    // Logger matching pattern (wildcard * or exact match)
    if (policy.loggerName && policy.loggerName !== '*') {
      if (policy.loggerName !== record.loggerName) {
        return freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Logger name (${record.loggerName}) does not match policy selector (${policy.loggerName}).`,
          duration: performance.now() - startTime,
          timestamp
        }) as LoggingMetricResult;
      }
    }

    // 2. Normalize labels
    const labelsToSend: Record<string, string> = {};
    if (policy.labels) {
      for (const [k, v] of Object.entries(policy.labels)) {
        labelsToSend[k] = v;
      }
    }

    labelsToSend['logger'] = record.loggerName;
    labelsToSend['level'] = record.level;
    if (record.componentId) {
      labelsToSend['source'] = record.componentId;
    }
    if (record.correlationId) {
      labelsToSend['correlationId'] = record.correlationId;
    }
    if (record.requestId) {
      labelsToSend['requestId'] = record.requestId;
    }

    const finalLabels = normalizeLabels(labelsToSend);

    // 3. Build trigger
    const trigger = buildTrigger(record, finalLabels);

    // 4. Extract value from LogRecord
    let value = 1;
    if (policy.metadata?.valueField) {
      const field = String(policy.metadata.valueField);
      if (field === 'durationMs' && record.durationMs !== undefined) {
        value = record.durationMs;
      } else if (record.context && record.context[field] !== undefined) {
        value = Number(record.context[field]);
      } else if (record.metadata && record.metadata[field] !== undefined) {
        value = Number(record.metadata[field]);
      }
    }

    if (isNaN(value)) {
      value = 1;
    }

    // 5. Normalise metrics request
    buildRequest({
      metricName: policy.metricName,
      metricType: policy.metricType,
      value,
      labels: finalLabels,
      sourceLogger: record.loggerName,
      correlationId: record.correlationId,
      requestId: record.requestId
    });

    try {
      // 6. Metrics Auto-Registration and Delegation
      let instrument: any;
      try {
        instrument = metricsRuntime.getMetric(policy.metricName);
      } catch {
        const labelKeys = Object.keys(finalLabels).sort();
        const definition = {
          name: policy.metricName,
          description: `Auto-registered metric for logging policy ${policy.id}`,
          labelKeys
        };

        if (policy.metricType === 'COUNTER') {
          instrument = metricsRuntime.registerCounter(definition);
        } else if (policy.metricType === 'GAUGE') {
          instrument = metricsRuntime.registerGauge(definition);
        } else if (policy.metricType === 'HISTOGRAM') {
          instrument = metricsRuntime.registerHistogram(definition);
        } else if (policy.metricType === 'TIMER') {
          instrument = metricsRuntime.registerTimer(definition);
        } else {
          throw new LoggingMetricsDispatchError(`Unsupported metric type: ${policy.metricType}`);
        }
      }

      // Record observation
      if (policy.metricType === 'COUNTER') {
        instrument.increment(value, finalLabels);
      } else if (policy.metricType === 'GAUGE') {
        instrument.set(value, finalLabels);
      } else if (policy.metricType === 'HISTOGRAM') {
        instrument.observe(value, finalLabels);
      } else if (policy.metricType === 'TIMER') {
        instrument.record(value, finalLabels);
      }

      return freezeDeepSafe({
        status: 'ACCEPTED',
        triggerId: trigger.triggerId,
        metricName: policy.metricName,
        operation: policy.metricType,
        duration: performance.now() - startTime,
        timestamp
      }) as LoggingMetricResult;
    } catch (err: any) {
      throw new LoggingMetricsDispatchError(
        `Failed to delegate metric observation: ${err.message}`
      );
    }
  }
}
