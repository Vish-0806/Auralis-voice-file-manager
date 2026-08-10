import type { IMetricsRuntime } from '../interfaces/metrics-runtime';
import type { IMetricsProvider } from '../interfaces/metrics-provider';
import type {
  ICounterInstrument,
  IGaugeInstrument,
  IHistogramInstrument,
  ITimerInstrument,
  IMetricInstrument
} from '../interfaces/metric-instrument';
import { MetricsProvider } from '../provider/MetricsProvider';
import type { MetricDefinition } from '../models/metric';
import type { MetricSample } from '../models/sample';
import type { MetricSnapshot } from '../models/snapshot';
import type { MetricsStatistics, MetricsDiagnostics } from '../models/statistics';

export class MetricsRuntime implements IMetricsRuntime {
  private readonly _provider: IMetricsProvider;

  constructor(provider?: IMetricsProvider) {
    this._provider = provider || new MetricsProvider();
  }

  public provider(): IMetricsProvider {
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

  public registerCounter(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ICounterInstrument {
    return this._provider.registerCounter(definition);
  }

  public registerGauge(definition: Omit<MetricDefinition, 'type' | 'enabled'>): IGaugeInstrument {
    return this._provider.registerGauge(definition);
  }

  public registerHistogram(definition: Omit<MetricDefinition, 'type' | 'enabled'> & { buckets?: number[] }): IHistogramInstrument {
    return this._provider.registerHistogram(definition);
  }

  public registerTimer(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ITimerInstrument {
    return this._provider.registerTimer(definition);
  }

  public getMetric(name: string): IMetricInstrument {
    return this._provider.getMetric(name);
  }

  public getCounter(name: string): ICounterInstrument {
    return this._provider.getCounter(name);
  }

  public getGauge(name: string): IGaugeInstrument {
    return this._provider.getGauge(name);
  }

  public getHistogram(name: string): IHistogramInstrument {
    return this._provider.getHistogram(name);
  }

  public getTimer(name: string): ITimerInstrument {
    return this._provider.getTimer(name);
  }

  public removeMetric(name: string): void {
    this._provider.removeMetric(name);
  }

  public listMetrics(): ReadonlyArray<MetricDefinition> {
    return this._provider.listMetrics();
  }

  public getSnapshot(name: string): MetricSnapshot {
    return this._provider.getSnapshot(name);
  }

  public listSnapshots(): ReadonlyArray<MetricSnapshot> {
    return this._provider.listSnapshots();
  }

  public getRecentSamples(limit?: number): ReadonlyArray<MetricSample> {
    return this._provider.getRecentSamples(limit);
  }

  public getSamplesByMetric(name: string): ReadonlyArray<MetricSample> {
    return this._provider.getSamplesByMetric(name);
  }

  public getSamplesByLabel(name: string, labels: Record<string, string>): ReadonlyArray<MetricSample> {
    return this._provider.getSamplesByLabel(name, labels);
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }

  public getStatistics(): MetricsStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): MetricsDiagnostics {
    return this._provider.getDiagnostics();
  }

  public flush(): Promise<void> {
    return this._provider.flush();
  }
}
