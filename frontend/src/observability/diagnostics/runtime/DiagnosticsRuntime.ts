import { IDiagnosticsRuntime } from '../interfaces/diagnostics-runtime';
import { IDiagnosticsProvider } from '../interfaces/diagnostics-provider';
import { IDiagnosticsSource } from '../interfaces/diagnostics-source';
import { DiagnosticCheck, DiagnosticCheckCallback } from '../models/check';
import { DiagnosticResult } from '../models/result';
import { DiagnosticReport } from '../models/report';
import { DiagnosticsStatistics } from '../models/statistics';
import { DiagnosticSeverityValue, DiagnosticCategoryValue } from '../models/diagnostic';
import { DiagnosticsProvider } from '../provider/DiagnosticsProvider';

export class DiagnosticsRuntime implements IDiagnosticsRuntime {
  private readonly _provider: IDiagnosticsProvider;

  constructor(provider?: IDiagnosticsProvider) {
    this._provider = provider || new DiagnosticsProvider();
  }

  public provider(): IDiagnosticsProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public registerSource(source: IDiagnosticsSource): void {
    this._provider.registerSource(source);
  }

  public unregisterSource(sourceId: string): void {
    this._provider.unregisterSource(sourceId);
  }

  public getSource(sourceId: string): IDiagnosticsSource | null {
    return this._provider.getSource(sourceId);
  }

  public hasSource(sourceId: string): boolean {
    return this._provider.hasSource(sourceId);
  }

  public listSources(): ReadonlyArray<IDiagnosticsSource> {
    return this._provider.listSources();
  }

  public registerCheck(check: {
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
  }): DiagnosticCheck {
    return this._provider.registerCheck(check);
  }

  public unregisterCheck(checkId: string): void {
    this._provider.unregisterCheck(checkId);
  }

  public getCheck(checkId: string): DiagnosticCheck | null {
    return this._provider.getCheck(checkId);
  }

  public listChecks(): ReadonlyArray<DiagnosticCheck> {
    return this._provider.listChecks();
  }

  public getChecksForSource(sourceId: string): ReadonlyArray<DiagnosticCheck> {
    return this._provider.getChecksForSource(sourceId);
  }

  public run(): Promise<DiagnosticReport> {
    return this._provider.run();
  }

  public runSource(sourceId: string): Promise<DiagnosticReport> {
    return this._provider.runSource(sourceId);
  }

  public runCheck(checkId: string): Promise<DiagnosticResult> {
    return this._provider.runCheck(checkId);
  }

  public getHistory(): ReadonlyArray<DiagnosticReport> {
    return this._provider.getHistory();
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }

  public getStatistics(): DiagnosticsStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics() {
    return this._provider.getDiagnostics();
  }
}
