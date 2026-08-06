/**
 * Configuration Runtime Interfaces (Phase 16.3.3).
 *
 * Defines contracts for IConfigurationSource, IConfigurationValidator, IConfigurationProvider,
 * and IConfigurationRuntime including Schema, Resolution, and Validation APIs.
 */

import {
  ConfigurationCapabilities,
  ConfigurationConfiguration,
  ConfigurationContext,
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationSchema,
  ConfigurationSnapshot,
  ConfigurationSourceHealth,
  ConfigurationSourceStatistics,
  ConfigurationState,
  ConfigurationStatistics,
  ConfigurationValidationResult,
} from './models';

export interface IConfigurationSource {
  readonly name: string;
  readonly priority: number;
  readonly enabled: boolean;

  contains(key: string): boolean;
  get(key: string): unknown | undefined;
  set(key: string, value: unknown): boolean;
  remove(key: string): boolean;
  clear(): void;
  keys(): ReadonlyArray<string>;
  values(): ReadonlyArray<unknown>;
  items(): Readonly<Record<string, unknown>>;
  health(): ConfigurationSourceHealth;
  statistics(): ConfigurationSourceStatistics;
}

export interface IConfigurationValidator {
  validate(values: Record<string, unknown>, schema: ConfigurationSchema): ConfigurationValidationResult;
}

export interface IConfigurationProvider {
  initialize(): ConfigurationHealth;
  shutdown(): ConfigurationHealth;
  restart(): ConfigurationHealth;
  health(): ConfigurationHealth;
  statistics(): ConfigurationStatistics;
  capabilities(): ConfigurationCapabilities;
  diagnostics(): ConfigurationDiagnostics;
  state(): ConfigurationState;
  configuration(): ConfigurationConfiguration;
  context(): ConfigurationContext;

  registerSource(source: IConfigurationSource): void;
  unregisterSource(sourceName: string): boolean;
  get<T = unknown>(key: string, defaultValue?: T): T | undefined;
  has(key: string): boolean;
  getEntry(key: string): ConfigurationEntry | undefined;
  getAll(): Readonly<Record<string, unknown>>;
  createSnapshot(): ConfigurationSnapshot;
  listSources(): ReadonlyArray<IConfigurationSource>;

  registerSchema(schema: ConfigurationSchema): void;
  unregisterSchema(schemaName: string): boolean;
  getSchema(schemaName: string): ConfigurationSchema | undefined;
  listSchemas(): ReadonlyArray<ConfigurationSchema>;

  resolve<T = unknown>(key: string, targetType?: string, defaultValue?: T): T;
  resolveAll(): Readonly<Record<string, unknown>>;
  validate(schemaName?: string): ConfigurationValidationResult;
}

export interface IConfigurationRuntime {
  initialize(): ConfigurationHealth;
  shutdown(): ConfigurationHealth;
  restart(): ConfigurationHealth;
  provider(): IConfigurationProvider;
  health(): ConfigurationHealth;
  statistics(): ConfigurationStatistics;
  diagnostics(): ConfigurationDiagnostics;
  state(): ConfigurationState;

  registerSource(source: IConfigurationSource): void;
  unregisterSource(sourceName: string): boolean;
  get<T = unknown>(key: string, defaultValue?: T): T | undefined;
  has(key: string): boolean;
  getEntry(key: string): ConfigurationEntry | undefined;
  getAll(): Readonly<Record<string, unknown>>;
  createSnapshot(): ConfigurationSnapshot;
  listSources(): ReadonlyArray<IConfigurationSource>;

  registerSchema(schema: ConfigurationSchema): void;
  unregisterSchema(schemaName: string): boolean;
  getSchema(schemaName: string): ConfigurationSchema | undefined;
  listSchemas(): ReadonlyArray<ConfigurationSchema>;

  resolve<T = unknown>(key: string, targetType?: string, defaultValue?: T): T;
  resolveAll(): Readonly<Record<string, unknown>>;
  validate(schemaName?: string): ConfigurationValidationResult;
}
