import { CorrelationStatistics } from './correlation-statistics';

export type CorrelationHealthStatus = 'UNKNOWN' | 'HEALTHY' | 'DEGRADED' | 'UNHEALTHY';

export interface CorrelationDiagnostics {
  readonly runtimeState: string;
  readonly eventCount: number;
  readonly linkCount: number;
  readonly correlationCount: number;
  readonly statistics: CorrelationStatistics;
  readonly configuredCapacity: number;
  readonly generatedAt: number;
  readonly healthStatus: CorrelationHealthStatus;
}
