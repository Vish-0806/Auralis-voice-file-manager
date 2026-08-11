import { IDiagnosticsSource } from './diagnostics-source';
import { DiagnosticCheck, DiagnosticCheckCallback } from '../models/check';
import { DiagnosticResult } from '../models/result';
import { DiagnosticReport } from '../models/report';
import { DiagnosticsStatistics } from '../models/statistics';
import { DiagnosticSeverityValue, DiagnosticCategoryValue } from '../models/diagnostic';

export interface IDiagnosticsProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  registerSource(source: IDiagnosticsSource): void;
  unregisterSource(sourceId: string): void;
  getSource(sourceId: string): IDiagnosticsSource | null;
  hasSource(sourceId: string): boolean;
  listSources(): ReadonlyArray<IDiagnosticsSource>;

  registerCheck(check: {
    id: string;
    sourceId: string;
    name: string;
    description: string;
    category: DiagnosticCategoryValue;
    severity: DiagnosticSeverityValue;
    enabled?: boolean;
    timeout?: number;
    priority?: number;
    execute: DiagnosticCheckCallback;
  }): DiagnosticCheck;
  unregisterCheck(checkId: string): void;
  getCheck(checkId: string): DiagnosticCheck | null;
  listChecks(): ReadonlyArray<DiagnosticCheck>;
  getChecksForSource(sourceId: string): ReadonlyArray<DiagnosticCheck>;

  run(): Promise<DiagnosticReport>;
  runSource(sourceId: string): Promise<DiagnosticReport>;
  runCheck(checkId: string): Promise<DiagnosticResult>;

  getHistory(): ReadonlyArray<DiagnosticReport>;
  clearHistory(): void;

  getStatistics(): DiagnosticsStatistics;
  getDiagnostics(): {
    readonly runtimeState: string;
    readonly sourceCount: number;
    readonly enabledSourceCount: number;
    readonly checkCount: number;
    readonly enabledCheckCount: number;
    readonly historySize: number;
    readonly statistics: DiagnosticsStatistics;
    readonly generatedAt: number;
  };
}
