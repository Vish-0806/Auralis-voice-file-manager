/**
 * Configuration Provider Implementation (Phase 16.3.3).
 *
 * Implements IConfigurationProvider owning configuration runtime state transitions,
 * telemetry statistics, health evaluation, context metadata, capabilities reporting,
 * source resolution delegation, schema management, type conversion, and constraint validation.
 */

import {
  ConfigurationCapabilities,
  ConfigurationConfiguration,
  ConfigurationContext,
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationRuntimeState,
  ConfigurationSchema,
  ConfigurationSnapshot,
  ConfigurationSourceRegistration,
  ConfigurationState,
  ConfigurationStatistics,
  ConfigurationValidationResult,
  createConfigurationCapabilities,
  createConfigurationConfiguration,
  createConfigurationContext,
  createConfigurationDiagnostics,
  createConfigurationHealth,
  createConfigurationSourceRegistration,
  createConfigurationState,
  createConfigurationStatistics,
  createConfigurationValidationResult,
} from './models';
import { IConfigurationProvider, IConfigurationSource } from './interfaces';
import { SourceRegistry } from './source_registry';
import { ConfigurationSourceManager } from './configuration_source_manager';
import { MemoryConfigurationSource } from './memory_source';
import { ConfigurationSchemaManager } from './configuration_schema';
import { ConfigurationResolver } from './configuration_resolver';
import { ConfigurationValidator } from './configuration_validator';

export class ConfigurationProvider implements IConfigurationProvider {
  private _runtimeState: ConfigurationRuntimeState = ConfigurationRuntimeState.UNINITIALIZED;
  private readonly _config: ConfigurationConfiguration;
  private readonly _capabilities: ConfigurationCapabilities;
  private readonly _context: ConfigurationContext;

  private readonly _registry: SourceRegistry;
  private readonly _sourceManager: ConfigurationSourceManager;
  private readonly _defaultMemorySource: MemoryConfigurationSource;

  private readonly _schemaManager: ConfigurationSchemaManager;
  private readonly _resolver: ConfigurationResolver;
  private readonly _validator: ConfigurationValidator;

  private _startedAt: string | null = null;
  private _initializations = 0;
  private _shutdowns = 0;
  private _restarts = 0;
  private _errors = 0;

  constructor(
    config?: ConfigurationConfiguration,
    capabilities?: ConfigurationCapabilities,
    context?: ConfigurationContext,
    registry?: SourceRegistry,
    schemaManager?: ConfigurationSchemaManager,
  ) {
    this._config = config ?? createConfigurationConfiguration();
    this._capabilities = capabilities ?? createConfigurationCapabilities();
    this._context = context ?? createConfigurationContext();

    this._registry = registry ?? new SourceRegistry();
    this._sourceManager = new ConfigurationSourceManager(this._registry);

    this._defaultMemorySource = new MemoryConfigurationSource();
    this._registry.register(this._defaultMemorySource);

    this._schemaManager = schemaManager ?? new ConfigurationSchemaManager();
    this._resolver = new ConfigurationResolver(this._sourceManager, this._schemaManager);
    this._validator = new ConfigurationValidator();
  }

  public initialize(): ConfigurationHealth {
    if (
      this._runtimeState === ConfigurationRuntimeState.INITIALIZING ||
      this._runtimeState === ConfigurationRuntimeState.READY
    ) {
      return this.health();
    }

    this._runtimeState = ConfigurationRuntimeState.INITIALIZING;
    this._runtimeState = ConfigurationRuntimeState.READY;
    this._startedAt = new Date().toISOString();
    this._initializations++;

    return this.health();
  }

  public shutdown(): ConfigurationHealth {
    if (this._runtimeState === ConfigurationRuntimeState.STOPPED) {
      return this.health();
    }

    this._runtimeState = ConfigurationRuntimeState.STOPPING;
    this._runtimeState = ConfigurationRuntimeState.STOPPED;
    this._startedAt = null;
    this._shutdowns++;

    return this.health();
  }

  public restart(): ConfigurationHealth {
    this._restarts++;
    this.shutdown();
    return this.initialize();
  }

