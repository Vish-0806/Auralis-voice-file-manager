import { IObservabilityCompositionProvider } from '../interfaces/composition-provider';
import {
  ObservabilityCompositionState,
  ObservabilityCompositionStateValue,
  ObservabilityCompositionHealth,
  ObservabilityCompositionStatistics,
  ObservabilityCompositionDiagnostics,
  ObservabilitySubsystem,
  ObservabilitySubsystemState,
  ObservabilitySubsystemHealth
} from '../models';
import { IMonitoringRuntime } from '../../interfaces/monitoring-runtime';
import { ILoggingRuntime } from '../../logging/interfaces/logging-runtime';
import { IMetricsRuntime } from '../../metrics/interfaces/metrics-runtime';
import { ITracingRuntime } from '../../tracing/interfaces/tracing-runtime';
import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import { IDiagnosticsRuntime } from '../../diagnostics/interfaces/diagnostics-runtime';
import { IAlertingRuntime } from '../../alerting/interfaces/alerting-runtime';

import { MonitoringRuntime } from '../../runtime/MonitoringRuntime';
import { LoggingRuntime } from '../../logging/runtime/LoggingRuntime';
import { MetricsRuntime } from '../../metrics/runtime/MetricsRuntime';
import { TracingRuntime } from '../../tracing/runtime/TracingRuntime';
import { TelemetryRuntime } from '../../telemetry/runtime/TelemetryRuntime';
import { DiagnosticsRuntime } from '../../diagnostics/runtime/DiagnosticsRuntime';
import { AlertingRuntime } from '../../alerting/runtime/AlertingRuntime';

import {
  ObservabilityCompositionStateError,
  ObservabilityCompositionInitializationError,
  ObservabilityCompositionShutdownError
} from '../errors/CompositionErrors';

import { freezeDeepSafe } from '../../models/monitoring';
import { MonitorStatus, MonitorStatusValue } from '../../models/health';

export class ObservabilityCompositionProvider implements IObservabilityCompositionProvider {
  private _state: ObservabilityCompositionStateValue = ObservabilityCompositionState.UNINITIALIZED;
  private readonly _monitoring: IMonitoringRuntime;
  private readonly _logging: ILoggingRuntime;
  private readonly _metrics: IMetricsRuntime;
  private readonly _tracing: ITracingRuntime;
  private readonly _telemetry: ITelemetryRuntime;
  private readonly _diagnostics: IDiagnosticsRuntime;
  private readonly _alerting: IAlertingRuntime;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Statistics
  private _initializationCount = 0;
  private _shutdownCount = 0;
  private _initializationFailures = 0;
  private _shutdownFailures = 0;
  private _totalLifecycleOperations = 0;
  private _successfulLifecycleOperations = 0;
  private _failedLifecycleOperations = 0;
  private _totalLifecycleDurationMs = 0;

  constructor(dependencies?: {
    monitoring?: IMonitoringRuntime;
    logging?: ILoggingRuntime;
    metrics?: IMetricsRuntime;
    tracing?: ITracingRuntime;
    telemetry?: ITelemetryRuntime;
    diagnostics?: IDiagnosticsRuntime;
    alerting?: IAlertingRuntime;
  }) {
    this._monitoring = dependencies?.monitoring || new MonitoringRuntime();
    this._logging = dependencies?.logging || new LoggingRuntime();
    this._metrics = dependencies?.metrics || new MetricsRuntime();
    this._tracing = dependencies?.tracing || new TracingRuntime();
    this._telemetry = dependencies?.telemetry || new TelemetryRuntime();
    this._diagnostics = dependencies?.diagnostics || new DiagnosticsRuntime();
    this._alerting = dependencies?.alerting || new AlertingRuntime();
  }

