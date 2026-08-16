import { ITracingTelemetryProvider } from '../interfaces/tracing-telemetry-provider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import { Span } from '../../../tracing/models/span';
import {
  TracingTelemetryPolicy,
  TracingTelemetryResult,
  TracingTelemetryStatistics,
  TracingTelemetryDiagnostics
} from '../models';
import { TracingTelemetryPolicyRegistry } from '../registry/TracingTelemetryPolicyRegistry';
import {
  TracingTelemetryStateError
} from '../errors/TracingTelemetryErrors';
import { TracingTelemetryAdapter } from '../TracingTelemetryAdapter';
import { freezeDeepSafe } from '../../../models/monitoring';

export class TracingTelemetryProvider implements ITracingTelemetryProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry = new TracingTelemetryPolicyRegistry();

  private readonly _telemetryRuntime: ITelemetryRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Idempotency tracking (FIFO bounded queue of traceId + spanId + policyId + telemetryType)
  private readonly _processedKeys: string[] = [];
  private readonly _maxProcessedCapacity = 1000;

  // Concurrency tracking Map
  private readonly _inFlight = new Map<string, Promise<TracingTelemetryResult>>();

  // Statistics counters
  private _totalEvaluations = 0;
  private _matchedPolicies = 0;
  private _skippedSpans = 0;
  private _acceptedSpans = 0;
  private _rejectedSpans = 0;
  private _telemetryRecordsEmitted = 0;
  private _sampledRecords = 0;
  private _unsampledRecords = 0;
  private _errorBypasses = 0;
  private _duplicateEvents = 0;
  private _failedIntegrations = 0;
  private _totalProcessingDuration = 0;

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
      throw new TracingTelemetryStateError(`Provider is not ready (state: ${this._state}).`);
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
      return Promise.reject(new TracingTelemetryStateError('Cannot initialize while stopping.'));
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

  public registerPolicy(policy: TracingTelemetryPolicy): void {
    this.ensureReady();
    this._registry.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this.ensureReady();
    this._registry.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): TracingTelemetryPolicy | null {
    this.ensureReady();
    return this._registry.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<TracingTelemetryPolicy> {
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

  public processCompletedSpan(span: Span): Promise<TracingTelemetryResult> {
    this.ensureReady();
    this._totalEvaluations++;
    const startTime = performance.now();

    // 1. Concurrency Check
    const executionKey = `${span.traceId}/${span.spanId}`;
    const existing = this._inFlight.get(executionKey);
    if (existing) {
      return existing;
    }

    const promise = (async () => {
      try {
        const policies = this._registry.listPolicies();
        
        let matchingPolicy: TracingTelemetryPolicy | null = null;
        for (const policy of policies) {
          if (!policy.enabled) continue;

          if (policy.traceName && policy.traceName !== '*') {
            const traceName = (span.attributes as any)?.traceName;
            if (traceName !== policy.traceName) continue;
          }

          if (policy.spanName && policy.spanName !== '*') {
            if (policy.spanName !== span.name) continue;
          }

          if (policy.spanKind && policy.spanKind !== span.kind) continue;

          if (policy.statusFilter && policy.statusFilter.length > 0) {
            if (!policy.statusFilter.includes(span.status)) continue;
          }

          matchingPolicy = policy;
          break;
        }

        if (!matchingPolicy) {
          this._skippedSpans++;
          this._totalProcessingDuration += (performance.now() - startTime);
          return freezeDeepSafe({
            status: 'SKIPPED',
            reason: 'No matching policy found.',
            duration: performance.now() - startTime,
            timestamp: Date.now()
          }) as TracingTelemetryResult;
        }

        this._matchedPolicies++;

        // 2. Idempotency Check
        const idempotencyKey = `${span.traceId}/${span.spanId}/${matchingPolicy.id}/${matchingPolicy.telemetryType}`;
        if (this._processedKeys.includes(idempotencyKey)) {
          this._duplicateEvents++;
          this._skippedSpans++;
          this._totalProcessingDuration += (performance.now() - startTime);
          return freezeDeepSafe({
            status: 'SKIPPED',
            reason: `Span observation '${idempotencyKey}' has already been processed under this policy.`,
            duration: performance.now() - startTime,
            timestamp: Date.now()
          }) as TracingTelemetryResult;
        }

        if (this._processedKeys.length >= this._maxProcessedCapacity) {
          this._processedKeys.shift();
        }
        this._processedKeys.push(idempotencyKey);

        // 3. Delegate to Adapter
        const adapterResult = await TracingTelemetryAdapter.adapt({
          span,
          policy: matchingPolicy,
          telemetryRuntime: this._telemetryRuntime
        });

        if (adapterResult.status === 'ACCEPTED') {
          this._acceptedSpans++;
          this._telemetryRecordsEmitted++;

          const isError = span.status === 'ERROR';
          if (isError && matchingPolicy.bypassSamplingOnError) {
            this._errorBypasses++;
          }

          if (matchingPolicy.samplingRate !== undefined && matchingPolicy.samplingRate < 1.0) {
            this._sampledRecords++;
          } else {
            this._unsampledRecords++;
          }
        } else if (adapterResult.status === 'SKIPPED') {
          this._skippedSpans++;
        } else {
          this._rejectedSpans++;
        }

        this._totalProcessingDuration += (performance.now() - startTime);
        return adapterResult;
      } catch (err: any) {
        this._failedIntegrations++;
        this._rejectedSpans++;
        this._totalProcessingDuration += (performance.now() - startTime);
        
        this.recordFailure(err);

        return freezeDeepSafe({
          status: 'REJECTED',
          reason: `Integration failed: ${err.message}`,
          duration: performance.now() - startTime,
          timestamp: Date.now()
        }) as TracingTelemetryResult;
      } finally {
        this._inFlight.delete(executionKey);
      }
    })();

    this._inFlight.set(executionKey, promise);
    return promise;
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

  public getStatistics(): TracingTelemetryStatistics {
    const avgDuration = this._totalEvaluations > 0
      ? this._totalProcessingDuration / this._totalEvaluations
      : 0;

    return freezeDeepSafe({
      totalEvaluations: this._totalEvaluations,
      matchedPolicies: this._matchedPolicies,
      skippedSpans: this._skippedSpans,
      acceptedSpans: this._acceptedSpans,
      rejectedSpans: this._rejectedSpans,
      telemetryRecordsEmitted: this._telemetryRecordsEmitted,
      sampledRecords: this._sampledRecords,
      unsampledRecords: this._unsampledRecords,
      errorBypasses: this._errorBypasses,
      duplicateEvents: this._duplicateEvents,
      failedIntegrations: this._failedIntegrations,
      averageProcessingDuration: avgDuration
    }) as TracingTelemetryStatistics;
  }

  public getDiagnostics(): TracingTelemetryDiagnostics {
    return freezeDeepSafe({
      runtimeState: this._state,
      registeredPolicyCount: this._registry.getPolicyCount(),
      statistics: this.getStatistics(),
      health: this.getHealth(),
      recentFailures: [...this._recentFailures],
      historyCapacity: this._maxProcessedCapacity,
      generatedAt: Date.now()
    }) as TracingTelemetryDiagnostics;
  }
}
