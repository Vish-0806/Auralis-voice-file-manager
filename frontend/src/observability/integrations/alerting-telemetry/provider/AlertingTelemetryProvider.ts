import { IAlertingTelemetryProvider } from '../interfaces/alerting-telemetry-provider';
import { ITelemetryRuntime } from '../../../telemetry/interfaces/telemetry-runtime';
import {
  AlertingTelemetryPolicy,
  AlertingTelemetryTrigger,
  AlertingTelemetryResult,
  AlertingTelemetryStatistics,
  AlertingTelemetryDiagnostics
} from '../models';
import { AlertingTelemetryPolicyRegistry } from '../registry/AlertingTelemetryPolicyRegistry';
import { AlertingTelemetryStateError } from '../errors/AlertingTelemetryErrors';
import { AlertingTelemetryAdapter, findMatchingPolicy } from '../AlertingTelemetryAdapter';
import { freezeDeepSafe } from '../../../models/monitoring';

export class AlertingTelemetryProvider implements IAlertingTelemetryProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry = new AlertingTelemetryPolicyRegistry();
  private readonly _telemetryRuntime: ITelemetryRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Idempotency tracking (FIFO bounded queue of idempotency keys)
  private readonly _processedKeys: string[] = [];
  private readonly _maxProcessedCapacity = 1000;

  // Concurrency tracking Map
  private readonly _inFlight = new Map<string, Promise<AlertingTelemetryResult>>();

  // Statistics counters
  private _totalIntegrationAttempts = 0;
  private _successfulIntegrations = 0;
  private _skippedIntegrations = 0;
  private _duplicateEvents = 0;
  private _rejectedEvents = 0;
  private _failedIntegrations = 0;
  private _telemetryRecordsCreated = 0;
  private _telemetryDispatchFailures = 0;
  private _policyMatches = 0;
  private _policyMisses = 0;
  private _totalDuration = 0;
  private _batchCount = 0;
  private _batchItemCount = 0;

  // Diagnostics recent failures list
  private readonly _recentFailures: {
    timestamp: number;
    error: { name: string; message: string; stack?: string };
  }[] = [];
  private readonly _maxRecentFailures = 50;
  private _lastIntegrationTimestamp?: number;

  constructor(dependencies: { telemetryRuntime: ITelemetryRuntime }) {
    if (!dependencies?.telemetryRuntime) {
      throw new Error('telemetryRuntime dependency is required.');
    }
    this._telemetryRuntime = dependencies.telemetryRuntime;
  }

  private ensureReady(): void {
    if (this._state !== 'READY') {
      throw new AlertingTelemetryStateError(`Provider is not ready (state: ${this._state}).`);
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
      return Promise.reject(new AlertingTelemetryStateError('Cannot initialize while stopping.'));
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

  public registerPolicy(policy: AlertingTelemetryPolicy): void {
    this.ensureReady();
    this._registry.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this.ensureReady();
    this._registry.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): AlertingTelemetryPolicy | null {
    this.ensureReady();
    return this._registry.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<AlertingTelemetryPolicy> {
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

  public integrate(trigger: AlertingTelemetryTrigger): Promise<AlertingTelemetryResult> {
    this.ensureReady();
    this._totalIntegrationAttempts++;
    this._lastIntegrationTimestamp = Date.now();
    const startTime = performance.now();

    const executionKey = `${trigger.kind}/${trigger.alertId || ''}/${trigger.fingerprint || ''}/${trigger.lifecycleState || ''}/${trigger.timestamp}`;
    const existing = this._inFlight.get(executionKey);
    if (existing) {
      this._duplicateEvents++;
      return existing;
    }

    const promise = (async () => {
      try {
        const policies = this._registry.listPolicies();
        const policy = findMatchingPolicy(policies, trigger);

        if (!policy) {
          this._policyMisses++;
          this._skippedIntegrations++;
          const duration = performance.now() - startTime;
          this._totalDuration += duration;
          return freezeDeepSafe({
            status: 'SKIPPED',
            reason: 'No matching policy found.',
            duration,
            timestamp: Date.now()
          }) as AlertingTelemetryResult;
        }

        this._policyMatches++;

        // Idempotency check
        const idempotencyKey = `${trigger.kind}/${trigger.alertId || ''}/${trigger.fingerprint || ''}/${trigger.lifecycleState || ''}/${trigger.timestamp}/${policy.id}/${policy.telemetryType}`;
        const isDuplicate = this._processedKeys.includes(idempotencyKey);

        if (isDuplicate && !policy.allowRepeat) {
          this._duplicateEvents++;
          this._skippedIntegrations++;
          const duration = performance.now() - startTime;
          this._totalDuration += duration;
          return freezeDeepSafe({
            status: 'SKIPPED',
            reason: `Duplicate event found for idempotency key: ${idempotencyKey}`,
            duration,
            timestamp: Date.now()
          }) as AlertingTelemetryResult;
        }

        if (!isDuplicate) {
          if (this._processedKeys.length >= this._maxProcessedCapacity) {
            this._processedKeys.shift();
          }
          this._processedKeys.push(idempotencyKey);
        }

        // Delegate to Adapter
        const result = await AlertingTelemetryAdapter.adapt({
          trigger,
          policy,
          telemetryRuntime: this._telemetryRuntime
        });

        if (result.status === 'ACCEPTED') {
          this._successfulIntegrations++;
          this._telemetryRecordsCreated++;
        } else if (result.status === 'SKIPPED') {
          this._skippedIntegrations++;
        } else {
          this._rejectedEvents++;
          this._failedIntegrations++;
        }

        const duration = performance.now() - startTime;
        this._totalDuration += duration;
        return result;
      } catch (err: any) {
        this._rejectedEvents++;
        this._failedIntegrations++;
        this._telemetryDispatchFailures++;
        const duration = performance.now() - startTime;
        this._totalDuration += duration;

        this.recordFailure(err);

        return freezeDeepSafe({
          status: 'REJECTED',
          reason: `Integration failed: ${err.message}`,
          duration,
          timestamp: Date.now()
        }) as AlertingTelemetryResult;
      } finally {
        this._inFlight.delete(executionKey);
      }
    })();

    this._inFlight.set(executionKey, promise);
    return promise;
  }

  public async integrateBatch(triggers: ReadonlyArray<AlertingTelemetryTrigger>): Promise<ReadonlyArray<AlertingTelemetryResult>> {
    this.ensureReady();
    this._batchCount++;
    this._batchItemCount += triggers.length;

    const results = await Promise.all(
      triggers.map(async (trigger) => {
        try {
          return await this.integrate(trigger);
        } catch (err: any) {
          this.recordFailure(err);
          return freezeDeepSafe({
            status: 'REJECTED',
            reason: `Batch item integration failed: ${err.message}`,
            duration: 0,
            timestamp: Date.now()
          }) as AlertingTelemetryResult;
        }
      })
    );

    return freezeDeepSafe(results) as ReadonlyArray<AlertingTelemetryResult>;
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

  public statistics(): AlertingTelemetryStatistics {
    const avgDuration = this._totalIntegrationAttempts > 0
      ? this._totalDuration / this._totalIntegrationAttempts
      : 0;

    return freezeDeepSafe({
      totalIntegrationAttempts: this._totalIntegrationAttempts,
      successfulIntegrations: this._successfulIntegrations,
      skippedIntegrations: this._skippedIntegrations,
      duplicateEvents: this._duplicateEvents,
      rejectedEvents: this._rejectedEvents,
      failedIntegrations: this._failedIntegrations,
      telemetryRecordsCreated: this._telemetryRecordsCreated,
      telemetryDispatchFailures: this._telemetryDispatchFailures,
      policyMatches: this._policyMatches,
      policyMisses: this._policyMisses,
      averageIntegrationDuration: avgDuration,
      batchCount: this._batchCount,
      batchItemCount: this._batchItemCount
    }) as AlertingTelemetryStatistics;
  }

  public diagnostics(): AlertingTelemetryDiagnostics {
    return freezeDeepSafe({
      runtimeState: this._state,
      policyCount: this._registry.getPolicyCount(),
      statistics: this.statistics(),
      idempotencyCacheSize: this._processedKeys.length,
      inFlightRequestCount: this._inFlight.size,
      lastIntegrationTimestamp: this._lastIntegrationTimestamp,
      recentFailures: [...this._recentFailures],
      health: this.getHealth(),
      generatedAt: Date.now()
    }) as AlertingTelemetryDiagnostics;
  }
}
