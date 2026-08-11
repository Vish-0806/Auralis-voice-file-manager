import { IDiagnosticsProvider } from '../interfaces/diagnostics-provider';
import { IDiagnosticsSource } from '../interfaces/diagnostics-source';
import { DiagnosticCheck, DiagnosticCheckCallback } from '../models/check';
import { DiagnosticResult } from '../models/result';
import { DiagnosticReport } from '../models/report';
import { DiagnosticsStatistics } from '../models/statistics';
import {
  DiagnosticStatus,
  DiagnosticStatusValue,
  DiagnosticSeverity,
  DiagnosticSeverityValue,
  DiagnosticCategoryValue,
  DiagnosticsRuntimeState,
  DiagnosticsRuntimeStateValue
} from '../models/diagnostic';
import { DiagnosticsRegistry } from '../registry/DiagnosticsRegistry';
import { DiagnosticsExecutor } from '../executor/DiagnosticsExecutor';
import {
  DiagnosticsStateError,
  DiagnosticSourceNotFoundError,
  DiagnosticCheckNotFoundError
} from '../errors/DiagnosticsErrors';
import {
  createDiagnosticCheck,
  createDiagnosticReport,
  createDiagnosticsStatistics,
  createDiagnosticsSnapshot
} from '../factories/diagnosticsFactories';

export class DiagnosticsProvider implements IDiagnosticsProvider {
  private lifecycleState: DiagnosticsRuntimeStateValue = DiagnosticsRuntimeState.UNINITIALIZED;
  private readonly registry = new DiagnosticsRegistry();
  private readonly executor = new DiagnosticsExecutor();

  // Bounded report history
  private readonly history: DiagnosticReport[] = [];
  private readonly historyCapacity: number;

  // Statistics counters
  private totalRuns = 0;
  private successfulRuns = 0;
  private degradedRuns = 0;
  private failedRuns = 0;
  private skippedChecks = 0;
  private executedChecks = 0;
  private failedChecks = 0;
  private timedOutChecks = 0;
  private totalDuration = 0;

  private activeRunPromise: Promise<DiagnosticReport> | null = null;

  constructor(options?: { historyCapacity?: number }) {
    this.historyCapacity = options?.historyCapacity ?? 50;
  }

