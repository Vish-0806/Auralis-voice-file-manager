/**
 * Configuration Resolver & Automatic Type Converter (Phase 16.3.3).
 *
 * Implements type conversion (string, number, boolean, date, array, set, map, enum, object),
 * fallback default resolution, schema definition lookup, and resolution metrics tracking.
 */

import { createResolutionStatistics, ResolutionStatistics } from './models';
import { ConfigurationValidationException } from './exceptions';
import { ConfigurationSourceManager } from './configuration_source_manager';
import { ConfigurationSchemaManager } from './configuration_schema';

export class ConfigurationResolver {
  private readonly _sourceManager: ConfigurationSourceManager;
  private readonly _schemaManager: ConfigurationSchemaManager;

  private _resolutions = 0;
  private _conversions = 0;
  private _defaultFallbacks = 0;
  private _failedResolutions = 0;

  constructor(
    sourceManager: ConfigurationSourceManager,
    schemaManager: ConfigurationSchemaManager,
  ) {
    this._sourceManager = sourceManager;
    this._schemaManager = schemaManager;
  }

  public resolve<T = unknown>(key: string, targetType?: string, defaultValue?: T): T {
    const k = key.trim();
    this._resolutions++;

    const rawValue = this._sourceManager.get(k);
    const definition = this._schemaManager.getDefinition(k);

    const expectedType = (targetType ?? definition?.expectedType ?? (typeof rawValue)).toLowerCase();
    const fallback = defaultValue !== undefined ? defaultValue : (definition?.defaultValue as T);

    if (rawValue === undefined || rawValue === null) {
      if (fallback !== undefined) {
        this._defaultFallbacks++;
        return fallback;
      }
      if (definition?.required) {
        this._failedResolutions++;
        throw new ConfigurationValidationException(`Configuration key '${k}' is required but not provided.`);
      }
      return undefined as unknown as T;
    }

    return this.convertType<T>(k, rawValue, expectedType);
  }

  public resolveAll(): Readonly<Record<string, unknown>> {
    const allRaw = this._sourceManager.getAll();
    const resolved: Record<string, unknown> = {};

    for (const key of Object.keys(allRaw)) {
      resolved[key] = this.resolve(key);
    }

    return Object.freeze(resolved);
  }

  public statistics(): ResolutionStatistics {
    return createResolutionStatistics({
      resolutions: this._resolutions,
      conversions: this._conversions,
      defaultFallbacks: this._defaultFallbacks,
      failedResolutions: this._failedResolutions,
    });
  }

  private convertType<T>(key: string, rawValue: unknown, expectedType: string): T {
    if (expectedType === 'string') {
      if (typeof rawValue === 'string') return rawValue as unknown as T;
      this._conversions++;
      return String(rawValue) as unknown as T;
    }

    if (expectedType === 'number') {
      if (typeof rawValue === 'number' && !isNaN(rawValue)) {
        return rawValue as unknown as T;
      }
      const parsed = Number(rawValue);
      if (isNaN(parsed)) {
        this._failedResolutions++;
        throw new ConfigurationValidationException(`Cannot convert value '${String(rawValue)}' to number for key '${key}'.`);
      }
      this._conversions++;
      return parsed as unknown as T;
    }

    if (expectedType === 'boolean') {
      if (typeof rawValue === 'boolean') return rawValue as unknown as T;
      const str = String(rawValue).toLowerCase().trim();
      if (str === 'true' || str === '1' || str === 'yes') {
        this._conversions++;
        return true as unknown as T;
      }
      if (str === 'false' || str === '0' || str === 'no') {
        this._conversions++;
        return false as unknown as T;
      }
      this._failedResolutions++;
      throw new ConfigurationValidationException(`Cannot convert value '${String(rawValue)}' to boolean for key '${key}'.`);
    }

    if (expectedType === 'date') {
      if (rawValue instanceof Date && !isNaN(rawValue.getTime())) {
        return rawValue as unknown as T;
      }
      const date = new Date(rawValue as any);
      if (isNaN(date.getTime())) {
        this._failedResolutions++;
        throw new ConfigurationValidationException(`Cannot convert value '${String(rawValue)}' to Date for key '${key}'.`);
      }
      this._conversions++;
      return date as unknown as T;
    }

    if (expectedType === 'array') {
      if (Array.isArray(rawValue)) return rawValue as unknown as T;
      if (typeof rawValue === 'string') {
        this._conversions++;
        return rawValue.split(',').map((s) => s.trim()) as unknown as T;
      }
      return [rawValue] as unknown as T;
    }

    if (expectedType === 'set') {
      if (rawValue instanceof Set) return rawValue as unknown as T;
      if (Array.isArray(rawValue)) {
        this._conversions++;
        return new Set(rawValue) as unknown as T;
      }
      if (typeof rawValue === 'string') {
        this._conversions++;
        return new Set(rawValue.split(',').map((s) => s.trim())) as unknown as T;
      }
    }

    if (expectedType === 'map') {
      if (rawValue instanceof Map) return rawValue as unknown as T;
      if (typeof rawValue === 'object' && rawValue !== null) {
        this._conversions++;
        return new Map(Object.entries(rawValue)) as unknown as T;
      }
    }

    return rawValue as T;
  }
}