  public health(): ConfigurationHealth {
    const healthy = this._runtimeState === ConfigurationRuntimeState.READY;
    const message = healthy
      ? 'Configuration runtime is ready and operational.'
      : `Configuration runtime is in state ${this._runtimeState}.`;

    return createConfigurationHealth({
      healthy,
      runtimeState: this._runtimeState,
      message,
    });
  }

  public statistics(): ConfigurationStatistics {
    const uptime =
      this._runtimeState === ConfigurationRuntimeState.READY && this._startedAt
        ? Math.max(0, Math.floor((Date.now() - new Date(this._startedAt).getTime()) / 1000))
        : 0;

    return createConfigurationStatistics({
      initializations: this._initializations,
      shutdowns: this._shutdowns,
      restarts: this._restarts,
      errors: this._errors,
      uptime,
    });
  }

  public capabilities(): ConfigurationCapabilities {
    return this._capabilities;
  }

  public diagnostics(): ConfigurationDiagnostics {
    const sourceRegs: ConfigurationSourceRegistration[] = this.listSources().map((s) =>
      createConfigurationSourceRegistration({
        sourceName: s.name,
        priority: s.priority,
        enabled: s.enabled,
      }),
    );

    const schemaNames = this.listSchemas().map((s) => s.schemaName);

    return createConfigurationDiagnostics({
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      sources: sourceRegs,
      snapshot: this.createSnapshot(),
      schemas: schemaNames,
      validationStats: this._validator.statistics(),
      resolutionStats: this._resolver.statistics(),
      timestamp: new Date().toISOString(),
    });
  }

  public state(): ConfigurationState {
    return createConfigurationState({
      runtimeState: this._runtimeState,
      initialized: this._runtimeState === ConfigurationRuntimeState.READY,
      startedAt: this._startedAt,
    });
  }

  public configuration(): ConfigurationConfiguration {
    return this._config;
  }

  public context(): ConfigurationContext {
    return this._context;
  }

  public registerSource(source: IConfigurationSource): void {
    this._registry.register(source);
  }

  public unregisterSource(sourceName: string): boolean {
    return this._registry.unregister(sourceName);
  }

  public get<T = unknown>(key: string, defaultValue?: T): T | undefined {
    return this._sourceManager.get<T>(key, defaultValue);
  }

  public has(key: string): boolean {
    return this._sourceManager.has(key);
  }

  public getEntry(key: string): ConfigurationEntry | undefined {
    return this._sourceManager.getEntry(key);
  }

  public getAll(): Readonly<Record<string, unknown>> {
    return this._sourceManager.getAll();
  }

  public createSnapshot(): ConfigurationSnapshot {
    return this._sourceManager.createSnapshot();
  }

  public listSources(): ReadonlyArray<IConfigurationSource> {
    return this._registry.listSources();
  }

  public registerSchema(schema: ConfigurationSchema): void {
    this._schemaManager.registerSchema(schema);
  }

  public unregisterSchema(schemaName: string): boolean {
    return this._schemaManager.unregisterSchema(schemaName);
  }

  public getSchema(schemaName: string): ConfigurationSchema | undefined {
    return this._schemaManager.getSchema(schemaName);
  }

  public listSchemas(): ReadonlyArray<ConfigurationSchema> {
    return this._schemaManager.listSchemas();
  }

  public resolve<T = unknown>(key: string, targetType?: string, defaultValue?: T): T {
    return this._resolver.resolve<T>(key, targetType, defaultValue);
  }

  public resolveAll(): Readonly<Record<string, unknown>> {
    return this._resolver.resolveAll();
  }

  public validate(schemaName?: string): ConfigurationValidationResult {
    const values = this.getAll();

    if (schemaName) {
      const schema = this._schemaManager.getSchema(schemaName);
      if (!schema) {
        return createConfigurationValidationResult({ valid: true });
      }
      return this._validator.validate(values, schema);
    }

    const schemas = this._schemaManager.listSchemas();
    let combinedValid = true;
    const combinedErrors: any[] = [];
    const combinedWarnings: any[] = [];

    for (const s of schemas) {
      const res = this._validator.validate(values, s);
      if (!res.valid) combinedValid = false;
      combinedErrors.push(...res.errors);
      combinedWarnings.push(...res.warnings);
    }

    return createConfigurationValidationResult({
      valid: combinedValid,
      errors: combinedErrors,
      warnings: combinedWarnings,
      timestamp: new Date().toISOString(),
    });
  }
}
