import { MonitoringAlertIntegrationStatistics } from './statistics';

export interface MonitoringAlertIntegrationDiagnostics {
  readonly lifecycleState: string;
  readonly policyCount: number;
  readonly statistics: MonitoringAlertIntegrationStatistics;
  readonly recentFailures: ReadonlyArray<{
    readonly timestamp: number;
    readonly error: { name: string; message: string; stack?: string };
  }>;
  readonly health: string;
  readonly generatedAt: number;
}
