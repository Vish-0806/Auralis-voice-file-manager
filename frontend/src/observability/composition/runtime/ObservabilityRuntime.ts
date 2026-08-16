import { IObservabilityCompositionRuntime } from '../interfaces/composition-runtime';
import { IObservabilityCompositionProvider } from '../interfaces/composition-provider';
import { ObservabilityCompositionProvider } from '../provider/ObservabilityCompositionProvider';
import {
  ObservabilityCompositionStateValue,
  ObservabilityCompositionHealth,
  ObservabilityCompositionStatistics,
  ObservabilityCompositionDiagnostics
} from '../models';
import { IMonitoringRuntime } from '../../interfaces/monitoring-runtime';
import { ILoggingRuntime } from '../../logging/interfaces/logging-runtime';
import { IMetricsRuntime } from '../../metrics/interfaces/metrics-runtime';
import { ITracingRuntime } from '../../tracing/interfaces/tracing-runtime';
import { ITelemetryRuntime } from '../../telemetry/interfaces/telemetry-runtime';
import { IDiagnosticsRuntime } from '../../diagnostics/interfaces/diagnostics-runtime';
import { IAlertingRuntime } from '../../alerting/interfaces/alerting-runtime';

export class ObservabilityRuntime implements IObservabilityCompositionRuntime {
  private readonly _provider: IObservabilityCompositionProvider;

  constructor(provider?: IObservabilityCompositionProvider) {
    this._provider = provider || new ObservabilityCompositionProvider();
  }

  public provider(): IObservabilityCompositionProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): ObservabilityCompositionStateValue {
    return this._provider.getState();
  }

  public getHealth(): ObservabilityCompositionHealth {
    return this._provider.getHealth();
  }

  public getStatistics(): ObservabilityCompositionStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): ObservabilityCompositionDiagnostics {
    return this._provider.getDiagnostics();
  }

  public monitoring(): IMonitoringRuntime {
    return this._provider.monitoring();
  }

  public logging(): ILoggingRuntime {
    return this._provider.logging();
  }

  public metrics(): IMetricsRuntime {
    return this._provider.metrics();
  }

  public tracing(): ITracingRuntime {
    return this._provider.tracing();
  }

  public telemetry(): ITelemetryRuntime {
    return this._provider.telemetry();
  }

  public diagnostics(): IDiagnosticsRuntime {
    return this._provider.diagnostics();
  }

  public alerting(): IAlertingRuntime {
    return this._provider.alerting();
  }
}
