import { MetricTypeValue } from '../../../metrics/models/metric';

export interface LoggingMetricRequest {
  readonly metricName: string;
  readonly metricType: MetricTypeValue;
  readonly value: number;
  readonly labels: Record<string, string>;
  readonly sourceLogger: string;
  readonly correlationId?: string;
  readonly requestId?: string;
}