  private ensureReady(): void {
    if (this.lifecycleState !== DiagnosticsRuntimeState.READY && this.lifecycleState !== DiagnosticsRuntimeState.RUNNING) {
      throw new DiagnosticsStateError(`Diagnostics provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  private ensureReadyOrRunning(): void {
    if (this.lifecycleState !== DiagnosticsRuntimeState.READY && this.lifecycleState !== DiagnosticsRuntimeState.RUNNING) {
      throw new DiagnosticsStateError(`Diagnostics provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (
      this.lifecycleState === DiagnosticsRuntimeState.READY ||
      this.lifecycleState === DiagnosticsRuntimeState.INITIALIZING ||
      this.lifecycleState === DiagnosticsRuntimeState.RUNNING
    ) {
      return;
    }

    if (
      this.lifecycleState === DiagnosticsRuntimeState.STOPPING ||
      this.lifecycleState === DiagnosticsRuntimeState.STOPPED
    ) {
      throw new DiagnosticsStateError(`Cannot initialize diagnostics provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = DiagnosticsRuntimeState.INITIALIZING;
    try {
      this.lifecycleState = DiagnosticsRuntimeState.READY;
    } catch (err: any) {
      this.lifecycleState = DiagnosticsRuntimeState.ERROR;
      throw new DiagnosticsStateError(`Failed to initialize diagnostics provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === DiagnosticsRuntimeState.STOPPED) {
      return;
    }

    if (this.lifecycleState === DiagnosticsRuntimeState.UNINITIALIZED) {
      throw new DiagnosticsStateError('Cannot shutdown diagnostics provider: it is not initialized.');
    }

    this.lifecycleState = DiagnosticsRuntimeState.STOPPING;
    this.lifecycleState = DiagnosticsRuntimeState.STOPPED;
  }

  public getState(): string {
    return this.lifecycleState;
  }

  public registerSource(source: IDiagnosticsSource): void {
    this.ensureReady();
    this.registry.registerSource(source);
  }

  public unregisterSource(sourceId: string): void {
    this.ensureReady();
    this.registry.unregisterSource(sourceId);
  }

  public getSource(sourceId: string): IDiagnosticsSource | null {
    this.ensureReady();
    return this.registry.getSource(sourceId);
  }

  public hasSource(sourceId: string): boolean {
    this.ensureReady();
    return this.registry.hasSource(sourceId);
  }

  public listSources(): ReadonlyArray<IDiagnosticsSource> {
    this.ensureReady();
    return this.registry.listSources();
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
    this.ensureReady();
    const createdCheck = createDiagnosticCheck(check);
    this.registry.registerCheck(createdCheck);
    return createdCheck;
  }

  public unregisterCheck(checkId: string): void {
    this.ensureReady();
    this.registry.unregisterCheck(checkId);
  }

  public getCheck(checkId: string): DiagnosticCheck | null {
    this.ensureReady();
    return this.registry.getCheck(checkId);
  }

  public listChecks(): ReadonlyArray<DiagnosticCheck> {
    this.ensureReady();
    return this.registry.listChecks();
  }

  public getChecksForSource(sourceId: string): ReadonlyArray<DiagnosticCheck> {
    this.ensureReady();
    return this.registry.getChecksForSource(sourceId);
  }

  public async run(): Promise<DiagnosticReport> {
    this.ensureReadyOrRunning();

    if (this.activeRunPromise) {
      return this.activeRunPromise;
    }

    this.lifecycleState = DiagnosticsRuntimeState.RUNNING;

    this.activeRunPromise = (async () => {
      try {
        const startTime = Date.now();
        const sources = this.registry.listSources();
        const checks = [...this.registry.listChecks()];

        // Sort checks by priority desc, then id asc
        checks.sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));

        const results: DiagnosticResult[] = [];
        for (const check of checks) {
          const res = await this.executeCheckInternal(check);
          results.push(res);
        }

        const endTime = Date.now();
        const runDuration = endTime - startTime;

        const report = this.generateReportInternal(results, sources.length, checks.length);

        // Update run-level stats
        this.totalRuns += 1;
        this.totalDuration += runDuration;
        if (report.overallStatus === DiagnosticStatus.HEALTHY) {
          this.successfulRuns += 1;
        } else if (report.overallStatus === DiagnosticStatus.DEGRADED) {
          this.degradedRuns += 1;
        } else if (report.overallStatus === DiagnosticStatus.UNHEALTHY) {
          this.failedRuns += 1;
        }

        // Store history (FIFO)
        this.history.unshift(report);
        if (this.history.length > this.historyCapacity) {
          this.history.pop();
        }

        return report;
      } finally {
        this.activeRunPromise = null;
        if (this.lifecycleState === DiagnosticsRuntimeState.RUNNING) {
          this.lifecycleState = DiagnosticsRuntimeState.READY;
        }
      }
    })();

    return this.activeRunPromise;
  }

  public async runSource(sourceId: string): Promise<DiagnosticReport> {
    this.ensureReadyOrRunning();
    if (!this.registry.hasSource(sourceId)) {
      throw new DiagnosticSourceNotFoundError(`Diagnostic source with ID '${sourceId}' is not registered.`);
    }

    const startTime = Date.now();
    const checks = [...this.registry.getChecksForSource(sourceId)];

    // Sort checks by priority desc, then id asc
    checks.sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));

    const results: DiagnosticResult[] = [];
    for (const check of checks) {
      const res = await this.executeCheckInternal(check);
      results.push(res);
    }

    const endTime = Date.now();
    const runDuration = endTime - startTime;

    const report = this.generateReportInternal(results, 1, checks.length);

    // Update run-level stats
    this.totalRuns += 1;
    this.totalDuration += runDuration;
    if (report.overallStatus === DiagnosticStatus.HEALTHY) {
      this.successfulRuns += 1;
    } else if (report.overallStatus === DiagnosticStatus.DEGRADED) {
      this.degradedRuns += 1;
    } else if (report.overallStatus === DiagnosticStatus.UNHEALTHY) {
      this.failedRuns += 1;
    }

    // Store history (FIFO)
    this.history.unshift(report);
    if (this.history.length > this.historyCapacity) {
      this.history.pop();
    }

