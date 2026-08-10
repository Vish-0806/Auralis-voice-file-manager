import type { ICounterInstrument } from '../interfaces/metric-instrument';
import type { MetricDefinition } from '../models/metric';
import { MetricType } from '../models/metric';
import type { MetricSample } from '../models/sample';
import { normalizeLabels, getSeriesKey, createMetricSample } from '../factories/metricsFactories';
import { MetricsValidationError } from '../errors/MetricsErrors';

export class CounterMetric implements ICounterInstrument {
  private enabled = true;
  private readonly values = new Map<string, number>();

  constructor(
    private readonly definition: MetricDefinition,
    private readonly onSampleRecorded: (sample: MetricSample) => void
  ) {}

  public getDefinition(): MetricDefinition {
    return this.definition;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  public increment(value = 1, labels?: Record<string, string>): void {
    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
      throw new MetricsValidationError('Increment value must be a valid number.');
    }
    if (value < 0) {
      throw new MetricsValidationError('Counter increment value must be positive (non-negative).');
    }

    if (!this.enabled || !this.definition.enabled) {
      return;
    }

    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);
    
    const current = this.values.get(key) || 0;
    const nextVal = current + value;
    this.values.set(key, nextVal);

    const sample = createMetricSample({
      metricName: this.definition.name,
      metricType: MetricType.COUNTER,
      value: nextVal,
      labels: normLabels,
      seriesKey: key,
      unit: this.definition.unit
    });
    this.onSampleRecorded(sample);
  }

  public getValue(labels?: Record<string, string>): number {
    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);
    return this.values.get(key) || 0;
  }

  public getSeriesValues(): Array<{ labels: Record<string, string>; seriesKey: string; value: number }> {
    return Array.from(this.values.entries()).map(([key, val]) => {
      const labels: Record<string, string> = {};
      if (key) {
        key.split(',').forEach(pair => {
          const parts = pair.split('=');
          const k = parts[0];
          const v = parts[1];
          if (k && v !== undefined) {
            labels[decodeURIComponent(k)] = decodeURIComponent(v);
          }
        });
      }
      return { labels, seriesKey: key, value: val };
    });
  }
}
