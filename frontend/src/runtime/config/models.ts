/**
 * Configuration Runtime Domain Models (Phase 16.3.6).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, diagnostics
 * telemetry, source priority enums, entry records, snapshots, schemas, validation results,
 * resolution results, configuration profile definitions, feature flag evaluation models,
 * sensitive value configuration management models, and production certification models for the Frontend Configuration Runtime.
 */

export enum ConfigurationRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export enum ConfigurationSourcePriority {
  SENSITIVE = 700,
  PROFILE = 600,
  MEMORY = 500,
  RUNTIME = 400,
  ENVIRONMENT = 300,
  LOCAL = 200,
  SESSION = 100,
  DEFAULT = 0,
}

export enum SensitiveValueType {
  PASSWORD = 'PASSWORD',
  TOKEN = 'TOKEN',
  API_KEY = 'API_KEY',
  CERTIFICATE = 'CERTIFICATE',
  PRIVATE_KEY = 'PRIVATE_KEY',
  CONNECTION_STRING = 'CONNECTION_STRING',
  CUSTOM = 'CUSTOM',
}

export interface ConfigurationState {
  readonly runtimeState: ConfigurationRuntimeState;
  readonly initialized: boolean;
  readonly startedAt: string | null;
}

export interface ConfigurationCapabilities {
  readonly supportsProfiles: boolean;
  readonly supportsSources: boolean;
  readonly supportsValidation: boolean;
  readonly supportsSecrets: boolean;
  readonly supportsFeatureFlags: boolean;
  readonly supportsDiagnostics: boolean;
}

export interface ConfigurationHealth {
  readonly healthy: boolean;
  readonly runtimeState: ConfigurationRuntimeState;
  readonly message: string;
}

export interface ConfigurationStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface ConfigurationContext {
  readonly runtimeId: string;
  readonly createdAt: string;
  readonly environment: string;
}

export interface ConfigurationConfiguration {
  readonly runtimeName: string;
  readonly version: string;
  readonly strictMode: boolean;
}

export interface ConfigurationEntry {
  readonly key: string;
  readonly value: unknown;
  readonly sourceName: string;
  readonly priority: number;
  readonly timestamp: string;
}

export interface ConfigurationSnapshot {
  readonly entries: Readonly<Record<string, ConfigurationEntry>>;
  readonly mergedValues: Readonly<Record<string, unknown>>;
  readonly timestamp: string;
  readonly sourceCount: number;
}

export interface ConfigurationSourceStatistics {
  readonly reads: number;
  readonly writes: number;
  readonly deletes: number;
  readonly hits: number;
  readonly misses: number;
  readonly itemCount: number;
}

export interface ConfigurationSourceHealth {
  readonly healthy: boolean;
  readonly sourceName: string;
  readonly enabled: boolean;
  readonly message: string;
}

export interface ConfigurationSourceRegistration {
  readonly sourceName: string;
  readonly priority: number;
  readonly enabled: boolean;
  readonly registeredAt: string;
}

export interface ConfigurationConstraint {
  readonly minValue?: number;
  readonly maxValue?: number;
  readonly minLength?: number;
  readonly maxLength?: number;
  readonly regexPattern?: string;
  readonly allowedValues?: ReadonlyArray<unknown>;
}

export interface ConfigurationDefinition {
  readonly key: string;
  readonly expectedType: string;
  readonly defaultValue?: unknown;
  readonly required: boolean;
  readonly constraint?: ConfigurationConstraint;
  readonly description?: string;
}

export interface ConfigurationSchema {
  readonly schemaName: string;
  readonly definitions: Readonly<Record<string, ConfigurationDefinition>>;
}

export interface ConfigurationError {
  readonly key: string;
  readonly message: string;
  readonly code: string;
}

export interface ConfigurationWarning {
  readonly key: string;
  readonly message: string;
  readonly code: string;
}

export interface ConfigurationValidationResult {
  readonly valid: boolean;
  readonly errors: ReadonlyArray<ConfigurationError>;
  readonly warnings: ReadonlyArray<ConfigurationWarning>;
  readonly timestamp: string;
}

export interface ConfigurationResolutionResult<T = unknown> {
  readonly key: string;
  readonly value: T;
  readonly converted: boolean;
  readonly sourceName?: string;
  readonly timestamp: string;
}

