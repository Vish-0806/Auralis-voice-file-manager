import { LoggingMetricsStatistics } from './statistics';
import { LoggingMetricsPolicy } from './policy';

export interface LoggingMetricsDiagnostics {
  readonly runtimeState: string;
  readonly registeredPolicies: ReadonlyArray<LoggingMetricsPolicy>;
  readonly statistics: LoggingMetricsStatistics;
  readonly health: string;
  readonly recentFailures: ReadonlyArray<{
    readonly timestamp: number;
    readonly error: { name: string; message: string; stack?: string };
  }>;
  readonly generatedAt: number;
}
