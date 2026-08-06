/**
 * Configuration Schema Manager (Phase 16.3.3).
 *
 * Manages schema registration, unregistration, duplicate validation, definition lookup,
 * and schema inventory reporting.
 */

import { ConfigurationDefinition, ConfigurationSchema } from './models';
import { ConfigurationProviderException } from './exceptions';

export class ConfigurationSchemaManager {
  private readonly _schemas = new Map<string, ConfigurationSchema>();

  public registerSchema(schema: ConfigurationSchema): void {
    if (!schema) {
      throw new ConfigurationProviderException('Configuration schema cannot be null or undefined.');
    }
    const name = schema.schemaName.trim();
    if (!name) {
      throw new ConfigurationProviderException('Schema name cannot be empty.');
    }
    if (this._schemas.has(name)) {
      throw new ConfigurationProviderException(`Configuration schema '${name}' is already registered.`);
    }

    this._schemas.set(name, schema);
  }

  public unregisterSchema(schemaName: string): boolean {
    const key = schemaName.trim();
    return this._schemas.delete(key);
  }

  public getSchema(schemaName: string): ConfigurationSchema | undefined {
    const key = schemaName.trim();
    return this._schemas.get(key);
  }

  public contains(schemaName: string): boolean {
    const key = schemaName.trim();
    return this._schemas.has(key);
  }

  public getDefinition(key: string): ConfigurationDefinition | undefined {
    const k = key.trim();
    for (const schema of Array.from(this._schemas.values())) {
      if (schema.definitions && schema.definitions[k]) {
        return schema.definitions[k];
      }
    }
    return undefined;
  }

  public listSchemas(): ReadonlyArray<ConfigurationSchema> {
    return Object.freeze(Array.from(this._schemas.values()));
  }

  public clear(): void {
    this._schemas.clear();
  }
}