export interface ValidationStatistics {
  readonly validations: number;
  readonly passedValidations: number;
  readonly failedValidations: number;
  readonly totalErrors: number;
  readonly totalWarnings: number;
}

export interface ResolutionStatistics {
  readonly resolutions: number;
  readonly conversions: number;
  readonly defaultFallbacks: number;
  readonly failedResolutions: number;
}

export interface FeatureFlag {
  readonly featureName: string;
  readonly enabled: boolean;
  readonly description?: string;
  readonly rolloutPercentage?: number;
  readonly allowedProfiles?: ReadonlyArray<string>;
  readonly allowedEnvironments?: ReadonlyArray<string>;
  readonly dependencies?: ReadonlyArray<string>;
}

export interface FeatureEvaluation {
  readonly featureName: string;
  readonly enabled: boolean;
  readonly reason: string;
  readonly profileName?: string;
  readonly environmentName?: string;
  readonly evaluatedAt: string;
}

export interface FeatureStatistics {
  readonly evaluations: number;
  readonly enabledEvaluations: number;
  readonly disabledEvaluations: number;
  readonly cachedEvaluations: number;
}

export interface FeatureHealth {
  readonly healthy: boolean;
  readonly totalFeatures: number;
  readonly enabledFeatures: number;
  readonly disabledFeatures: number;
}

export interface ConfigurationProfileDefinition {
  readonly profileType: string;
  readonly profileName: string;
  readonly parentProfileName?: string;
  readonly overrides: Readonly<Record<string, unknown>>;
  readonly active: boolean;
  readonly priority: number;
}

export interface ConfigurationProfileSnapshot {
  readonly activeProfileName: string;
  readonly mergedOverrides: Readonly<Record<string, unknown>>;
  readonly registeredProfiles: ReadonlyArray<string>;
  readonly timestamp: string;
}

export interface ProfileStatistics {
  readonly registrations: number;
  readonly activations: number;
  readonly overrideKeysCount: number;
}

export interface ProfileHealth {
  readonly healthy: boolean;
  readonly activeProfileName: string;
  readonly totalProfiles: number;
}

export interface SensitiveValuePolicy {
  readonly allowRead: boolean;
  readonly allowWrite: boolean;
  readonly allowExport: boolean;
  readonly allowLogging: boolean;
  readonly allowRedaction: boolean;
}

export interface SensitiveConfiguration {
  readonly key: string;
  readonly rawValue: unknown;
  readonly sensitiveType: SensitiveValueType;
  readonly policy: SensitiveValuePolicy;
  readonly registeredAt: string;
}

export interface SensitiveConfigurationReference {
  readonly key: string;
  readonly sensitiveType: SensitiveValueType;
  readonly redactedValue: string;
  readonly registeredAt: string;
}

export interface SensitiveConfigurationSnapshot {
  readonly references: ReadonlyArray<SensitiveConfigurationReference>;
  readonly sensitiveCount: number;
  readonly timestamp: string;
}

export interface SensitiveAccessRecord {
  readonly key: string;
  readonly action: 'REGISTER' | 'READ' | 'REDACT' | 'UPDATE' | 'REMOVE';
  readonly success: boolean;
  readonly reason?: string;
  readonly timestamp: string;
}

export interface SensitiveStatistics {
  readonly totalValues: number;
  readonly reads: number;
  readonly redactions: number;
  readonly blockedAccesses: number;
  readonly auditRecordsCount: number;
}

export interface SensitiveHealth {
  readonly healthy: boolean;
  readonly totalValues: number;
}

export interface CertificationIssue {
  readonly severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  readonly component: string;
  readonly message: string;
  readonly remediation?: string;
}

export interface ConfigurationCertification {
  readonly certified: boolean;
  readonly score: number;
  readonly environment: string;
  readonly issues: ReadonlyArray<CertificationIssue>;
  readonly certifiedAt: string;
}

export interface ConfigurationCertificationSummary {
  readonly certified: boolean;
  readonly score: number;
  readonly totalChecks: number;
  readonly passedChecks: number;
  readonly failedChecks: number;
  readonly warningChecks: number;
}

export interface CertificationStatistics {
  readonly certificationsRun: number;
  readonly passedCertifications: number;
  readonly failedCertifications: number;
  readonly averageScore: number;
}

