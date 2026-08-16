import { IDiagnosticsTelemetryProvider } from '../interfaces/diagnostics-telemetry-provider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import { DiagnosticReport } from '../../../diagnostics/models/report';
import {
  DiagnosticsTelemetryPolicy,
  DiagnosticsTelemetryResult,
  DiagnosticsTelemetryStatistics,
  DiagnosticsTelemetryDiagnostics
} from '../models';
import { DiagnosticsTelemetryPolicyRegistry } from '../registry/DiagnosticsTelemetryPolicyRegistry';
import { DiagnosticsTelemetryStateError } from '../errors/DiagnosticsTelemetryErrors';
import { DiagnosticsTelemetryAdapter } from '../DiagnosticsTelemetryAdapter';
import {
  buildTriggerFromReport,
  buildTriggerFromResult
} from '../factories/diagnosticsTelemetryFactories';
import { freezeDeepSafe } from '../../../models/monitoring';

export class DiagnosticsTelemetryProvider implements IDiagnosticsTelemetryProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry = new DiagnosticsTelemetryPolicyRegistry();

  private readonly _telemetryRuntime: ITelemetryRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Idempotency tracking (FIFO bounded queue of diagnosticRunId [+ resultId] + policyId + telemetryType)
  private readonly _processedKeys: string[] = [];
  private readonly _maxProcessedCapacity = 1000;

  // Concurrency tracking Map
  private readonly _inFlight = new Map<string, Promise<ReadonlyArray<DiagnosticsTelemetryResult>>>();

  // Statistics counters
  private _totalEvaluations = 0;
  private _matchedPolicies = 0;
  private _skippedResults = 0;
  private _acceptedResults = 0;
  private _rejectedResults = 0;
  private _telemetryRecordsEmitted = 0;
  private _sampledRecords = 0;
  private _unsampledRecords = 0;
  private _severityBypasses = 0;
  private _duplicateEvents = 0;
  private _failedIntegrations = 0;
  private _totalProcessingDuration = 0;
  private _runLevelIntegrations = 0;
  private _resultLevelIntegrations = 0;

  // Diagnostics recent failures list
  private readonly _recentFailures: {
    timestamp: number;
    error: { name: string; message: string; stack?: string };
  }[] = [];
  private readonly _maxRecentFailures = 50;

  constructor(dependencies: { telemetryRuntime: ITelemetryRuntime }) {
    if (!dependencies?.telemetryRuntime) {
      throw new Error('telemetryRuntime dependency is required.');
    }
    this._telemetryRuntime = dependencies.telemetryRuntime;
  }

  private ensureReady(): void {
    if (this._state !== 'READY') {
      throw new DiagnosticsTelemetryStateError(`Provider is not ready (state: ${this._state}).`);
    }
  }

  public initialize(): Promise<void> {
    if (this._state === 'READY') {
      return Promise.resolve();
    }
    if (this._state === 'INITIALIZING') {
      return this._initPromise || Promise.resolve();
    }
    if (this._state === 'STOPPING') {
      return Promise.reject(new DiagnosticsTelemetryStateError('Cannot initialize while stopping.'));
    }

    this._state = 'INITIALIZING';
    this._initPromise = (async () => {
      await Promise.resolve();
      try {
        this._state = 'READY';
      } catch (err) {
        this._state = 'FAILED';
        throw err;
      } finally {
        this._initPromise = null;
      }
    })();

    return this._initPromise;
  }

  public shutdown(): Promise<void> {
    if (this._state === 'STOPPED' || this._state === 'UNINITIALIZED') {
      return Promise.resolve();
    }
    if (this._state === 'STOPPING') {
      return this._shutdownPromise || Promise.resolve();
    }

    this._state = 'STOPPING';
    this._shutdownPromise = (async () => {
      await Promise.resolve();
      try {
        this._registry.clear();
        this._processedKeys.length = 0;
        this._inFlight.clear();
        this._recentFailures.length = 0;
        this._state = 'STOPPED';
      } catch (err) {
        this._state = 'FAILED';
        throw err;
      } finally {
        this._shutdownPromise = null;
      }
    })();

    return this._shutdownPromise;
  }

  public getState(): string {
    return this._state;
  }

  public getHealth(): string {
    if (this._state === 'UNINITIALIZED') return 'UNKNOWN';
    if (this._state === 'FAILED') return 'UNHEALTHY';
    if (this._state === 'READY') {
      if (this._recentFailures.length > 10) return 'DEGRADED';
      return 'HEALTHY';
    }
    return 'UNKNOWN';
  }

  public registerPolicy(policy: DiagnosticsTelemetryPolicy): void {
    this.ensureReady();
    this._registry.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this.ensureReady();
    this._registry.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): DiagnosticsTelemetryPolicy | null {
    this.ensureReady();
    return this._registry.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<DiagnosticsTelemetryPolicy> {
    this.ensureReady();
    return this._registry.listPolicies();
  }

  public enablePolicy(policyId: string): void {
    this.ensureReady();
    this._registry.enablePolicy(policyId);
  }

  public disablePolicy(policyId: string): void {
    this.ensureReady();
    this._registry.disablePolicy(policyId);
  }

  public processDiagnosticReport(report: DiagnosticReport): Promise<ReadonlyArray<DiagnosticsTelemetryResult>> {
    this.ensureReady();
    this._totalEvaluations++;
    const startTime = performance.now();

    // 1. Concurrency check
    const executionKey = report.reportId;
    const existing = this._inFlight.get(executionKey);
    if (existing) {
      return existing;
    }

    const promise = (async () => {
      const results: DiagnosticsTelemetryResult[] = [];
      try {
        const policies = this._registry.listPolicies();

        const runPolicies = policies.filter(p => p.enabled && p.level === 'RUN');
        const resultPolicies = policies.filter(p => p.enabled && p.level === 'RESULT');

        // A. Run-Level Evaluation
        let matchingRunPolicy: DiagnosticsTelemetryPolicy | null = null;
        for (const policy of runPolicies) {
          if (policy.severity && policy.severity !== report.overallSeverity) continue;
          if (policy.status && policy.status !== report.overallStatus) continue;
          
          matchingRunPolicy = policy;
          break;
        }

        if (matchingRunPolicy) {
          this._matchedPolicies++;
          const idempotencyKey = `${report.reportId}/${matchingRunPolicy.id}/${matchingRunPolicy.telemetryType}`;
          const isDuplicate = this._processedKeys.includes(idempotencyKey);

          if (isDuplicate && !matchingRunPolicy.allowRepeat) {
            this._duplicateEvents++;
            this._skippedResults++;
            results.push(
              freezeDeepSafe({
                status: 'SKIPPED',
                reason: `Diagnostic run evaluation '${idempotencyKey}' already processed.`,
                duration: performance.now() - startTime,
                timestamp: Date.now()
              }) as DiagnosticsTelemetryResult
            );
          } else {
            if (!isDuplicate) {
              if (this._processedKeys.length >= this._maxProcessedCapacity) {
                this._processedKeys.shift();
              }
              this._processedKeys.push(idempotencyKey);
            }

            try {
              const trigger = buildTriggerFromReport(report);
              const adaptResult = await DiagnosticsTelemetryAdapter.adapt({
                trigger,
                policy: matchingRunPolicy,
                telemetryRuntime: this._telemetryRuntime
              });

              this.updateStats(adaptResult, matchingRunPolicy, trigger.diagnosticSeverity);
              this._runLevelIntegrations++;
              results.push(adaptResult);
            } catch (err: any) {
              this._failedIntegrations++;
              this._rejectedResults++;
              this.recordFailure(err);
              results.push(
                freezeDeepSafe({
                  status: 'REJECTED',
                  reason: `Run integration failed: ${err.message}`,
                  duration: performance.now() - startTime,
                  timestamp: Date.now()
                }) as DiagnosticsTelemetryResult
              );
            }
          }
        }

        // B. Result-Level Evaluation
        for (const res of report.results) {
          let matchingResultPolicy: DiagnosticsTelemetryPolicy | null = null;
          for (const policy of resultPolicies) {
            if (policy.sourceId && policy.sourceId !== res.sourceId) continue;
            if (policy.checkId && policy.checkId !== res.checkId) continue;
            if (policy.severity && policy.severity !== res.severity) continue;
            if (policy.status && policy.status !== res.status) continue;

            const category = (res as any).category || (res.metadata as any).category;
            if (policy.category && policy.category !== category) continue;

            matchingResultPolicy = policy;
            break;
          }

          if (matchingResultPolicy) {
            this._matchedPolicies++;
            const idempotencyKey = `${report.reportId}/${res.sourceId}/${res.checkId}/${matchingResultPolicy.id}/${matchingResultPolicy.telemetryType}`;
            const isDuplicate = this._processedKeys.includes(idempotencyKey);

            if (isDuplicate && !matchingResultPolicy.allowRepeat) {
              this._duplicateEvents++;
              this._skippedResults++;
              results.push(
                freezeDeepSafe({
                  status: 'SKIPPED',
                  reason: `Diagnostic result evaluation '${idempotencyKey}' already processed.`,
                  duration: performance.now() - startTime,
                  timestamp: Date.now()
                }) as DiagnosticsTelemetryResult
              );
            } else {
              if (!isDuplicate) {
                if (this._processedKeys.length >= this._maxProcessedCapacity) {
                  this._processedKeys.shift();
                }
                this._processedKeys.push(idempotencyKey);
              }

              try {
                const trigger = buildTriggerFromResult(res, report.reportId);
                const adaptResult = await DiagnosticsTelemetryAdapter.adapt({
                  trigger,
                  policy: matchingResultPolicy,
                  telemetryRuntime: this._telemetryRuntime
                });

                this.updateStats(adaptResult, matchingResultPolicy, trigger.diagnosticSeverity);
                this._resultLevelIntegrations++;
                results.push(adaptResult);
              } catch (err: any) {
                this._failedIntegrations++;
                this._rejectedResults++;
                this.recordFailure(err);
                results.push(
                  freezeDeepSafe({
                    status: 'REJECTED',
                    reason: `Result integration failed: ${err.message}`,
                    duration: performance.now() - startTime,
                    timestamp: Date.now()
                  }) as DiagnosticsTelemetryResult
                );
              }
            }
          }
        }

        this._totalProcessingDuration += (performance.now() - startTime);
        return freezeDeepSafe(results) as ReadonlyArray<DiagnosticsTelemetryResult>;
      } catch (err: any) {
        this._failedIntegrations++;
        this._rejectedResults++;
        this._totalProcessingDuration += (performance.now() - startTime);
        this.recordFailure(err);

        return freezeDeepSafe([
          {
            status: 'REJECTED',
            reason: `Integration critical failure: ${err.message}`,
            duration: performance.now() - startTime,
            timestamp: Date.now()
          }
        ]) as ReadonlyArray<DiagnosticsTelemetryResult>;
      } finally {
        this._inFlight.delete(executionKey);
      }
    })();

    this._inFlight.set(executionKey, promise);
    return promise;
  }

  private updateStats(result: DiagnosticsTelemetryResult, policy: DiagnosticsTelemetryPolicy, severity: string): void {
    if (result.status === 'ACCEPTED') {
      this._acceptedResults++;
      this._telemetryRecordsEmitted++;

      const isError = severity === 'CRITICAL' || severity === 'ERROR';
      if (isError && policy.bypassSamplingOnError) {
        this._severityBypasses++;
      }

      if (policy.samplingRate !== undefined && policy.samplingRate < 1.0) {
        this._sampledRecords++;
      } else {
        this._unsampledRecords++;
      }
    } else if (result.status === 'SKIPPED') {
      this._skippedResults++;
    } else {
      this._rejectedResults++;
    }
  }

  private recordFailure(err: any): void {
    const errorObj = {
      name: err.name || 'Error',
      message: err.message || String(err),
      stack: err.stack
    };
    this._recentFailures.unshift({
      timestamp: Date.now(),
      error: errorObj
    });
    if (this._recentFailures.length > this._maxRecentFailures) {
      this._recentFailures.pop();
    }
  }

  public getStatistics(): DiagnosticsTelemetryStatistics {
    const avgDuration = this._totalEvaluations > 0
      ? this._totalProcessingDuration / this._totalEvaluations
      : 0;

    return freezeDeepSafe({
      totalEvaluations: this._totalEvaluations,
      matchedPolicies: this._matchedPolicies,
      skippedResults: this._skippedResults,
      acceptedResults: this._acceptedResults,
      rejectedResults: this._rejectedResults,
      telemetryRecordsEmitted: this._telemetryRecordsEmitted,
      sampledRecords: this._sampledRecords,
      unsampledRecords: this._unsampledRecords,
      severityBypasses: this._severityBypasses,
      duplicateEvents: this._duplicateEvents,
      failedIntegrations: this._failedIntegrations,
      averageProcessingDuration: avgDuration,
      runLevelIntegrations: this._runLevelIntegrations,
      resultLevelIntegrations: this._resultLevelIntegrations
    }) as DiagnosticsTelemetryStatistics;
  }

  public getDiagnostics(): DiagnosticsTelemetryDiagnostics {
    return freezeDeepSafe({
      runtimeState: this._state,
      registeredPolicyCount: this._registry.getPolicyCount(),
      statistics: this.getStatistics(),
      health: this.getHealth(),
      recentFailures: [...this._recentFailures],
      historyCapacity: this._maxProcessedCapacity,
      generatedAt: Date.now()
    }) as DiagnosticsTelemetryDiagnostics;
  }
}
