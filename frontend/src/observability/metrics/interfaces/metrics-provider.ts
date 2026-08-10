import type {
  ICounterInstrument,
  IGaugeInstrument,
  IHistogramInstrument,
  ITimerInstrument,
  IMetricInstrument
} from './metric-instrument';
import type { MetricDefinition } from '../models/metric';
import type { MetricSample } from '../models/sample';
import type { MetricSnapshot } from '../models/snapshot';
import type { MetricsStatistics, MetricsDiagnostics } from '../models/statistics';

export interface IMetricsProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  registerCounter(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ICounterInstrument;
  registerGauge(definition: Omit<MetricDefinition, 'type' | 'enabled'>): IGaugeInstrument;
  registerHistogram(definition: Omit<MetricDefinition, 'type' | 'enabled'> & { buckets?: number[] }): IHistogramInstrument;
  registerTimer(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ITimerInstrument;

  getMetric(name: string): IMetricInstrument;
  getCounter(name: string): ICounterInstrument;
  getGauge(name: string): IGaugeInstrument;
  getHistogram(name: string): IHistogramInstrument;
  getTimer(name: string): ITimerInstrument;

  removeMetric(name: string): void;
  listMetrics(): ReadonlyArray<MetricDefinition>;

  getSnapshot(name: string): MetricSnapshot;
  listSnapshots(): ReadonlyArray<MetricSnapshot>;

  getRecentSamples(limit?: number): ReadonlyArray<MetricSample>;
  getSamplesByMetric(name: string): ReadonlyArray<MetricSample>;
  getSamplesByLabel(name: string, labels: Record<string, string>): ReadonlyArray<MetricSample>;
  clearHistory(): void;

  getStatistics(): MetricsStatistics;
  getDiagnostics(): MetricsDiagnostics;
  flush(): Promise<void>;
}
