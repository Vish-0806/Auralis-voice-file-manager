import { DiagnosticStatusValue, DiagnosticSeverityValue } from './diagnostic';

export interface NormalizedErrorInfo {
  readonly name: string;
  readonly message: string;
  readonly stack?: string;
}

export interface DiagnosticResult {
  readonly checkId: string;
  readonly sourceId: string;
  readonly status: DiagnosticStatusValue;
  readonly severity: DiagnosticSeverityValue;
  readonly message: string;
  readonly duration: number;
  readonly timestamp: number;
  readonly metadata: Record<string, unknown>;
  readonly error?: NormalizedErrorInfo;
}
