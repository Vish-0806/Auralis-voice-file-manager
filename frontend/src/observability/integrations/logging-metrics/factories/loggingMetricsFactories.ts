import { freezeDeepSafe } from '../../../models/monitoring';
import { LogRecord } from '../../../logging/models/log';
import { LoggingMetricTrigger, LoggingMetricRequest } from '../models';

const SENSITIVE_KEYS = new Set([
  'password',
  'token',
  'secret',
  'authorization',
  'cookie',
  'api_key',
  'credential'
]);

export function normalizeLabels(labels?: Record<string, string>): Record<string, string> {
  const result: Record<string, string> = {};
  if (!labels) {
    return Object.freeze(result);
  }

  const sortedKeys = Object.keys(labels).sort();
  for (const key of sortedKeys) {
    const lowerKey = key.toLowerCase();
    
    let isSensitive = false;
    for (const sens of SENSITIVE_KEYS) {
      if (lowerKey.includes(sens)) {
        isSensitive = true;
        break;
      }
    }

    if (!isSensitive) {
      result[key] = String(labels[key]);
    }
  }

  return Object.freeze(result);
}

export function createTriggerId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return 'trig_lm_' + crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(36).substring(2, 10);
  return `trig_lm_${Date.now()}_${rand}`;
}

export function buildTrigger(
  record: LogRecord,
  normalizedLabels: Record<string, string>
): LoggingMetricTrigger {
  const trigger: LoggingMetricTrigger = {
    triggerId: createTriggerId(),
    timestamp: record.timestamp || Date.now(),
    loggerName: record.loggerName,
    logLevel: record.level,
    correlationId: record.correlationId,
    requestId: record.requestId,
    message: record.message,
    metadata: record.metadata ? { ...record.metadata } : undefined,
    labels: normalizedLabels
  };

  return freezeDeepSafe(trigger) as LoggingMetricTrigger;
}

export function buildRequest(options: {
  metricName: string;
  metricType: string;
  value: number;
  labels: Record<string, string>;
  sourceLogger: string;
  correlationId?: string;
  requestId?: string;
}): LoggingMetricRequest {
  const request: LoggingMetricRequest = {
    metricName: options.metricName,
    metricType: options.metricType as any,
    value: options.value,
    labels: options.labels,
    sourceLogger: options.sourceLogger,
    correlationId: options.correlationId,
    requestId: options.requestId
  };

  return freezeDeepSafe(request) as LoggingMetricRequest;
}
