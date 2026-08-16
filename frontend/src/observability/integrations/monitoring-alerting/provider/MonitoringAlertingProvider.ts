import { IMonitoringAlertingProvider } from '../interfaces/monitoring-alerting-provider';
import { IAlertingRuntime } from '../../../alerting/interfaces/alerting-runtime';
import { ICorrelationRuntime } from '../../../correlation/interfaces/correlation-runtime';
import { MonitoringResult } from '../../../models/monitoring';
import { MonitorStatusValue } from '../../../models/health';
import {
  MonitoringAlertPolicy,
  MonitoringAlertIntegrationResult,
  MonitoringAlertIntegrationStatistics,
  MonitoringAlertIntegrationDiagnostics
} from '../models';
import { MonitoringAlertPolicyRegistry } from '../registry/MonitoringAlertPolicyRegistry';
import {
  MonitoringAlertingStateError
} from '../errors/MonitoringAlertingErrors';
import { MonitoringAlertingAdapter } from '../MonitoringAlertingAdapter';
import { freezeDeepSafe } from '../../../models/monitoring';

export class MonitoringAlertingProvider implements IMonitoringAlertingProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry = new MonitoringAlertPolicyRegistry();
  
  private readonly _alertingRuntime: IAlertingRuntime;
  private readonly _correlationRuntime: ICorrelationRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // State Transition Tracker
  private readonly _lastStates = new Map<string, MonitorStatusValue>();

  // In-flight processing Map for concurrency protection
  private readonly _inFlight = new Map<string, Promise<MonitoringAlertIntegrationResult>>();

  // Statistics counters
  private _evaluations = 0;
  private _matchedPolicies = 0;
  private _skippedTriggers = 0;
  private _alertingRequests = 0;
  private _successfulAlertingRequests = 0;
  private _failedAlertingRequests = 0;
  private _suppressedRequests = 0;
  private _deduplicatedRequests = 0;
  private _duplicateIntegrationRequests = 0;
  private _integrationErrors = 0;
  private _totalIntegrationDuration = 0;

  // Diagnostics recent failures list
  private readonly _recentFailures: {
    timestamp: number;
    error: { name: string; message: string; stack?: string };
  }[] = [];
  private readonly _maxRecentFailures = 50;

  constructor(dependencies: {
    alertingRuntime: IAlertingRuntime;
    correlationRuntime: ICorrelationRuntime;
  }) {
    if (!dependencies?.alertingRuntime) {
      throw new Error('alertingRuntime dependency is required.');
    }
    if (!dependencies?.correlationRuntime) {
      throw new Error('correlationRuntime dependency is required.');
    }
    this._alertingRuntime = dependencies.alertingRuntime;
    this._correlationRuntime = dependencies.correlationRuntime;
  }

  private ensureReady(): void {
    if (this._state !== 'READY') {
      throw new MonitoringAlertingStateError(`Provider is not ready (state: ${this._state}).`);
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
      return Promise.reject(new MonitoringAlertingStateError('Cannot initialize while stopping.'));
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
        this._lastStates.clear();
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

  public registerPolicy(policy: MonitoringAlertPolicy): void {
    this.ensureReady();
    this._registry.registerPolicy(policy);
  }

  public unregisterPolicy(policyId: string): void {
    this.ensureReady();
    this._registry.unregisterPolicy(policyId);
  }

  public getPolicy(policyId: string): MonitoringAlertPolicy | null {
    this.ensureReady();
    return this._registry.getPolicy(policyId);
  }

  public listPolicies(): ReadonlyArray<MonitoringAlertPolicy> {
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

  public processResult(result: MonitoringResult): Promise<MonitoringAlertIntegrationResult> {
    this.ensureReady();
    this._evaluations++;
    const startTime = Date.now();

    // 1. Concurrency check: Deduplicate concurrent integration operations
    const targetKey = result.checkId ? `${result.componentId}/${result.checkId}` : result.componentId;
    const executionKey = `${targetKey}/${result.status}/${result.completedAt}`;
    
    const existing = this._inFlight.get(executionKey);
    if (existing) {
      this._duplicateIntegrationRequests++;
      return existing;
    }

    const promise = (async () => {
      try {
        // 2. State Transition Awareness
        const lastStatus = this._lastStates.get(targetKey);
        
        // Find matching policy first to check custom bypass rules (allowRepeat)
        const policies = this._registry.listPolicies();
        const policy = policies.find(p => p.enabled && (
          (p.checkId === result.checkId && p.componentId === result.componentId) ||
          (p.componentId === result.componentId && !p.checkId) ||
          (!p.componentId && !p.checkId && !p.source)
        ));

        // Skip integration if status hasn't changed, unless configured to allow repeats
        if (lastStatus === result.status && !policy?.metadata?.allowRepeat) {
          this._skippedTriggers++;
          return freezeDeepSafe({
            occurred: false,
            skipped: true,
            reason: `Monitoring status remains unchanged (${result.status}).`,
            timestamp: Date.now()
          }) as MonitoringAlertIntegrationResult;
        }

        // Keep track of the transition
        this._lastStates.set(targetKey, result.status);

        // 3. Delegate to Adapter
        const integrationResult = await MonitoringAlertingAdapter.adapt({
          result,
          policies,
          alertingRuntime: this._alertingRuntime,
          correlationRuntime: this._correlationRuntime
        });

        // 4. Update stats based on results
        if (integrationResult.occurred) {
          this._matchedPolicies++;
          this._alertingRequests++;
          const alertResult = integrationResult.alertingResult;
          if (alertResult) {
            if (alertResult.status === 'SUCCESS' || alertResult.status === 'COMPLETED') {
              this._successfulAlertingRequests++;
            } else if (alertResult.status === 'FAILED') {
              this._failedAlertingRequests++;
            } else if (alertResult.status === 'SUPPRESSED') {
              this._suppressedRequests++;
            } else if (alertResult.status === 'DUPLICATE') {
              this._deduplicatedRequests++;
            }
          }
        } else {
          this._skippedTriggers++;
        }

        this._totalIntegrationDuration += (Date.now() - startTime);
        return integrationResult;
      } catch (err: any) {
        this._integrationErrors++;
        this._failedAlertingRequests++;
        this._totalIntegrationDuration += (Date.now() - startTime);

        this.recordFailure(err);

        // Return a normalized integration failure instead of crashing the flow
        return freezeDeepSafe({
          occurred: false,
          skipped: false,
          reason: `Integration failed: ${err.message}`,
          timestamp: Date.now()
        }) as MonitoringAlertIntegrationResult;
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

  public getStatistics(): MonitoringAlertIntegrationStatistics {
    const avgDuration = this._evaluations > 0
      ? this._totalIntegrationDuration / this._evaluations
      : 0;

    return freezeDeepSafe({
      evaluations: this._evaluations,
      matchedPolicies: this._matchedPolicies,
      skippedTriggers: this._skippedTriggers,
      alertingRequests: this._alertingRequests,
      successfulAlertingRequests: this._successfulAlertingRequests,
      failedAlertingRequests: this._failedAlertingRequests,
      suppressedRequests: this._suppressedRequests,
      deduplicatedRequests: this._deduplicatedRequests,
      duplicateIntegrationRequests: this._duplicateIntegrationRequests,
      integrationErrors: this._integrationErrors,
      averageIntegrationDuration: avgDuration
    }) as MonitoringAlertIntegrationStatistics;
  }

  public getDiagnostics(): MonitoringAlertIntegrationDiagnostics {
    return freezeDeepSafe({
      lifecycleState: this._state,
      policyCount: this._registry.getPolicyCount(),
      statistics: this.getStatistics(),
      recentFailures: [...this._recentFailures],
      health: this.getHealth(),
      generatedAt: Date.now()
    }) as MonitoringAlertIntegrationDiagnostics;
  }
}
