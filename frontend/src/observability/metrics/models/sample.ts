import type { MetricTypeValue } from './metric';

export interface MetricSample {
  readonly id: string;
  readonly metricName: string;
  readonly metricType: MetricTypeValue;
  readonly timestamp: number;
  readonly value: number;
  readonly labels?: Record<string, string>;
  readonly seriesKey?: string;
  readonly unit?: string;
  readonly operation?: string;
  readonly durationMs?: number;
}
