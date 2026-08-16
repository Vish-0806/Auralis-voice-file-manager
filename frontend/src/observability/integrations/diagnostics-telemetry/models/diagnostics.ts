import { DiagnosticsTelemetryStatistics } from './statistics';

export interface DiagnosticsTelemetryDiagnostics {
  readonly runtimeState: string;
  readonly registeredPolicyCount: number;
  readonly statistics: DiagnosticsTelemetryStatistics;
  readonly health: string;
  readonly recentFailures: ReadonlyArray<{
    readonly timestamp: number;
    readonly error: { name: string; message: string; stack?: string };
  }>;
  readonly historyCapacity: number;
  readonly generatedAt: number;
}
