import { PluginDuplicateError, PluginDiscoveryError } from '../errors/PluginErrors';
import type { IPluginDiscoveryManager, IPluginDiscoverySource } from '../interfaces/plugin-discovery';
import type {
  PluginManifest,
  PluginDiscoveryResult,
  PluginDiscoveryStatistics,
  PluginDiscoveryHealth,
  PluginManifestValidationIssue
} from '../models/manifest';
import { PluginManifestValidator } from './PluginManifestValidator';

export class PluginDiscoveryManager implements IPluginDiscoveryManager {
  private readonly sources = new Map<string, IPluginDiscoverySource>();
  private readonly manifests = new Map<string, PluginManifest>();

  private discoveryAttemptsCount = 0;
  private discoveredPluginsCount = 0;
  private validManifestsCount = 0;
  private invalidManifestsCount = 0;
  private duplicateAttemptsCount = 0;
  private discoveryFailuresCount = 0;
  private validationFailuresCount = 0;

  public registerSource(source: IPluginDiscoverySource): void {
    if (!source || !source.descriptor || !source.descriptor.id) {
      throw new PluginDiscoveryError('Invalid discovery source');
    }
    this.sources.set(source.descriptor.id, source);
  }

  public unregisterSource(sourceId: string): void {
    if (!this.sources.has(sourceId)) {
      throw new PluginDiscoveryError(`Source '${sourceId}' is not registered`);
    }
    this.sources.delete(sourceId);
  }

  public getSources(): ReadonlyArray<IPluginDiscoverySource> {
    return Object.freeze(Array.from(this.sources.values()));
  }

  public async discover(): Promise<PluginDiscoveryResult> {
    this.discoveryAttemptsCount += 1;
    const newManifests: PluginManifest[] = [];
    const invalid: Array<{
      readonly sourceId: string;
      readonly error: string;
      readonly issues?: ReadonlyArray<PluginManifestValidationIssue>;
    }> = [];
    const duplicates: string[] = [];
    const failures: Array<{
      readonly sourceId: string;
      readonly error: string;
    }> = [];

    for (const source of this.sources.values()) {
      try {
        const candidates = await source.discover();
        this.discoveredPluginsCount += candidates.length;

        for (const candidate of candidates) {
          try {
            const manifest = PluginManifestValidator.parse(candidate);

            if (this.manifests.has(manifest.id) || newManifests.some(m => m.id === manifest.id)) {
              this.duplicateAttemptsCount += 1;
              duplicates.push(manifest.id);
              throw new PluginDuplicateError(`Duplicate plugin ID detected: '${manifest.id}'`);
            }

            // Register
            this.manifests.set(manifest.id, manifest);
            newManifests.push(manifest);
            this.validManifestsCount += 1;
          } catch (err: any) {
            if (err instanceof PluginDuplicateError) {
              throw err;
            }
            this.invalidManifestsCount += 1;
            this.validationFailuresCount += 1;
            const validation = PluginManifestValidator.validate(candidate);
            invalid.push({
              sourceId: source.descriptor.id,
              error: err.message || 'Manifest validation failed',
              issues: validation.issues
            });
          }
        }
      } catch (err: any) {
        if (err instanceof PluginDuplicateError) {
          // Re-throw duplicate errors immediately as required by duplicate handling
          throw err;
        }
        this.discoveryFailuresCount += 1;
        failures.push({
          sourceId: source.descriptor.id,
          error: err.message || 'Discovery failure'
        });
      }
    }

    const success = failures.length === 0 && invalid.length === 0 && duplicates.length === 0;

    return this.freezeDeep({
      success,
      manifests: newManifests,
      invalid,
      duplicates,
      failures
    });
  }