export interface CertificationHealth {
  readonly healthy: boolean;
  readonly lastCertificationScore: number;
  readonly statusMessage: string;
}

export interface CertificationReport {
  readonly certification: ConfigurationCertification;
  readonly summary: ConfigurationCertificationSummary;
  readonly diagnostics: ConfigurationDiagnostics;
  readonly benchmarkMs: number;
  readonly generatedAt: string;
}

export interface ConfigurationDiagnostics {
  readonly health: ConfigurationHealth;
  readonly statistics: ConfigurationStatistics;
  readonly capabilities: ConfigurationCapabilities;
  readonly context: ConfigurationContext;
  readonly sources?: ReadonlyArray<ConfigurationSourceRegistration>;
  readonly snapshot?: ConfigurationSnapshot;
  readonly schemas?: ReadonlyArray<string>;
  readonly validationStats?: ValidationStatistics;
  readonly resolutionStats?: ResolutionStatistics;
  readonly activeProfile?: string;
  readonly profilesSnapshot?: ConfigurationProfileSnapshot;
  readonly profileStats?: ProfileStatistics;
  readonly featureStats?: FeatureStatistics;
  readonly featureHealth?: FeatureHealth;
  readonly sensitiveSnapshot?: SensitiveConfigurationSnapshot;
  readonly sensitiveStats?: SensitiveStatistics;
  readonly sensitiveHealth?: SensitiveHealth;
  readonly certification?: ConfigurationCertification;
  readonly certificationSummary?: ConfigurationCertificationSummary;
  readonly timestamp: string;
}

export function createConfigurationState(
  params: Partial<ConfigurationState> = {},
): ConfigurationState {
  return Object.freeze({
    runtimeState: params.runtimeState ?? ConfigurationRuntimeState.UNINITIALIZED,
    initialized: params.initialized ?? false,
    startedAt: params.startedAt ?? null,
  });
}

export function createConfigurationCapabilities(
  params: Partial<ConfigurationCapabilities> = {},
): ConfigurationCapabilities {
  return Object.freeze({
    supportsProfiles: params.supportsProfiles ?? true,
    supportsSources: params.supportsSources ?? true,
    supportsValidation: params.supportsValidation ?? true,
    supportsSecrets: params.supportsSecrets ?? true,
    supportsFeatureFlags: params.supportsFeatureFlags ?? true,
    supportsDiagnostics: params.supportsDiagnostics ?? true,
  });
}

export function createConfigurationHealth(
  params: Partial<ConfigurationHealth> = {},
): ConfigurationHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    runtimeState: params.runtimeState ?? ConfigurationRuntimeState.UNINITIALIZED,
    message: params.message ?? 'Configuration runtime is uninitialized.',
  });
}

export function createConfigurationStatistics(
  params: Partial<ConfigurationStatistics> = {},
): ConfigurationStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    errors: params.errors ?? 0,
    uptime: params.uptime ?? 0,
  });
}

export function createConfigurationContext(
  params: Partial<ConfigurationContext> = {},
): ConfigurationContext {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `config_runtime_${Date.now()}`,
    createdAt: params.createdAt ?? new Date().toISOString(),
    environment: params.environment ?? 'production',
  });
}

export function createConfigurationConfiguration(
  params: Partial<ConfigurationConfiguration> = {},
): ConfigurationConfiguration {
  return Object.freeze({
    runtimeName: params.runtimeName ?? 'Auralis Configuration Runtime',
    version: params.version ?? '1.0.0',
    strictMode: params.strictMode ?? true,
  });
}

