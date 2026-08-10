import type { IHistogramInstrument } from '../interfaces/metric-instrument';
import type { MetricDefinition } from '../models/metric';
import { MetricType } from '../models/metric';
import type { MetricSample } from '../models/sample';
import type { HistogramAggregation } from '../models/snapshot';
import { normalizeLabels, getSeriesKey, createMetricSample } from '../factories/metricsFactories';
import { MetricsValidationError } from '../errors/MetricsErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class HistogramMetric implements IHistogramInstrument {
  private enabled = true;
  private readonly aggregations = new Map<string, HistogramAggregation>();
  private readonly bucketBoundaries: number[];

  constructor(
    private readonly definition: MetricDefinition,
    private readonly onSampleRecorded: (sample: MetricSample) => void,
    buckets?: number[]
  ) {
    const rawBuckets = buckets || [0, 10, 50, 100, 500, 1000];
    if (!Array.isArray(rawBuckets)) {
      throw new MetricsValidationError('Histogram buckets must be an array of numbers.');
    }
    for (let i = 0; i < rawBuckets.length; i++) {
      if (typeof rawBuckets[i] !== 'number' || isNaN(rawBuckets[i])) {
        throw new MetricsValidationError('Histogram bucket boundaries must be valid numbers.');
      }
      if (i > 0 && rawBuckets[i] <= rawBuckets[i - 1]) {
        throw new MetricsValidationError('Histogram bucket boundaries must be sorted in strictly ascending order.');
      }
    }
    this.bucketBoundaries = [...rawBuckets];
  }

  public getDefinition(): MetricDefinition {
    return this.definition;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  public observe(value: number, labels?: Record<string, string>): void {
    if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
      throw new MetricsValidationError('Observed value must be a valid number.');
    }

    if (!this.enabled || !this.definition.enabled) {
      return;
    }

    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);

    const agg = this.aggregations.get(key) || this.createEmptyAggregation();
    const count = agg.count + 1;
    const sum = agg.sum + value;
    const min = agg.count === 0 ? value : Math.min(agg.min, value);
    const max = agg.count === 0 ? value : Math.max(agg.max, value);
    const average = sum / count;

    const buckets = { ...agg.buckets };
    for (const boundary of this.bucketBoundaries) {
      if (value <= boundary) {
        buckets[String(boundary)] = (buckets[String(boundary)] || 0) + 1;
      }
    }
    buckets['+Inf'] = (buckets['+Inf'] || 0) + 1;

    const nextAgg: HistogramAggregation = {
      count,
      sum,
      min,
      max,
      average,
      buckets
    };

    this.aggregations.set(key, nextAgg);

    const sample = createMetricSample({
      metricName: this.definition.name,
      metricType: MetricType.HISTOGRAM,
      value,
      labels: normLabels,
      seriesKey: key,
      unit: this.definition.unit
    });
    this.onSampleRecorded(sample);
  }

  public getAggregation(labels?: Record<string, string>): HistogramAggregation {
    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);
    return freezeDeepSafe(this.aggregations.get(key) || this.createEmptyAggregation()) as HistogramAggregation;
  }

  public getSeriesAggregations(): Array<{ labels: Record<string, string>; seriesKey: string; histogram: HistogramAggregation }> {
    return Array.from(this.aggregations.entries()).map(([key, val]) => {
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
      return { labels, seriesKey: key, histogram: freezeDeepSafe(val) as HistogramAggregation };
    });
  }

  private createEmptyAggregation(): HistogramAggregation {
    const buckets: Record<string, number> = {};
    for (const boundary of this.bucketBoundaries) {
      buckets[String(boundary)] = 0;
    }
    buckets['+Inf'] = 0;

    return {
      count: 0,
      sum: 0,
      min: 0,
      max: 0,
      average: 0,
      buckets
    };
  }
}
