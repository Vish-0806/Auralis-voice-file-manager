import { describe, it, expect } from 'vitest';
import {
  CounterMetric,
  GaugeMetric,
  HistogramMetric,
  TimerMetric,
  MetricType,
  MetricsValidationError
} from '../../../src/observability';

describe('Metrics Instruments Tests', () => {
  describe('Counter', () => {
    it('should increment monotonic values and reject negatives', () => {
      const def = { name: 'c', type: MetricType.COUNTER, labelKeys: [], enabled: true };
      const counter = new CounterMetric(def, () => {});

      expect(counter.getValue()).toBe(0);
      counter.increment(5);
      expect(counter.getValue()).toBe(5);

      expect(() => {
        counter.increment(-2);
      }).toThrow(MetricsValidationError);
    });
  });

  describe('Gauge', () => {
    it('should set, increment, and decrement values', () => {
      const def = { name: 'g', type: MetricType.GAUGE, labelKeys: [], enabled: true };
      const gauge = new GaugeMetric(def, () => {});

      expect(gauge.getValue()).toBe(0);
      gauge.set(10);
      expect(gauge.getValue()).toBe(10);

      gauge.increment(5);
      expect(gauge.getValue()).toBe(15);

      gauge.decrement(3);
      expect(gauge.getValue()).toBe(12);
    });

    it('should reject invalid values like NaN or Infinity', () => {
      const def = { name: 'g', type: MetricType.GAUGE, labelKeys: [], enabled: true };
      const gauge = new GaugeMetric(def, () => {});

      expect(() => {
        gauge.set(NaN);
      }).toThrow(MetricsValidationError);

      expect(() => {
        gauge.set(Infinity);
      }).toThrow(MetricsValidationError);
    });
  });

  describe('Histogram', () => {
    it('should update aggregations and reject unsorted buckets', () => {
      const def = { name: 'h', type: MetricType.HISTOGRAM, labelKeys: [], enabled: true };
      
      expect(() => {
        new HistogramMetric(def, () => {}, [50, 10]); // unsorted buckets
      }).toThrow(MetricsValidationError);

      const hist = new HistogramMetric(def, () => {}, [10, 50, 100]);
      hist.observe(5);
      hist.observe(20);
      hist.observe(200);

      const agg = hist.getAggregation();
      expect(agg.count).toBe(3);
      expect(agg.sum).toBe(225);
      expect(agg.min).toBe(5);
      expect(agg.max).toBe(200);
      expect(agg.average).toBe(75);

      expect(agg.buckets['10']).toBe(1); // 5 <= 10
      expect(agg.buckets['50']).toBe(2); // 5, 20 <= 50
      expect(agg.buckets['100']).toBe(2);
      expect(agg.buckets['+Inf']).toBe(3);
    });
  });

  describe('Timer', () => {
    it('should record timers and support start/stop scopes', async () => {
      const def = { name: 't', type: MetricType.TIMER, labelKeys: [], enabled: true };
      const timer = new TimerMetric(def, () => {});

      timer.record(150);
      expect(timer.getAggregation().count).toBe(1);
      expect(timer.getAggregation().sum).toBe(150);

      const stop = timer.start();
      await new Promise(resolve => setTimeout(resolve, 50));
      stop();

      const agg = timer.getAggregation();
      expect(agg.count).toBe(2);
      expect(agg.sum).toBeGreaterThanOrEqual(190);
    });
  });
});