export function createConfigurationEntry(
  params: Partial<ConfigurationEntry> & { key: string; value: unknown; sourceName: string },
): ConfigurationEntry {
  return Object.freeze({
    key: params.key,
    value: params.value,
    sourceName: params.sourceName,
    priority: params.priority ?? ConfigurationSourcePriority.DEFAULT,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createConfigurationSnapshot(
  params: Partial<ConfigurationSnapshot> = {},
): ConfigurationSnapshot {
  return Object.freeze({
    entries: Object.freeze({ ...(params.entries ?? {}) }),
    mergedValues: Object.freeze({ ...(params.mergedValues ?? {}) }),
    timestamp: params.timestamp ?? new Date().toISOString(),
    sourceCount: params.sourceCount ?? 0,
  });
}

export function createConfigurationSourceStatistics(
  params: Partial<ConfigurationSourceStatistics> = {},
): ConfigurationSourceStatistics {
  return Object.freeze({
    reads: params.reads ?? 0,
    writes: params.writes ?? 0,
    deletes: params.deletes ?? 0,
    hits: params.hits ?? 0,
    misses: params.misses ?? 0,
    itemCount: params.itemCount ?? 0,
  });
}

export function createConfigurationSourceHealth(
  params: Partial<ConfigurationSourceHealth> & { sourceName: string },
): ConfigurationSourceHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    sourceName: params.sourceName,
    enabled: params.enabled ?? true,
    message: params.message ?? `Source '${params.sourceName}' is operational.`,
  });
}