  public initialize(): Promise<void> {
    if (this._state === ObservabilityCompositionState.READY) {
      return Promise.resolve();
    }
    if (this._state === ObservabilityCompositionState.INITIALIZING) {
      return this._initPromise || Promise.resolve();
    }
    if (this._state === ObservabilityCompositionState.STOPPING) {
      return Promise.reject(new ObservabilityCompositionStateError('Cannot initialize while stopping.'));
    }

    this._state = ObservabilityCompositionState.INITIALIZING;
    this._totalLifecycleOperations++;
    const startTime = Date.now();

    this._initPromise = (async () => {
      const initialized: { subsystem: string; runtime: any }[] = [];
      const order = [
        { name: ObservabilitySubsystem.MONITORING, runtime: this._monitoring },
        { name: ObservabilitySubsystem.LOGGING, runtime: this._logging },
        { name: ObservabilitySubsystem.METRICS, runtime: this._metrics },
        { name: ObservabilitySubsystem.TRACING, runtime: this._tracing },
        { name: ObservabilitySubsystem.TELEMETRY, runtime: this._telemetry },
        { name: ObservabilitySubsystem.DIAGNOSTICS, runtime: this._diagnostics },
        { name: ObservabilitySubsystem.ALERTING, runtime: this._alerting }
      ];

      try {
        for (const sub of order) {
          await sub.runtime.initialize();
          initialized.push({ subsystem: sub.name, runtime: sub.runtime });
        }
        
        this._state = ObservabilityCompositionState.READY;
        this._initializationCount++;
        this._successfulLifecycleOperations++;
        this._totalLifecycleDurationMs += (Date.now() - startTime);
      } catch (err: any) {
        this._state = ObservabilityCompositionState.FAILED;
        this._initializationFailures++;
        this._failedLifecycleOperations++;
        this._totalLifecycleDurationMs += (Date.now() - startTime);

        // Failure compensation: shut down already initialized subsystems in reverse order
        for (let i = initialized.length - 1; i >= 0; i--) {
          try {
            await initialized[i].runtime.shutdown();
          } catch {
            // Prioritize returning the primary error
          }
        }

        throw new ObservabilityCompositionInitializationError(
          `Observability initialization failed: ${err.message}`
        );
      } finally {
        this._initPromise = null;
      }
    })();

    return this._initPromise;
  }

  public shutdown(): Promise<void> {
    if (
      this._state === ObservabilityCompositionState.STOPPED ||
      this._state === ObservabilityCompositionState.UNINITIALIZED
    ) {
      return Promise.resolve();
    }
    if (this._state === ObservabilityCompositionState.STOPPING) {
      return this._shutdownPromise || Promise.resolve();
    }

    this._state = ObservabilityCompositionState.STOPPING;
    this._totalLifecycleOperations++;
    const startTime = Date.now();

    this._shutdownPromise = (async () => {
      const order = [
        { name: ObservabilitySubsystem.ALERTING, runtime: this._alerting },
        { name: ObservabilitySubsystem.DIAGNOSTICS, runtime: this._diagnostics },
        { name: ObservabilitySubsystem.TELEMETRY, runtime: this._telemetry },
        { name: ObservabilitySubsystem.TRACING, runtime: this._tracing },
        { name: ObservabilitySubsystem.METRICS, runtime: this._metrics },
        { name: ObservabilitySubsystem.LOGGING, runtime: this._logging },
        { name: ObservabilitySubsystem.MONITORING, runtime: this._monitoring }
      ];

      let shutdownError: Error | null = null;

      for (const sub of order) {
        try {
          await sub.runtime.shutdown();
        } catch (err: any) {
          if (!shutdownError) {
            shutdownError = err;
          }
        }
      }

      this._shutdownCount++;
      this._totalLifecycleDurationMs += (Date.now() - startTime);

      if (shutdownError) {
        this._state = ObservabilityCompositionState.FAILED;
        this._shutdownFailures++;
        this._failedLifecycleOperations++;
        this._shutdownPromise = null;
        throw new ObservabilityCompositionShutdownError(
          `Observability shutdown failed: ${shutdownError.message}`
        );
      } else {
        this._state = ObservabilityCompositionState.STOPPED;
        this._successfulLifecycleOperations++;
        this._shutdownPromise = null;
      }
    })();

    return this._shutdownPromise;
  }

  public getState(): ObservabilityCompositionStateValue {
    return this._state;
  }

