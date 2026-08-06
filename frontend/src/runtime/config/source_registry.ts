/**
 * Source Registry Implementation (Phase 16.3.2).
 *
 * Manages registration, unregistration, duplicate validation, and priority-sorted retrieval
 * of configuration sources.
 */

import { ConfigurationProviderException } from './exceptions';
import { IConfigurationSource } from './interfaces';

export class SourceRegistry {
  private readonly _sources = new Map<string, IConfigurationSource>();

  public register(source: IConfigurationSource): void {
    if (!source) {
      throw new ConfigurationProviderException('Configuration source cannot be null or undefined.');
    }
    const name = source.name.trim();
    if (!name) {
      throw new ConfigurationProviderException('Configuration source name cannot be empty.');
    }
    if (this._sources.has(name)) {
      throw new ConfigurationProviderException(`Configuration source '${name}' is already registered.`);
    }

    this._sources.set(name, source);
  }

  public unregister(name: string): boolean {
    const key = name.trim();
    return this._sources.delete(key);
  }

  public get(name: string): IConfigurationSource | undefined {
    const key = name.trim();
    return this._sources.get(key);
  }

  public listSources(): ReadonlyArray<IConfigurationSource> {
    const list = Array.from(this._sources.values());
    list.sort((a, b) => b.priority - a.priority);
    return Object.freeze(list);
  }

  public clear(): void {
    this._sources.clear();
  }
}
