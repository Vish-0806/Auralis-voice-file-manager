import { DiagnosticStatusValue, DiagnosticSeverityValue } from './diagnostic';
import { DiagnosticResult } from './result';
import { DiagnosticsStatistics } from './statistics';

export interface DiagnosticReport {
  readonly reportId: string;
  readonly generatedAt: number;
  readonly runtimeState: string;
  readonly overallStatus: DiagnosticStatusValue;
  readonly overallSeverity: DiagnosticSeverityValue;
  readonly sourceCount: number;
  readonly checkCount: number;
  readonly passedCount: number;
  readonly degradedCount: number;
  readonly failedCount: number;
  readonly skippedCount: number;
  readonly results: ReadonlyArray<DiagnosticResult>;
  readonly summary: string;
  readonly statistics: DiagnosticsStatistics;
}
