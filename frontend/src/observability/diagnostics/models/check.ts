import { DiagnosticCategoryValue, DiagnosticSeverityValue, DiagnosticStatusValue } from './diagnostic';

export type DiagnosticCheckCallback = () => void | Promise<void> | DiagnosticStatusValue | Promise<DiagnosticStatusValue>;

export interface DiagnosticCheck {
  readonly id: string;
  readonly sourceId: string;
  readonly name: string;
  readonly description: string;
  readonly category: DiagnosticCategoryValue;
  readonly severity: DiagnosticSeverityValue;
  readonly enabled: boolean;
  readonly timeout?: number; // timeout in milliseconds
  readonly priority: number;
  readonly execute: DiagnosticCheckCallback;
}
