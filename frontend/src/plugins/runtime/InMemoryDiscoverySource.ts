import type { IPluginDiscoverySource } from '../interfaces/plugin-discovery';
import type { PluginDiscoverySourceDescriptor } from '../models/manifest';

export class InMemoryDiscoverySource implements IPluginDiscoverySource {
  constructor(
    public readonly descriptor: PluginDiscoverySourceDescriptor,
    private readonly candidates: ReadonlyArray<unknown> = []
  ) {}

  public async discover(): Promise<ReadonlyArray<unknown>> {
    // Return a deeply frozen snapshot copy of candidates to enforce immutability
    return this.freezeDeep([...this.candidates]);
  }

  private freezeDeep<T>(value: T): T {
    if (Array.isArray(value)) {
      const arrayValue = value.map((item) => this.freezeDeep(item));
      return Object.freeze(arrayValue) as T;
    }

    if (value && typeof value === 'object') {
      const objectValue = value as Record<string, unknown>;
      Object.keys(objectValue).forEach((key) => {
        const nestedValue = objectValue[key];
        if (nestedValue && typeof nestedValue === 'object') {
          objectValue[key] = this.freezeDeep(nestedValue);
        }
      });
      return Object.freeze(objectValue) as T;
    }

    return value;
  }
}
