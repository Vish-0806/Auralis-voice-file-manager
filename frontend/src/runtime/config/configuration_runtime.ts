/**
 * Configuration Runtime Coordinator Implementation (Phase 16.3.3).
 *
 * Implements IConfigurationRuntime acting as central coordinator for configuration lifecycle,
 * source resolution, schema registration, type conversion, and constraint validation operations.
 */

import {
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationSchema,
  ConfigurationSnapshot,
  ConfigurationState,
  ConfigurationStatistics,
  ConfigurationValidationResult,
} from './models';
import { IConfigurationProvider, IConfigurationRuntime, IConfigurationSource } from './interfaces';
import { ConfigurationProvider } from './configuration_provider';

export class ConfigurationRuntime implements IConfigurationRuntime {
  private readonly _provider: IConfigurationProvider;

  constructor(provider?: IConfigurationProvider) {
    this._provider = provider ?? new ConfigurationProvider();
  }

  public initialize(): ConfigurationHealth {
    return this._provider.initialize();
  }

  public shutdown(): ConfigurationHealth {
    return this._provider.shutdown();
  }

  public restart(): ConfigurationHealth {
    return this._provider.restart();
  }

  public provider(): IConfigurationProvider {
    return this._provider;
  }

  public health(): ConfigurationHealth {
    return this._provider.health();
  }

  public statistics(): ConfigurationStatistics {
    return this._provider.statistics();
  }

  public diagnostics(): ConfigurationDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): ConfigurationState {
    return this._provider.state();
  }

  public registerSource(source: IConfigurationSource): void {
    this._provider.registerSource(source);
  }

  public unregisterSource(sourceName: string): boolean {
    return this._provider.unregisterSource(sourceName);
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    return this._provider.get<T>(key, defaultValue);
  }

  public has(key: string): boolean {
    return this._provider.has(key);
  }

  public getEntry(key: string): ConfigurationEntry | undefined {
    return this._provider.getEntry(key);
  }

  public getAll(): Readonly<Record<string, unknown>> {
    return this._provider.getAll();
  }

  public createSnapshot(): ConfigurationSnapshot {
    return this._provider.createSnapshot();
  }

  public listSources(): ReadonlyArray<IConfigurationSource> {
    return this._provider.listSources();
  }

  public registerSchema(schema: ConfigurationSchema): void {
    this._provider.registerSchema(schema);
  }

  public unregisterSchema(schemaName: string): boolean {
    return this._provider.unregisterSchema(schemaName);
  }

  public getSchema(schemaName: string): ConfigurationSchema | undefined {
    return this._provider.getSchema(schemaName);
  }

  public listSchemas(): ReadonlyArray<ConfigurationSchema> {
    return this._provider.listSchemas();
  }

  public resolve<T = unknown>(key: string, targetType?: string, defaultValue?: T): T {
    return this._provider.resolve<T>(key, targetType, defaultValue);
  }

  public resolveAll(): Readonly<Record<string, unknown>> {
    return this._provider.resolveAll();
  }

  public validate(schemaName?: string): ConfigurationValidationResult {
    return this._provider.validate(schemaName);
  }
}