  public getHealth(): ObservabilityCompositionHealth {
    const subsystemHealths: ObservabilitySubsystemHealth[] = [];

    const evalSubsystemHealth = (state: string): MonitorStatusValue => {
      if (state === 'READY' || state === 'INITIALIZED') {
        return MonitorStatus.HEALTHY;
      }
      if (state === 'ERROR' || state === 'FAILED') {
        return MonitorStatus.UNHEALTHY;
      }
      return MonitorStatus.UNKNOWN;
    };

    // 1. Monitoring Runtime has a dedicated getHealth() interface
    let monitoringHealthStatus: MonitorStatusValue = MonitorStatus.UNKNOWN;
    try {
      monitoringHealthStatus = this._monitoring.getHealth().status;
    } catch {
      monitoringHealthStatus = MonitorStatus.UNHEALTHY;
    }
    subsystemHealths.push({
      subsystem: ObservabilitySubsystem.MONITORING,
      status: monitoringHealthStatus
    });

    // 2. Map other runtimes using adaptions from their state APIs
    const subsystems = [
      { name: ObservabilitySubsystem.LOGGING, runtime: this._logging },
      { name: ObservabilitySubsystem.METRICS, runtime: this._metrics },
      { name: ObservabilitySubsystem.TRACING, runtime: this._tracing },
      { name: ObservabilitySubsystem.TELEMETRY, runtime: this._telemetry },
      { name: ObservabilitySubsystem.DIAGNOSTICS, runtime: this._diagnostics },
      { name: ObservabilitySubsystem.ALERTING, runtime: this._alerting }
    ];

    for (const sub of subsystems) {
      let status: MonitorStatusValue;
      try {
        status = evalSubsystemHealth(sub.runtime.getState());
      } catch {
        status = MonitorStatus.UNHEALTHY;
      }
      subsystemHealths.push({ subsystem: sub.name, status });
    }

    let healthyCount = 0;
    let degradedCount = 0;
    let unhealthyCount = 0;

    for (const h of subsystemHealths) {
      if (h.status === MonitorStatus.HEALTHY) {
        healthyCount++;
      } else if (h.status === MonitorStatus.DEGRADED) {
        degradedCount++;
      } else if (h.status === MonitorStatus.UNHEALTHY) {
        unhealthyCount++;
      }
    }

    let overallStatus: MonitorStatusValue = MonitorStatus.HEALTHY;
    if (unhealthyCount > 0) {
      overallStatus = MonitorStatus.UNHEALTHY;
    } else if (degradedCount > 0) {
      overallStatus = MonitorStatus.DEGRADED;
    } else if (healthyCount === 0) {
      overallStatus = MonitorStatus.UNKNOWN;
    }

    return freezeDeepSafe({
      status: overallStatus,
      subsystemHealths,
      unhealthySubsystemCount: unhealthyCount,
      degradedSubsystemCount: degradedCount,
      healthySubsystemCount: healthyCount,
      generatedAt: Date.now()
    }) as ObservabilityCompositionHealth;
  }

  public getStatistics(): ObservabilityCompositionStatistics {
    const avgDuration = this._totalLifecycleOperations > 0
      ? this._totalLifecycleDurationMs / this._totalLifecycleOperations
      : 0;

    return freezeDeepSafe({
      initializationCount: this._initializationCount,
      shutdownCount: this._shutdownCount,
      initializationFailures: this._initializationFailures,
      shutdownFailures: this._shutdownFailures,
      totalLifecycleOperations: this._totalLifecycleOperations,
      successfulLifecycleOperations: this._successfulLifecycleOperations,
      failedLifecycleOperations: this._failedLifecycleOperations,
      averageLifecycleDurationMs: avgDuration
    }) as ObservabilityCompositionStatistics;
  }

  public getDiagnostics(): ObservabilityCompositionDiagnostics {
    const subsystemStates: ObservabilitySubsystemState[] = [];

    const order = [
      { name: ObservabilitySubsystem.MONITORING, runtime: this._monitoring },
      { name: ObservabilitySubsystem.LOGGING, runtime: this._logging },
      { name: ObservabilitySubsystem.METRICS, runtime: this._metrics },
      { name: ObservabilitySubsystem.TRACING, runtime: this._tracing },
      { name: ObservabilitySubsystem.TELEMETRY, runtime: this._telemetry },
      { name: ObservabilitySubsystem.DIAGNOSTICS, runtime: this._diagnostics },
      { name: ObservabilitySubsystem.ALERTING, runtime: this._alerting }
    ];

    const health = this.getHealth();

    for (const sub of order) {
      let stateStr = 'UNKNOWN';
      try {
        stateStr = sub.runtime.getState();
      } catch {
        stateStr = 'ERROR';
      }
      const isHealthy = health.subsystemHealths.find(h => h.subsystem === sub.name)?.status === MonitorStatus.HEALTHY;
      subsystemStates.push({
        subsystem: sub.name,
        state: stateStr,
        healthy: isHealthy
      });
    }

    return freezeDeepSafe({
      compositionState: this._state,
      subsystemStates,
      health,
      statistics: this.getStatistics(),
      generatedAt: Date.now()
    }) as ObservabilityCompositionDiagnostics;
  }

  public monitoring(): IMonitoringRuntime { return this._monitoring; }
  public logging(): ILoggingRuntime { return this._logging; }
  public metrics(): IMetricsRuntime { return this._metrics; }
  public tracing(): ITracingRuntime { return this._tracing; }
  public telemetry(): ITelemetryRuntime { return this._telemetry; }
  public diagnostics(): IDiagnosticsRuntime { return this._diagnostics; }
  public alerting(): IAlertingRuntime { return this._alerting; }
}