export function createConfigurationSourceRegistration(
  params: Partial<ConfigurationSourceRegistration> & { sourceName: string },
): ConfigurationSourceRegistration {
  return Object.freeze({
    sourceName: params.sourceName,
    priority: params.priority ?? ConfigurationSourcePriority.DEFAULT,
    enabled: params.enabled ?? true,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createConfigurationConstraint(
  params: Partial<ConfigurationConstraint> = {},
): ConfigurationConstraint {
  return Object.freeze({
    minValue: params.minValue,
    maxValue: params.maxValue,
    minLength: params.minLength,
    maxLength: params.maxLength,
    regexPattern: params.regexPattern,
    allowedValues: params.allowedValues ? Object.freeze([...params.allowedValues]) : undefined,
  });
}

export function createConfigurationDefinition(
  params: Partial<ConfigurationDefinition> & { key: string; expectedType: string },
): ConfigurationDefinition {
  return Object.freeze({
    key: params.key,
    expectedType: params.expectedType,
    defaultValue: params.defaultValue,
    required: params.required ?? false,
    constraint: params.constraint ? createConfigurationConstraint(params.constraint) : undefined,
    description: params.description,
  });
}

export function createConfigurationSchema(
  params: Partial<ConfigurationSchema> & { schemaName: string },
): ConfigurationSchema {
  return Object.freeze({
    schemaName: params.schemaName,
    definitions: Object.freeze({ ...(params.definitions ?? {}) }),
  });
}

export function createConfigurationError(
  params: Partial<ConfigurationError> & { key: string; message: string },
): ConfigurationError {
  return Object.freeze({
    key: params.key,
    message: params.message,
    code: params.code ?? 'VALIDATION_ERROR',
  });
}

export function createConfigurationWarning(
  params: Partial<ConfigurationWarning> & { key: string; message: string },
): ConfigurationWarning {
  return Object.freeze({
    key: params.key,
    message: params.message,
    code: params.code ?? 'VALIDATION_WARNING',
  });
}

export function createConfigurationValidationResult(
  params: Partial<ConfigurationValidationResult> = {},
): ConfigurationValidationResult {
  return Object.freeze({
    valid: params.valid ?? true,
    errors: Object.freeze([...(params.errors ?? [])]),
    warnings: Object.freeze([...(params.warnings ?? [])]),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createConfigurationResolutionResult<T = unknown>(
  params: Partial<ConfigurationResolutionResult<T>> & { key: string; value: T },
): ConfigurationResolutionResult<T> {
  return Object.freeze({
    key: params.key,
    value: params.value,
    converted: params.converted ?? false,
    sourceName: params.sourceName,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createValidationStatistics(
  params: Partial<ValidationStatistics> = {},
): ValidationStatistics {
  return Object.freeze({
    validations: params.validations ?? 0,
    passedValidations: params.passedValidations ?? 0,
    failedValidations: params.failedValidations ?? 0,
    totalErrors: params.totalErrors ?? 0,
    totalWarnings: params.totalWarnings ?? 0,
  });
}

export function createResolutionStatistics(
  params: Partial<ResolutionStatistics> = {},
): ResolutionStatistics {
  return Object.freeze({
    resolutions: params.resolutions ?? 0,
    conversions: params.conversions ?? 0,
    defaultFallbacks: params.defaultFallbacks ?? 0,
    failedResolutions: params.failedResolutions ?? 0,
  });
}

export function createFeatureFlag(
  params: Partial<FeatureFlag> & { featureName: string },
): FeatureFlag {
  return Object.freeze({
    featureName: params.featureName,
    enabled: params.enabled ?? false,
    description: params.description,
    rolloutPercentage: params.rolloutPercentage,
    allowedProfiles: params.allowedProfiles ? Object.freeze([...params.allowedProfiles]) : undefined,
    allowedEnvironments: params.allowedEnvironments ? Object.freeze([...params.allowedEnvironments]) : undefined,
    dependencies: params.dependencies ? Object.freeze([...params.dependencies]) : undefined,
  });
}

export function createFeatureEvaluation(
  params: Partial<FeatureEvaluation> & { featureName: string; enabled: boolean; reason: string },
): FeatureEvaluation {
  return Object.freeze({
    featureName: params.featureName,
    enabled: params.enabled,
    reason: params.reason,
    profileName: params.profileName,
    environmentName: params.environmentName,
    evaluatedAt: params.evaluatedAt ?? new Date().toISOString(),
  });
}

export function createFeatureStatistics(
  params: Partial<FeatureStatistics> = {},
): FeatureStatistics {
  return Object.freeze({
    evaluations: params.evaluations ?? 0,
    enabledEvaluations: params.enabledEvaluations ?? 0,
    disabledEvaluations: params.disabledEvaluations ?? 0,
    cachedEvaluations: params.cachedEvaluations ?? 0,
  });
}

export function createFeatureHealth(
  params: Partial<FeatureHealth> = {},
): FeatureHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    totalFeatures: params.totalFeatures ?? 0,
    enabledFeatures: params.enabledFeatures ?? 0,
    disabledFeatures: params.disabledFeatures ?? 0,
  });
}

export function createConfigurationProfileDefinition(
  params: Partial<ConfigurationProfileDefinition> & { profileType: string; profileName: string },
): ConfigurationProfileDefinition {
  return Object.freeze({
    profileType: params.profileType,
    profileName: params.profileName,
    parentProfileName: params.parentProfileName,
    overrides: Object.freeze({ ...(params.overrides ?? {}) }),
    active: params.active ?? false,
    priority: params.priority ?? 100,
  });
}

export function createConfigurationProfileSnapshot(
  params: Partial<ConfigurationProfileSnapshot> = {},
): ConfigurationProfileSnapshot {
  return Object.freeze({
    activeProfileName: params.activeProfileName ?? 'production',
    mergedOverrides: Object.freeze({ ...(params.mergedOverrides ?? {}) }),
    registeredProfiles: Object.freeze([...(params.registeredProfiles ?? [])]),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createProfileStatistics(
  params: Partial<ProfileStatistics> = {},
): ProfileStatistics {
  return Object.freeze({
    registrations: params.registrations ?? 0,
    activations: params.activations ?? 0,
    overrideKeysCount: params.overrideKeysCount ?? 0,
  });
}

export function createProfileHealth(
  params: Partial<ProfileHealth> = {},
): ProfileHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeProfileName: params.activeProfileName ?? 'production',
    totalProfiles: params.totalProfiles ?? 0,
  });
}

export function createSensitiveValuePolicy(
  params: Partial<SensitiveValuePolicy> = {},
): SensitiveValuePolicy {
  return Object.freeze({
    allowRead: params.allowRead ?? true,
    allowWrite: params.allowWrite ?? true,
    allowExport: params.allowExport ?? false,
    allowLogging: params.allowLogging ?? false,
    allowRedaction: params.allowRedaction ?? true,
  });
}

export function createSensitiveConfiguration(
  params: Partial<SensitiveConfiguration> & { key: string; rawValue: unknown },
): SensitiveConfiguration {
  return Object.freeze({
    key: params.key,
    rawValue: params.rawValue,
    sensitiveType: params.sensitiveType ?? SensitiveValueType.CUSTOM,
    policy: createSensitiveValuePolicy(params.policy),
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createSensitiveConfigurationReference(
  params: Partial<SensitiveConfigurationReference> & { key: string; redactedValue: string },
): SensitiveConfigurationReference {
  return Object.freeze({
    key: params.key,
    sensitiveType: params.sensitiveType ?? SensitiveValueType.CUSTOM,
    redactedValue: params.redactedValue,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createSensitiveConfigurationSnapshot(
  params: Partial<SensitiveConfigurationSnapshot> = {},
): SensitiveConfigurationSnapshot {
  return Object.freeze({
    references: Object.freeze([...(params.references ?? [])]),
    sensitiveCount: params.sensitiveCount ?? (params.references ? params.references.length : 0),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createSensitiveAccessRecord(
  params: Partial<SensitiveAccessRecord> & {
    key: string;
    action: 'REGISTER' | 'READ' | 'REDACT' | 'UPDATE' | 'REMOVE';
    success: boolean;
  },
): SensitiveAccessRecord {
  return Object.freeze({
    key: params.key,
    action: params.action,
    success: params.success,
    reason: params.reason,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createSensitiveStatistics(
  params: Partial<SensitiveStatistics> = {},
): SensitiveStatistics {
  return Object.freeze({
    totalValues: params.totalValues ?? 0,
    reads: params.reads ?? 0,
    redactions: params.redactions ?? 0,
    blockedAccesses: params.blockedAccesses ?? 0,
    auditRecordsCount: params.auditRecordsCount ?? 0,
  });
}

export function createSensitiveHealth(
  params: Partial<SensitiveHealth> = {},
): SensitiveHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    totalValues: params.totalValues ?? 0,
  });
}

export function createCertificationIssue(
  params: Partial<CertificationIssue> & { component: string; message: string },
): CertificationIssue {
  return Object.freeze({
    severity: params.severity ?? 'INFO',
    component: params.component,
    message: params.message,
    remediation: params.remediation,
  });
}

export function createConfigurationCertification(
  params: Partial<ConfigurationCertification> = {},
): ConfigurationCertification {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    environment: params.environment ?? 'production',
    issues: Object.freeze([...(params.issues ?? [])]),
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createConfigurationCertificationSummary(
  params: Partial<ConfigurationCertificationSummary> = {},
): ConfigurationCertificationSummary {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    totalChecks: params.totalChecks ?? 0,
    passedChecks: params.passedChecks ?? 0,
    failedChecks: params.failedChecks ?? 0,
    warningChecks: params.warningChecks ?? 0,
  });
}

export function createCertificationStatistics(
  params: Partial<CertificationStatistics> = {},
): CertificationStatistics {
  return Object.freeze({
    certificationsRun: params.certificationsRun ?? 0,
    passedCertifications: params.passedCertifications ?? 0,
    failedCertifications: params.failedCertifications ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationHealth(
  params: Partial<CertificationHealth> = {},
): CertificationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    lastCertificationScore: params.lastCertificationScore ?? 100,
    statusMessage: params.statusMessage ?? 'Configuration runtime is certified and operational.',
  });
}

export function createCertificationReport(
  params: Partial<CertificationReport> & {
    certification: ConfigurationCertification;
    summary: ConfigurationCertificationSummary;
    diagnostics: ConfigurationDiagnostics;
  },
): CertificationReport {
  return Object.freeze({
    certification: params.certification,
    summary: params.summary,
    diagnostics: params.diagnostics,
    benchmarkMs: params.benchmarkMs ?? 0,
    generatedAt: params.generatedAt ?? new Date().toISOString(),
  });
}

export function createConfigurationDiagnostics(
  params: Partial<ConfigurationDiagnostics> = {},
): ConfigurationDiagnostics {
  return Object.freeze({
    health: params.health ?? createConfigurationHealth(),
    statistics: params.statistics ?? createConfigurationStatistics(),
    capabilities: params.capabilities ?? createConfigurationCapabilities(),
    context: params.context ?? createConfigurationContext(),
    sources: params.sources ? Object.freeze([...params.sources]) : undefined,
    snapshot: params.snapshot,
    schemas: params.schemas ? Object.freeze([...params.schemas]) : undefined,
    validationStats: params.validationStats,
    resolutionStats: params.resolutionStats,
    activeProfile: params.activeProfile,
    profilesSnapshot: params.profilesSnapshot,
    profileStats: params.profileStats,
    featureStats: params.featureStats,
    featureHealth: params.featureHealth,
    sensitiveSnapshot: params.sensitiveSnapshot,
    sensitiveStats: params.sensitiveStats,
    sensitiveHealth: params.sensitiveHealth,
    certification: params.certification,
    certificationSummary: params.certificationSummary,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
