import type { MetricDefinition } from './metric';

export interface HistogramAggregation {
  readonly count: number;
  readonly sum: number;
  readonly min: number;
  readonly max: number;
  readonly average: number;
  readonly buckets: Record<string, number>;
}

export interface TimerAggregation {
  readonly count: number;
  readonly sum: number;
  readonly min: number;
  readonly max: number;
  readonly average: number;
}

export interface MetricSnapshot {
  readonly definition: MetricDefinition;
  readonly values: ReadonlyArray<{
    readonly labels: Record<string, string>;
    readonly seriesKey: string;
    readonly value?: number;
    readonly histogram?: HistogramAggregation;
    readonly timer?: TimerAggregation;
  }>;
  readonly generatedAt: number;
}
