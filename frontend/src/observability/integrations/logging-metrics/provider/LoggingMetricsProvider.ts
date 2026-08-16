import { ILoggingMetricsProvider } from '../interfaces/logging-metrics-provider';
import { IMetricsRuntime } from '../../../metrics/interfaces/metrics-runtime';
import { LogRecord } from '../../../logging/models/log';
import {
  LoggingMetricsPolicy,
  LoggingMetricResult,
  LoggingMetricsStatistics,
  LoggingMetricsDiagnostics
} from '../models';
import { LoggingMetricsPolicyRegistry } from '../registry/LoggingMetricsPolicyRegistry';
import {
  LoggingMetricsStateError
} from '../errors/LoggingMetricsErrors';
import { LoggingMetricsAdapter } from '../LoggingMetricsAdapter';
import { freezeDeepSafe } from '../../../models/monitoring';

export class LoggingMetricsProvider implements ILoggingMetricsProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry = new LoggingMetricsPolicyRegistry();

  private readonly _metricsRuntime: IMetricsRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Idempotency tracking (FIFO bounded queue)
  private readonly _processedEventIds: string[] = [];
  private readonly _maxProcessedIdsCapacity = 1000;

  // Concurrency tracking Map
  private readonly _inFlight = new Map<string, Promise<LoggingMetricResult>>();

  // Statistics counters
  private _totalEvaluations = 0;
  private _matchedPolicies = 0;
  private _skippedEvents = 0;
  private _acceptedEvents = 0;
  private _rejectedEvents = 0;
  private _metricObservationsEmitted = 0;
  private _counterIncrements = 0;
  private _gaugeUpdates = 0;
  private _histogramObservations = 0;
  private _timerObservations = 0;
  private _failedIntegrations = 0;
  private _totalProcessingDuration = 0;

  // Diagnostics recent failures list
  private readonly _recentFailures: {
    timestamp: number;
    error: { name: string; message: string; stack?: string };
  }[] = [];
  private readonly _maxRecentFailures = 50;

  constructor(dependencies: { metricsRuntime: IMetricsRuntime }) {
    if (!dependencies?.metricsRuntime) {
      throw new Error('metricsRuntime dependency is required.');
    }
    this._metricsRuntime = dependencies.metricsRuntime;
  }

  private ensureReady(): void {
    if (this._state !== 'READY') {
      throw new LoggingMetricsStateError(`Provider is not ready (state: ${this._state}).`);
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
      return Promise.reject(new LoggingMetricsStateError('Cannot initialize while stopping.'));
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
        this._processedEventIds.length = 0;
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

  public registerPolicy(policy: LoggingMetricsPolicy): void {
    this.ensureReady();
    this._registry.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this.ensureReady();
    this._registry.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): LoggingMetricsPolicy | null {
    this.ensureReady();
    return this._registry.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<LoggingMetricsPolicy> {
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

  public processLogRecord(record: LogRecord): Promise<LoggingMetricResult> {
    this.ensureReady();
    this._totalEvaluations++;
    const startTime = performance.now();

    // 1. Concurrency Protection
    const executionKey = record.id || `key_${record.timestamp}_${record.message.substring(0, 20)}`;
    const existing = this._inFlight.get(executionKey);
    if (existing) {
      return existing;
    }

    // 2. Idempotency Check
    if (record.id && this._processedEventIds.includes(record.id)) {
      this._skippedEvents++;
      return Promise.resolve(
        freezeDeepSafe({
          status: 'SKIPPED',
          reason: `Log record ID '${record.id}' has already been processed.`,
          duration: 0,
          timestamp: Date.now()
        }) as LoggingMetricResult
      );
    }

    const promise = (async () => {
      try {
        if (record.id) {
          if (this._processedEventIds.length >= this._maxProcessedIdsCapacity) {
            this._processedEventIds.shift();
          }
          this._processedEventIds.push(record.id);
        }

        const policies = this._registry.listPolicies();
        
        let matchingPolicy: LoggingMetricsPolicy | null = null;
        for (const policy of policies) {
          if (!policy.enabled) continue;
          
          if (policy.loggerName && policy.loggerName !== '*') {
            if (policy.loggerName !== record.loggerName) continue;
          }
          
          matchingPolicy = policy;
          break;
        }

        if (!matchingPolicy) {
          this._skippedEvents++;
          this._totalProcessingDuration += (Date.now() - startTime);
          return freezeDeepSafe({
            status: 'SKIPPED',
            reason: 'No matching policy found.',
            duration: performance.now() - startTime,
            timestamp: Date.now()
          }) as LoggingMetricResult;
        }

        this._matchedPolicies++;

        const adapterResult = await LoggingMetricsAdapter.adapt({
          record,
          policy: matchingPolicy,
          metricsRuntime: this._metricsRuntime
        });

        if (adapterResult.status === 'ACCEPTED') {
          this._acceptedEvents++;
          this._metricObservationsEmitted++;
          
          if (matchingPolicy.metricType === 'COUNTER') this._counterIncrements++;
          else if (matchingPolicy.metricType === 'GAUGE') this._gaugeUpdates++;
          else if (matchingPolicy.metricType === 'HISTOGRAM') this._histogramObservations++;
          else if (matchingPolicy.metricType === 'TIMER') this._timerObservations++;
        } else if (adapterResult.status === 'SKIPPED') {
          this._skippedEvents++;
        } else {
          this._rejectedEvents++;
        }

        this._totalProcessingDuration += (performance.now() - startTime);
        return adapterResult;
      } catch (err: any) {
        this._failedIntegrations++;
        this._rejectedEvents++;
        this._totalProcessingDuration += (performance.now() - startTime);
        
        this.recordFailure(err);

        return freezeDeepSafe({
          status: 'REJECTED',
          reason: `Integration failed: ${err.message}`,
          duration: performance.now() - startTime,
          timestamp: Date.now()
        }) as LoggingMetricResult;
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

  public getStatistics(): LoggingMetricsStatistics {
    const avgDuration = this._totalEvaluations > 0
      ? this._totalProcessingDuration / this._totalEvaluations
      : 0;

    return freezeDeepSafe({
      totalEvaluations: this._totalEvaluations,
      matchedPolicies: this._matchedPolicies,
      skippedEvents: this._skippedEvents,
      acceptedEvents: this._acceptedEvents,
      rejectedEvents: this._rejectedEvents,
      metricObservationsEmitted: this._metricObservationsEmitted,
      counterIncrements: this._counterIncrements,
      gaugeUpdates: this._gaugeUpdates,
      histogramObservations: this._histogramObservations,
      timerObservations: this._timerObservations,
      failedIntegrations: this._failedIntegrations,
      averageProcessingDuration: avgDuration
    }) as LoggingMetricsStatistics;
  }

  public getDiagnostics(): LoggingMetricsDiagnostics {
    return freezeDeepSafe({
      runtimeState: this._state,
      registeredPolicies: this._registry.listPolicies(),
      statistics: this.getStatistics(),
      health: this.getHealth(),
      recentFailures: [...this._recentFailures],
      generatedAt: Date.now()
    }) as LoggingMetricsDiagnostics;
  }
}
