import { AlertingTelemetryStatistics } from './statistics';

export interface AlertingTelemetryDiagnostics {
  readonly runtimeState: string;
  readonly policyCount: number;
  readonly statistics: AlertingTelemetryStatistics;
  readonly idempotencyCacheSize: number;
  readonly inFlightRequestCount: number;
  readonly lastIntegrationTimestamp?: number;
  readonly recentFailures: ReadonlyArray<{
    readonly timestamp: number;
    readonly error: { name: string; message: string; stack?: string };
  }>;
  readonly health: string;
  readonly generatedAt: number;
}
