import type { IMetricInstrument } from '../interfaces/metric-instrument';
import type { MetricDefinition } from '../models/metric';
import { MetricAlreadyExistsError, MetricNotFoundError, MetricsValidationError } from '../errors/MetricsErrors';
import { validateMetricName } from '../factories/metricsFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class MetricsRegistry {
  private readonly instruments = new Map<string, IMetricInstrument>();

  public register(instrument: IMetricInstrument): void {
    const def = instrument.getDefinition();
    validateMetricName(def.name);

    if (this.instruments.has(def.name)) {
      throw new MetricAlreadyExistsError(`Metric with name '${def.name}' is already registered.`, def.name);
    }
    
    if (def.labelKeys && !Array.isArray(def.labelKeys)) {
      throw new MetricsValidationError('Metric labelKeys must be an array of strings.');
    }
    if (def.labelKeys) {
      for (const key of def.labelKeys) {
        if (!key || typeof key !== 'string' || !key.trim()) {
          throw new MetricsValidationError('Metric label key must be a non-empty string.');
        }
      }
    }

    this.instruments.set(def.name, instrument);
  }

  public unregister(name: string): void {
    if (!name || !name.trim()) {
      throw new MetricsValidationError('Metric name cannot be empty.');
    }
    const trimmed = name.trim();
    if (!this.instruments.has(trimmed)) {
      throw new MetricNotFoundError(`Metric with name '${trimmed}' not found.`, trimmed);
    }
    this.instruments.delete(trimmed);
  }

  public get(name: string): IMetricInstrument {
    if (!name || !name.trim()) {
      throw new MetricsValidationError('Metric name cannot be empty.');
    }
    const trimmed = name.trim();
    const inst = this.instruments.get(trimmed);
    if (!inst) {
      throw new MetricNotFoundError(`Metric with name '${trimmed}' not found.`, trimmed);
    }
    return inst;
  }

  public has(name: string): boolean {
    if (!name) return false;
    return this.instruments.has(name.trim());
  }

  public list(): ReadonlyArray<MetricDefinition> {
    const list = Array.from(this.instruments.values()).map(inst => inst.getDefinition());
    list.sort((a, b) => a.name.localeCompare(b.name));
    return freezeDeepSafe(list) as ReadonlyArray<MetricDefinition>;
  }

  public listInstruments(): ReadonlyArray<IMetricInstrument> {
    const list = Array.from(this.instruments.values());
    list.sort((a, b) => a.getDefinition().name.localeCompare(b.getDefinition().name));
    return Object.freeze(list);
  }

  public clear(): void {
    this.instruments.clear();
  }

  public getMetricCount(): number {
    return this.instruments.size;
  }
}