    return report;
  }

  public async runCheck(checkId: string): Promise<DiagnosticResult> {
    this.ensureReadyOrRunning();
    const check = this.registry.getCheck(checkId);
    if (!check) {
      throw new DiagnosticCheckNotFoundError(`Diagnostic check with ID '${checkId}' is not registered.`);
    }

    const res = await this.executeCheckInternal(check);
    return res;
  }

  private async executeCheckInternal(check: DiagnosticCheck): Promise<DiagnosticResult> {
    const res = await this.executor.execute(check);

    // Update check-level stats
    if (!check.enabled) {
      this.skippedChecks += 1;
    } else {
      this.executedChecks += 1;
      if (res.status === DiagnosticStatus.UNHEALTHY) {
        this.failedChecks += 1;
      }
      if (res.error?.name === 'DiagnosticTimeoutError') {
        this.timedOutChecks += 1;
      }
    }

    return res;
  }

  private generateReportInternal(
    results: ReadonlyArray<DiagnosticResult>,
    sourceCount: number,
    checkCount: number
  ): DiagnosticReport {
    const enabledResults = results.filter((r) => r.status !== DiagnosticStatus.DISABLED);

    let overallStatus: DiagnosticStatusValue = DiagnosticStatus.HEALTHY;
    if (enabledResults.length === 0) {
      overallStatus = DiagnosticStatus.UNKNOWN;
    } else {
      const hasUnhealthy = enabledResults.some((r) => r.status === DiagnosticStatus.UNHEALTHY);
      const hasDegraded = enabledResults.some((r) => r.status === DiagnosticStatus.DEGRADED);

      if (hasUnhealthy) {
        overallStatus = DiagnosticStatus.UNHEALTHY;
      } else if (hasDegraded) {
        overallStatus = DiagnosticStatus.DEGRADED;
      }
    }

    // Severity aggregation precedence: CRITICAL > ERROR > WARNING > INFO
    const severityPrecedence: Record<DiagnosticSeverityValue, number> = {
      [DiagnosticSeverity.CRITICAL]: 4,
      [DiagnosticSeverity.ERROR]: 3,
      [DiagnosticSeverity.WARNING]: 2,
      [DiagnosticSeverity.INFO]: 1
    };

    let overallSeverity: DiagnosticSeverityValue = DiagnosticSeverity.INFO;
    if (enabledResults.length > 0) {
      let maxPrecedence = 0;
      for (const r of enabledResults) {
        const prec = severityPrecedence[r.severity] || 1;
        if (prec > maxPrecedence) {
          maxPrecedence = prec;
          overallSeverity = r.severity;
        }
      }
    }

    const passedCount = enabledResults.filter((r) => r.status === DiagnosticStatus.HEALTHY).length;
    const degradedCount = enabledResults.filter((r) => r.status === DiagnosticStatus.DEGRADED).length;
    const failedCount = enabledResults.filter((r) => r.status === DiagnosticStatus.UNHEALTHY).length;
    const skippedCount = results.length - enabledResults.length;

    const reportId = `report-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const summary = `Overall status is ${overallStatus}. ${passedCount} passed, ${degradedCount} degraded, ${failedCount} failed, ${skippedCount} skipped.`;

    const reportStats = this.getStatistics();

    return createDiagnosticReport({
      reportId,
      generatedAt: Date.now(),
      runtimeState: this.lifecycleState,
      overallStatus,
      overallSeverity,
      sourceCount,
      checkCount,
      passedCount,
      degradedCount,
      failedCount,
      skippedCount,
      results,
      summary,
      statistics: reportStats
    });
  }

  public getHistory(): ReadonlyArray<DiagnosticReport> {
    this.ensureReady();
    return Object.freeze([...this.history]);
  }

  public clearHistory(): void {
    this.ensureReady();
    this.history.length = 0;
  }

  public getStatistics(): DiagnosticsStatistics {
    const avg = this.totalRuns > 0 ? this.totalDuration / this.totalRuns : 0;
    return createDiagnosticsStatistics({
      totalRuns: this.totalRuns,
      successfulRuns: this.successfulRuns,
      degradedRuns: this.degradedRuns,
      failedRuns: this.failedRuns,
      skippedChecks: this.skippedChecks,
      executedChecks: this.executedChecks,
      failedChecks: this.failedChecks,
      timedOutChecks: this.timedOutChecks,
      totalDuration: this.totalDuration,
      averageDuration: avg,
      sourceCount: this.registry.listSources().length,
      checkCount: this.registry.listChecks().length
    });
  }

  public getDiagnostics() {
    this.ensureReady();
    const sources = this.registry.listSources();
    const checks = this.registry.listChecks();

    return createDiagnosticsSnapshot({
      runtimeState: this.lifecycleState,
      sourceCount: sources.length,
      enabledSourceCount: sources.filter((s) => s.descriptor.enabled).length,
      checkCount: checks.length,
      enabledCheckCount: checks.filter((c) => c.enabled).length,
      historySize: this.history.length,
      statistics: this.getStatistics(),
      generatedAt: Date.now()
    });
  }
}
