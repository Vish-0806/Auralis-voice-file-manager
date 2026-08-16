import { TracingTelemetryStatistics } from './statistics';

export interface TracingTelemetryDiagnostics {
  readonly runtimeState: string;
  readonly registeredPolicyCount: number;
  readonly statistics: TracingTelemetryStatistics;
  readonly health: string;
  readonly recentFailures: ReadonlyArray<{
    readonly timestamp: number;
    readonly error: { name: string; message: string; stack?: string };
  }>;
  readonly historyCapacity: number;
  readonly generatedAt: number;
}
