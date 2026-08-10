import type { MetricDefinition } from '../models/metric';
import type { HistogramAggregation, TimerAggregation } from '../models/snapshot';

export interface IMetricInstrument {
  getDefinition(): MetricDefinition;
  isEnabled(): boolean;
  setEnabled(enabled: boolean): void;
}

export interface ICounterInstrument extends IMetricInstrument {
  increment(value?: number, labels?: Record<string, string>): void;
  getValue(labels?: Record<string, string>): number;
}

export interface IGaugeInstrument extends IMetricInstrument {
  set(value: number, labels?: Record<string, string>): void;
  increment(value?: number, labels?: Record<string, string>): void;
  decrement(value?: number, labels?: Record<string, string>): void;
  getValue(labels?: Record<string, string>): number;
}

export interface IHistogramInstrument extends IMetricInstrument {
  observe(value: number, labels?: Record<string, string>): void;
  getAggregation(labels?: Record<string, string>): HistogramAggregation;
}

export interface ITimerInstrument extends IMetricInstrument {
  record(durationMs: number, labels?: Record<string, string>): void;
  start(labels?: Record<string, string>): () => void;
  getAggregation(labels?: Record<string, string>): TimerAggregation;
}
