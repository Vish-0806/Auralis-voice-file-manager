import { DiagnosticSeverityValue, DiagnosticStatusValue, DiagnosticCategoryValue } from '../../../diagnostics/models/diagnostic';
import { NormalizedErrorInfo } from '../../../diagnostics/models/result';

export interface DiagnosticsTelemetryTrigger {
  readonly triggerId: string;
  readonly diagnosticRunId: string;
  readonly resultId?: string;
  readonly sourceId: string;
  readonly checkId?: string;
  readonly timestamp: number;
  readonly startedAt?: number;
  readonly completedAt?: number;
  readonly duration?: number;
  readonly sourceName: string;
  readonly checkName?: string;
  readonly diagnosticCategory?: DiagnosticCategoryValue;
  readonly diagnosticSeverity: DiagnosticSeverityValue;
  readonly diagnosticStatus: DiagnosticStatusValue;
  readonly message: string;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly operationId?: string;
  readonly traceId?: string;
  readonly metadata: Record<string, unknown>;
  readonly error?: NormalizedErrorInfo;
}
