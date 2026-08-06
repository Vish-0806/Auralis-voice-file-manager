/**
 * Configuration Runtime Coordinator Implementation (Phase 16.3.4).
 *
 * Implements IConfigurationRuntime acting as central coordinator for configuration lifecycle,
 * source resolution, schema management, type conversion, constraint validation, profile management,
 * and feature flag evaluations.
 */

import {
  ConfigurationDiagnostics,
  ConfigurationEntry,
  ConfigurationHealth,
  ConfigurationProfileDefinition,
  ConfigurationProfileSnapshot,
  ConfigurationSchema,
  ConfigurationSnapshot,
  ConfigurationState,
  ConfigurationStatistics,
  ConfigurationValidationResult,
  FeatureEvaluation,
  FeatureFlag,
  FeatureHealth,
  FeatureStatistics,
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

  public registerProfile(profile: ConfigurationProfileDefinition): void {
    this._provider.registerProfile(profile);
  }

  public activateProfile(profileName: string): void {
    this._provider.activateProfile(profileName);
  }

  public getActiveProfile(): ConfigurationProfileDefinition | undefined {
    return this._provider.getActiveProfile();
  }

  public createProfileSnapshot(): ConfigurationProfileSnapshot {
    return this._provider.createProfileSnapshot();
  }

  public listProfiles(): ReadonlyArray<ConfigurationProfileDefinition> {
    return this._provider.listProfiles();
  }

  public registerFeature(feature: FeatureFlag): void {
    this._provider.registerFeature(feature);
  }

  public removeFeature(featureName: string): boolean {
    return this._provider.removeFeature(featureName);
  }

  public enableFeature(featureName: string): void {
    this._provider.enableFeature(featureName);
  }

  public disableFeature(featureName: string): void {
    this._provider.disableFeature(featureName);
  }

  public toggleFeature(featureName: string): boolean {
    return this._provider.toggleFeature(featureName);
  }

  public evaluateFeature(
    featureName: string,
    context?: { profileName?: string; environmentName?: string; userId?: string },
  ): FeatureEvaluation {
    return this._provider.evaluateFeature(featureName, context);
  }

  public listFeatures(): ReadonlyArray<FeatureFlag> {
    return this._provider.listFeatures();
  }

  public featureStatistics(): FeatureStatistics {
    return this._provider.featureStatistics();
  }

  public featureHealth(): FeatureHealth {
    return this._provider.featureHealth();
  }
}
