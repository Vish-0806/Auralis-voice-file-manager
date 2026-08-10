import type { IMetricsProvider } from '../interfaces/metrics-provider';
import type {
  ICounterInstrument,
  IGaugeInstrument,
  IHistogramInstrument,
  ITimerInstrument,
  IMetricInstrument
} from '../interfaces/metric-instrument';
import { type MetricDefinition, MetricType } from '../models/metric';
import type { MetricSample } from '../models/sample';
import type { MetricSnapshot, HistogramAggregation, TimerAggregation } from '../models/snapshot';
import type { MetricsStatistics, MetricsDiagnostics } from '../models/statistics';
import { MetricsRegistry } from '../registry/MetricsRegistry';
import { CounterMetric } from './CounterMetric';
import { GaugeMetric } from './GaugeMetric';
import { HistogramMetric } from './HistogramMetric';
import { TimerMetric } from './TimerMetric';
import {
  MetricsStateError,
  MetricsInitializationError,
  MetricsValidationError
} from '../errors/MetricsErrors';
import { normalizeLabels } from '../factories/metricsFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class MetricsProvider implements IMetricsProvider {
  private lifecycleState = 'UNINITIALIZED';
  private readonly registry = new MetricsRegistry();
  private readonly history: MetricSample[] = [];
  private readonly historyCapacity = 1000;

  // Stats
  private totalSamples = 0;
  private counterSamples = 0;
  private gaugeSamples = 0;
  private histogramSamples = 0;
  private timerSamples = 0;
  private rejectedSamples = 0;
  private lastSampleTimestamp?: number;
  private minSampleValue?: number;
  private maxSampleValue?: number;

  private ensureReady(): void {
    if (this.lifecycleState !== 'READY') {
      throw new MetricsStateError(`Metrics provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (this.lifecycleState === 'READY') {
      return;
    }
    if (this.lifecycleState === 'INITIALIZING' || this.lifecycleState === 'STOPPING' || this.lifecycleState === 'STOPPED') {
      throw new MetricsStateError(`Cannot initialize metrics provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = 'INITIALIZING';
    try {
      this.lifecycleState = 'READY';
    } catch (err: any) {
      this.lifecycleState = 'ERROR';
      throw new MetricsInitializationError(`Failed to initialize metrics provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === 'STOPPED') {
      return;
    }
    if (this.lifecycleState === 'UNINITIALIZED') {
      throw new MetricsStateError('Cannot shutdown metrics provider: it is not initialized.');
    }

    this.lifecycleState = 'STOPPING';
    try {
      await this.flush();
    } finally {
      this.lifecycleState = 'STOPPED';
    }
  }

  public getState(): string {
    return this.lifecycleState;
  }

  private handleSampleRecorded(sample: MetricSample): void {
    // If provider is not READY, count as rejected
    if (this.lifecycleState !== 'READY') {
      this.rejectedSamples += 1;
      return;
    }

    this.totalSamples += 1;
    this.lastSampleTimestamp = sample.timestamp;

    if (this.minSampleValue === undefined || sample.value < this.minSampleValue) {
      this.minSampleValue = sample.value;
    }
    if (this.maxSampleValue === undefined || sample.value > this.maxSampleValue) {
      this.maxSampleValue = sample.value;
    }

    if (sample.metricType === MetricType.COUNTER) this.counterSamples += 1;
    else if (sample.metricType === MetricType.GAUGE) this.gaugeSamples += 1;
    else if (sample.metricType === MetricType.HISTOGRAM) this.histogramSamples += 1;
    else if (sample.metricType === MetricType.TIMER) this.timerSamples += 1;

    // FIFO eviction
    if (this.history.length >= this.historyCapacity) {
      this.history.shift();
    }
    this.history.push(sample);
  }

  public registerCounter(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ICounterInstrument {
    this.ensureReady();
    const fullDef: MetricDefinition = {
      ...definition,
      type: MetricType.COUNTER,
      enabled: true
    };
    const instrument = new CounterMetric(fullDef, s => this.handleSampleRecorded(s));
    this.registry.register(instrument);
    return instrument;
  }

  public registerGauge(definition: Omit<MetricDefinition, 'type' | 'enabled'>): IGaugeInstrument {
    this.ensureReady();
    const fullDef: MetricDefinition = {
      ...definition,
      type: MetricType.GAUGE,
      enabled: true
    };
    const instrument = new GaugeMetric(fullDef, s => this.handleSampleRecorded(s));
    this.registry.register(instrument);
    return instrument;
  }

  public registerHistogram(definition: Omit<MetricDefinition, 'type' | 'enabled'> & { buckets?: number[] }): IHistogramInstrument {
    this.ensureReady();
    const fullDef: MetricDefinition = {
      ...definition,
      type: MetricType.HISTOGRAM,
      enabled: true
    };
    const instrument = new HistogramMetric(fullDef, s => this.handleSampleRecorded(s), definition.buckets);
    this.registry.register(instrument);
    return instrument;
  }

  public registerTimer(definition: Omit<MetricDefinition, 'type' | 'enabled'>): ITimerInstrument {
    this.ensureReady();
    const fullDef: MetricDefinition = {
      ...definition,
      type: MetricType.TIMER,
      enabled: true
    };
    const instrument = new TimerMetric(fullDef, s => this.handleSampleRecorded(s));
    this.registry.register(instrument);
    return instrument;
  }

  public getMetric(name: string): IMetricInstrument {
    this.ensureReady();
    return this.registry.get(name);
  }

  public getCounter(name: string): ICounterInstrument {
    this.ensureReady();
    const metric = this.registry.get(name);
    if (metric.getDefinition().type !== MetricType.COUNTER) {
      throw new MetricsValidationError(`Metric '${name}' is registered but is not a Counter.`);
    }
    return metric as ICounterInstrument;
  }

  public getGauge(name: string): IGaugeInstrument {
    this.ensureReady();
    const metric = this.registry.get(name);
    if (metric.getDefinition().type !== MetricType.GAUGE) {
      throw new MetricsValidationError(`Metric '${name}' is registered but is not a Gauge.`);
    }
    return metric as IGaugeInstrument;
  }

  public getHistogram(name: string): IHistogramInstrument {
    this.ensureReady();
    const metric = this.registry.get(name);
    if (metric.getDefinition().type !== MetricType.HISTOGRAM) {
      throw new MetricsValidationError(`Metric '${name}' is registered but is not a Histogram.`);
    }
    return metric as IHistogramInstrument;
  }

  public getTimer(name: string): ITimerInstrument {
    this.ensureReady();
    const metric = this.registry.get(name);
    if (metric.getDefinition().type !== MetricType.TIMER) {
      throw new MetricsValidationError(`Metric '${name}' is registered but is not a Timer.`);
    }
    return metric as ITimerInstrument;
  }

  public removeMetric(name: string): void {
    this.ensureReady();
    this.registry.unregister(name);
  }

  public listMetrics(): ReadonlyArray<MetricDefinition> {
    this.ensureReady();
    return this.registry.list();
  }

  public getSnapshot(name: string): MetricSnapshot {
    this.ensureReady();
    const metric = this.registry.get(name);
    const def = metric.getDefinition();

    let values: Array<{
      labels: Record<string, string>;
      seriesKey: string;
      value?: number;
      histogram?: HistogramAggregation;
      timer?: TimerAggregation;
    }> = [];

    if (metric instanceof CounterMetric) {
      values = metric.getSeriesValues();
    } else if (metric instanceof GaugeMetric) {
      values = metric.getSeriesValues();
    } else if (metric instanceof HistogramMetric) {
      values = metric.getSeriesAggregations();
    } else if (metric instanceof TimerMetric) {
      values = metric.getSeriesAggregations();
    }

    const snapshot: MetricSnapshot = {
      definition: def,
      values,
      generatedAt: Date.now()
    };

    return freezeDeepSafe(snapshot) as MetricSnapshot;
  }

  public listSnapshots(): ReadonlyArray<MetricSnapshot> {
    this.ensureReady();
    const instruments = this.registry.listInstruments();
    const list = instruments.map(inst => this.getSnapshot(inst.getDefinition().name));
    return freezeDeepSafe(list) as ReadonlyArray<MetricSnapshot>;
  }

  public getRecentSamples(limit?: number): ReadonlyArray<MetricSample> {
    this.ensureReady();
    const take = limit !== undefined ? Math.min(limit, this.history.length) : this.history.length;
    const startIndex = this.history.length - take;
    return freezeDeepSafe(this.history.slice(startIndex)) as ReadonlyArray<MetricSample>;
  }

  public getSamplesByMetric(name: string): ReadonlyArray<MetricSample> {
    this.ensureReady();
    const filtered = this.history.filter(s => s.metricName === name);
    return freezeDeepSafe(filtered) as ReadonlyArray<MetricSample>;
  }

  public getSamplesByLabel(name: string, labels: Record<string, string>): ReadonlyArray<MetricSample> {
    this.ensureReady();
    const normLabels = normalizeLabels(labels);
    const filtered = this.history.filter(s => {
      if (s.metricName !== name) return false;
      if (!s.labels) return false;
      for (const [k, v] of Object.entries(normLabels)) {
        if (s.labels[k] !== v) return false;
      }
      return true;
    });
    return freezeDeepSafe(filtered) as ReadonlyArray<MetricSample>;
  }

  public clearHistory(): void {
    this.ensureReady();
    this.history.length = 0;
  }

  public getStatistics(): MetricsStatistics {
    this.ensureReady();
    return freezeDeepSafe({
      registeredMetricCount: this.registry.getMetricCount(),
      totalSamples: this.totalSamples,
      counterSamples: this.counterSamples,
      gaugeSamples: this.gaugeSamples,
      histogramSamples: this.histogramSamples,
      timerSamples: this.timerSamples,
      rejectedSamples: this.rejectedSamples,
      historySize: this.history.length,
      lastSampleTimestamp: this.lastSampleTimestamp,
      minSampleValue: this.minSampleValue,
      maxSampleValue: this.maxSampleValue
    });
  }

  public getDiagnostics(): MetricsDiagnostics {
    this.ensureReady();
    const warnings: string[] = [];
    if (this.rejectedSamples > 0) {
      warnings.push(`Detected ${this.rejectedSamples} rejected samples.`);
    }

    // Count series across all instruments
    let seriesCount = 0;
    const instruments = this.registry.listInstruments();
    for (const inst of instruments) {
      if (inst instanceof CounterMetric || inst instanceof GaugeMetric) {
        seriesCount += inst.getSeriesValues().length;
      } else if (inst instanceof HistogramMetric || inst instanceof TimerMetric) {
        seriesCount += inst.getSeriesAggregations().length;
      }
    }

    return freezeDeepSafe({
      runtimeState: this.lifecycleState,
      metricCount: this.registry.getMetricCount(),
      seriesCount,
      historySize: this.history.length,
      statistics: this.getStatistics(),
      generatedAt: Date.now(),
      warnings
    });
  }

  public async flush(): Promise<void> {
    if (this.lifecycleState !== 'READY' && this.lifecycleState !== 'STOPPING') {
      throw new MetricsStateError(`Cannot flush in state: ${this.lifecycleState}`);
    }
    // No-op for local metrics provider
  }
}
