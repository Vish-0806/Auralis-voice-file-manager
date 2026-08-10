import type { ITimerInstrument } from '../interfaces/metric-instrument';
import type { MetricDefinition } from '../models/metric';
import { MetricType } from '../models/metric';
import type { MetricSample } from '../models/sample';
import type { TimerAggregation } from '../models/snapshot';
import { normalizeLabels, getSeriesKey, createMetricSample } from '../factories/metricsFactories';
import { MetricsValidationError } from '../errors/MetricsErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class TimerMetric implements ITimerInstrument {
  private enabled = true;
  private readonly aggregations = new Map<string, TimerAggregation>();

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

  public record(durationMs: number, labels?: Record<string, string>): void {
    if (typeof durationMs !== 'number' || isNaN(durationMs) || !isFinite(durationMs)) {
      throw new MetricsValidationError('Duration must be a valid number.');
    }
    if (durationMs < 0) {
      throw new MetricsValidationError('Duration cannot be negative.');
    }

    if (!this.enabled || !this.definition.enabled) {
      return;
    }

    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);

    const agg = this.aggregations.get(key) || this.createEmptyAggregation();
    const count = agg.count + 1;
    const sum = agg.sum + durationMs;
    const min = agg.count === 0 ? durationMs : Math.min(agg.min, durationMs);
    const max = agg.count === 0 ? durationMs : Math.max(agg.max, durationMs);
    const average = sum / count;

    const nextAgg: TimerAggregation = {
      count,
      sum,
      min,
      max,
      average
    };

    this.aggregations.set(key, nextAgg);

    const sample = createMetricSample({
      metricName: this.definition.name,
      metricType: MetricType.TIMER,
      value: durationMs,
      labels: normLabels,
      seriesKey: key,
      unit: this.definition.unit || 'ms',
      durationMs
    });
    this.onSampleRecorded(sample);
  }

  public start(labels?: Record<string, string>): () => void {
    const start = typeof performance !== 'undefined' ? performance.now() : Date.now();
    return () => {
      const end = typeof performance !== 'undefined' ? performance.now() : Date.now();
      const elapsed = end - start;
      this.record(elapsed, labels);
    };
  }

  public getAggregation(labels?: Record<string, string>): TimerAggregation {
    const normLabels = normalizeLabels(labels, this.definition.labelKeys);
    const key = getSeriesKey(normLabels);
    return freezeDeepSafe(this.aggregations.get(key) || this.createEmptyAggregation()) as TimerAggregation;
  }

  public getSeriesAggregations(): Array<{ labels: Record<string, string>; seriesKey: string; timer: TimerAggregation }> {
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
      return { labels, seriesKey: key, timer: freezeDeepSafe(val) as TimerAggregation };
    });
  }

  private createEmptyAggregation(): TimerAggregation {
    return {
      count: 0,
      sum: 0,
      min: 0,
      max: 0,
      average: 0
    };
  }
}
