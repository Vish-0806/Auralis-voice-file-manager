import { LogLevelValue } from '../../../logging/models/log';
import { MetricTypeValue } from '../../../metrics/models/metric';

export interface LoggingMetricsPolicy {
  readonly id: string;
  readonly enabled: boolean;
  readonly loggerName: string;
  readonly minLevel: LogLevelValue;
  readonly metricName: string;
  readonly metricType: MetricTypeValue;
  readonly labels?: Record<string, string>;
  readonly alwaysCountErrors?: boolean;
  readonly samplingRate?: number;
  readonly priority: number;
  readonly metadata?: Record<string, unknown>;
}
