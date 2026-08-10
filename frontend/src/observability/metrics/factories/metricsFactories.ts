import type { MetricTypeValue } from '../models/metric';
import type { MetricSample } from '../models/sample';
import { MetricsValidationError } from '../errors/MetricsErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export function validateMetricName(name: string): void {
  if (!name || !name.trim()) {
    throw new MetricsValidationError('Metric name cannot be empty or whitespace only.');
  }
  const trimmed = name.trim();
  if (trimmed.length > 255) {
    throw new MetricsValidationError('Metric name exceeds maximum allowed length of 255 characters.');
  }
  const nameRegex = /^[a-zA-Z0-9_\-\.]+$/;
  if (!nameRegex.test(trimmed)) {
    throw new MetricsValidationError(`Metric name '${trimmed}' contains invalid characters. Only alphanumeric, dots, hyphens, and underscores are allowed.`);
  }
}

export function normalizeLabels(
  labels?: Record<string, string>,
  schemaKeys?: ReadonlyArray<string>
): Record<string, string> {
  const normalized: Record<string, string> = {};
  if (!labels) {
    if (schemaKeys && schemaKeys.length > 0) {
      throw new MetricsValidationError(`Missing required labels. Expected keys: ${schemaKeys.join(', ')}`);
    }
    return normalized;
  }

  const inputKeys = Object.keys(labels);
  if (schemaKeys) {
    for (const reqKey of schemaKeys) {
      if (!inputKeys.includes(reqKey)) {
        throw new MetricsValidationError(`Missing required label key: '${reqKey}'`);
      }
    }
    for (const key of inputKeys) {
      if (!schemaKeys.includes(key)) {
        throw new MetricsValidationError(`Label key '${key}' is not defined in the metric schema.`);
      }
    }
  }

  const sortedKeys = Object.keys(labels).sort();
  for (const key of sortedKeys) {
    if (!key || !key.trim()) {
      throw new MetricsValidationError('Label key cannot be empty or whitespace only.');
    }
    const val = labels[key];
    if (val === undefined || val === null) {
      throw new MetricsValidationError(`Value for label key '${key}' cannot be null or undefined.`);
    }
    normalized[key] = String(val).trim();
  }

  return normalized;
}

export function getSeriesKey(normalizedLabels: Record<string, string>): string {
  const pairs = Object.entries(normalizedLabels)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`);
  return pairs.join(',');
}

let sampleIdCounter = 0;
export function createMetricSample(input: {
  metricName: string;
  metricType: MetricTypeValue;
  value: number;
  labels?: Record<string, string>;
  seriesKey?: string;
  unit?: string;
  operation?: string;
  durationMs?: number;
}): MetricSample {
  sampleIdCounter += 1;
  const sample: MetricSample = {
    id: `sample_${Date.now()}_${sampleIdCounter}_${Math.random().toString(36).substring(2, 7)}`,
    timestamp: Date.now(),
    metricName: input.metricName,
    metricType: input.metricType,
    value: input.value,
    labels: input.labels ? { ...input.labels } : undefined,
    seriesKey: input.seriesKey,
    unit: input.unit,
    operation: input.operation,
    durationMs: input.durationMs
  };
  return freezeDeepSafe(sample) as MetricSample;
}