  public async discoverFromSource(sourceId: string): Promise<PluginDiscoveryResult> {
    const source = this.sources.get(sourceId);
    if (!source) {
      this.discoveryFailuresCount += 1;
      throw new PluginDiscoveryError(`Discovery source '${sourceId}' is not registered`);
    }

    this.discoveryAttemptsCount += 1;
    const newManifests: PluginManifest[] = [];
    const invalid: Array<{
      readonly sourceId: string;
      readonly error: string;
      readonly issues?: ReadonlyArray<PluginManifestValidationIssue>;
    }> = [];
    const duplicates: string[] = [];
    const failures: Array<{
      readonly sourceId: string;
      readonly error: string;
    }> = [];

    try {
      const candidates = await source.discover();
      this.discoveredPluginsCount += candidates.length;

      for (const candidate of candidates) {
        try {
          const manifest = PluginManifestValidator.parse(candidate);

          if (this.manifests.has(manifest.id) || newManifests.some(m => m.id === manifest.id)) {
            this.duplicateAttemptsCount += 1;
            duplicates.push(manifest.id);
            throw new PluginDuplicateError(`Duplicate plugin ID detected: '${manifest.id}'`);
          }

          this.manifests.set(manifest.id, manifest);
          newManifests.push(manifest);
          this.validManifestsCount += 1;
        } catch (err: any) {
          if (err instanceof PluginDuplicateError) {
            throw err;
          }
          this.invalidManifestsCount += 1;
          this.validationFailuresCount += 1;
          const validation = PluginManifestValidator.validate(candidate);
          invalid.push({
            sourceId,
            error: err.message || 'Manifest validation failed',
            issues: validation.issues
          });
        }
      }
    } catch (err: any) {
      if (err instanceof PluginDuplicateError) {
        throw err;
      }
      this.discoveryFailuresCount += 1;
      failures.push({
        sourceId,
        error: err.message || 'Discovery failure'
      });
    }

    const success = failures.length === 0 && invalid.length === 0 && duplicates.length === 0;

    return this.freezeDeep({
      success,
      manifests: newManifests,
      invalid,
      duplicates,
      failures
    });
  }

  public find(pluginId: string): PluginManifest | null {
    const manifest = this.manifests.get(pluginId);
    return manifest ? this.freezeDeep({ ...manifest }) : null;
  }

  public findAll(): ReadonlyArray<PluginManifest> {
    const list = Array.from(this.manifests.values());
    return this.freezeDeep(list);
  }

  public contains(pluginId: string): boolean {
    return this.manifests.has(pluginId);
  }

  public remove(pluginId: string): boolean {
    return this.manifests.delete(pluginId);
  }

  public clear(): void {
    this.manifests.clear();
  }

  public statistics(): PluginDiscoveryStatistics {
    return Object.freeze({
      discoveryAttempts: this.discoveryAttemptsCount,
      discoveredPlugins: this.discoveredPluginsCount,
      validManifests: this.validManifestsCount,
      invalidManifests: this.invalidManifestsCount,
      duplicateAttempts: this.duplicateAttemptsCount,
      discoveryFailures: this.discoveryFailuresCount,
      validationFailures: this.validationFailuresCount,
      registeredSources: this.sources.size
    });
  }

  public health(): PluginDiscoveryHealth {
    const issues: string[] = [];
    if (this.sources.size === 0) {
      issues.push('No discovery sources registered');
    }
    if (this.discoveryFailuresCount > 0) {
      issues.push(`${this.discoveryFailuresCount} discovery source failure(s) occurred`);
    }
    if (this.validationFailuresCount > 0) {
      issues.push(`${this.validationFailuresCount} manifest validation failure(s) occurred`);
    }
    if (this.duplicateAttemptsCount > 0) {
      issues.push(`${this.duplicateAttemptsCount} duplicate plugin registration attempt(s) occurred`);
    }

    return Object.freeze({
      healthy: issues.length === 0,
      message: issues.length === 0 ? 'Discovery engine healthy' : `Discovery engine unhealthy: ${issues.join(', ')}`,
      issues: Object.freeze(issues)
    });
  }

  public reset(): void {
    this.manifests.clear();
    this.sources.clear();
    this.discoveryAttemptsCount = 0;
    this.discoveredPluginsCount = 0;
    this.validManifestsCount = 0;
    this.invalidManifestsCount = 0;
    this.duplicateAttemptsCount = 0;
    this.discoveryFailuresCount = 0;
    this.validationFailuresCount = 0;
  }

  private freezeDeep<T>(value: T): T {
    if (Object.isFrozen(value)) {
      return value;
    }

    if (Array.isArray(value)) {
      const arrayValue = value.map((item) => this.freezeDeep(item));
      return Object.freeze(arrayValue) as T;
    }

    if (value && typeof value === 'object') {
      const objectValue = value as Record<string, unknown>;
      const copy: Record<string, unknown> = {};
      Object.keys(objectValue).forEach((key) => {
        copy[key] = this.freezeDeep(objectValue[key]);
      });
      return Object.freeze(copy) as unknown as T;
    }

    return value;
  }
}
