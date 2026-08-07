/**
 * Plugin Runtime Domain Models (Phase 16.7).
 *
 * Implements immutable state models, configuration objects, capabilities, telemetry,
 * health snapshots, stats, context metadata, registrations, life cycle records,
 * sandboxes, permissions, validation results, dependency resolutions, and certification reports.
 */

export enum PluginRuntimeStatus {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export enum PluginLifecycleState {
  DISCOVERED = 'DISCOVERED',
  REGISTERED = 'REGISTERED',
  VALIDATED = 'VALIDATED',
  RESOLVED = 'RESOLVED',
  LOADED = 'LOADED',
  INITIALIZED = 'INITIALIZED',
  ACTIVATED = 'ACTIVATED',
  DEACTIVATED = 'DEACTIVATED',
  UNLOADED = 'UNLOADED',
  FAILED = 'FAILED',
}

export type PermissionScope = 'filesystem' | 'clipboard' | 'configuration' | 'commands' | 'events' | 'state' | 'diagnostics' | 'network' | string;

export interface PluginAuthor {
  readonly name: string;
  readonly email?: string;
  readonly url?: string;
}

export interface PluginVersion {
  readonly major: number;
  readonly minor: number;
  readonly patch: number;
  readonly prerelease?: string;
  readonly build?: string;
  readonly raw: string;
}

export interface PluginDependency {
  readonly id: string;
  readonly versionRange: string;
  readonly optional: boolean;
}

export interface PluginCapability {
  readonly type: 'command' | 'view' | 'panel' | 'menu' | 'service' | 'listener' | 'configuration' | 'state' | 'extension' | string;
  readonly name: string;
  readonly details: Record<string, unknown>;
}

export interface PluginPermission {
  readonly scope: PermissionScope;
  readonly description?: string;
  readonly required: boolean;
}

export interface PluginSandbox {
  readonly capabilityRestrictions: ReadonlyArray<string>;
  readonly permissionRestrictions: ReadonlyArray<string>;
  readonly executionIsolation: boolean;
  readonly resourceLimits?: Record<string, number>;
  readonly runtimePolicies?: ReadonlyArray<string>;
}

export interface PluginMetadata {
  readonly homepage?: string;
  readonly repository?: string;
  readonly license?: string;
  readonly keywords?: ReadonlyArray<string>;
}

export interface PluginContribution {
  readonly target: string;
  readonly value: Record<string, unknown>;
}

export interface PluginExtensionPoint {
  readonly id: string;
  readonly schema?: Record<string, unknown>;
}

export interface PluginManifest {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly description: string;
  readonly author: PluginAuthor;
  readonly main: string;
  readonly dependencies: ReadonlyArray<PluginDependency>;
  readonly capabilities: ReadonlyArray<PluginCapability>;
  readonly permissions: ReadonlyArray<PluginPermission>;
  readonly sandbox: PluginSandbox;
  readonly metadata: PluginMetadata;
  readonly contributions: ReadonlyArray<PluginContribution>;
  readonly extensionPoints: ReadonlyArray<PluginExtensionPoint>;
  readonly engineVersion?: string;
}

export interface PluginDescriptor {
  readonly id: string;
  readonly manifest: PluginManifest;
  readonly loadPath?: string;
  readonly checksum?: string;
}

export interface PluginContext {
  readonly pluginId: string;
  readonly extensionApi: unknown;
  readonly storagePath?: string;
  readonly tempPath?: string;
}

export interface PluginState {
  readonly pluginId: string;
  readonly lifecycleState: PluginLifecycleState;
  readonly initialized: boolean;
  readonly activated: boolean;
  readonly error?: string;
  readonly registeredAt?: string;
  readonly activatedAt?: string;
}

export interface PluginConfiguration {
  readonly pluginId: string;
  readonly settings: Record<string, unknown>;
  readonly schema?: Record<string, unknown>;
}

export interface PluginHealth {
  readonly healthy: boolean;
  readonly pluginId: string;
  readonly lifecycleState: PluginLifecycleState;
  readonly issues: ReadonlyArray<string>;
  readonly message: string;
}

export interface PluginStatistics {
  readonly pluginId: string;
  readonly loadTimeMs: number;
  readonly activationTimeMs: number;
  readonly executionCount: number;
  readonly errorCount: number;
  readonly memoryUsageBytes?: number;
}

export interface PluginDiagnostics {
  readonly pluginId: string;
  readonly state: PluginState;
  readonly health: PluginHealth;
  readonly statistics: PluginStatistics;
  readonly timestamp: string;
}

export interface PluginSnapshot {
  readonly pluginId: string;
  readonly state: PluginState;
  readonly configuration: PluginConfiguration;
  readonly timestamp: string;
}

export interface PluginActivation {
  readonly pluginId: string;
  readonly activatedAt: string;
  readonly durationMs: number;
  readonly success: boolean;
  readonly error?: string;
}

export interface PluginDeactivation {
  readonly pluginId: string;
  readonly deactivatedAt: string;
  readonly durationMs: number;
  readonly success: boolean;
  readonly error?: string;
}

export interface PluginLoadResult {
  readonly pluginId: string;
  readonly success: boolean;
  readonly error?: string;
  readonly durationMs: number;
}

export interface PluginUnloadResult {
  readonly pluginId: string;
  readonly success: boolean;
  readonly error?: string;
  readonly durationMs: number;
}

export interface PluginRegistration {
  readonly pluginId: string;
  readonly registeredAt: string;
  readonly success: boolean;
  readonly error?: string;
}

export interface PluginValidationIssue {
  readonly severity: 'error' | 'warning';
  readonly path: string;
  readonly message: string;
}

export interface PluginValidationResult {
  readonly valid: boolean;
  readonly pluginId: string;
  readonly issues: ReadonlyArray<PluginValidationIssue>;
  readonly validatedAt: string;
}

export interface PluginCompatibilityResult {
  readonly compatible: boolean;
  readonly pluginId: string;
  readonly engineMatch: boolean;
  readonly dependencyMatch: boolean;
  readonly details: Record<string, string>;
}

export interface PluginResolutionResult {
  readonly resolved: boolean;
  readonly pluginId: string;
  readonly missingRequired: ReadonlyArray<string>;
  readonly missingOptional: ReadonlyArray<string>;
  readonly circularDetected: boolean;
  readonly loadOrder: ReadonlyArray<string>;
}

export interface PluginService {
  readonly id: string;
  readonly pluginId: string;
  readonly interfaceName: string;
  readonly scope: 'singleton' | 'transient' | 'scoped';
}

export interface PluginLifecycleRecord {
  readonly pluginId: string;
  readonly state: PluginLifecycleState;
  readonly timestamp: string;
  readonly description?: string;
}

export interface PluginExecutionRecord {
  readonly pluginId: string;
  readonly action: string;
  readonly timestamp: string;
  readonly durationMs: number;
  readonly success: boolean;
  readonly error?: string;
}

export interface PluginTelemetry {
  readonly pluginId: string;
  readonly totalExecutions: number;
  readonly failedExecutions: number;
  readonly successRate: number;
  readonly averageLatencyMs: number;
  readonly logs: ReadonlyArray<string>;
}

export interface PluginRuntimeState {
  readonly runtimeState: PluginRuntimeStatus;
  readonly initialized: boolean;
  readonly activePluginsCount: number;
  readonly totalPluginsCount: number;
  readonly startedAt: string | null;
}

export interface CertificationIssue {
  readonly type: string;
  readonly message: string;
  readonly critical: boolean;
}

export interface PluginCertification {
  readonly pluginId: string;
  readonly certified: boolean;
  readonly score: number;
  readonly issues: ReadonlyArray<CertificationIssue>;
  readonly certifiedAt: string;
}

export interface PluginCertificationSummary {
  readonly totalCertified: number;
  readonly totalFailed: number;
  readonly averageScore: number;
}

export interface CertificationStatistics {
  readonly totalRuns: number;
  readonly passCount: number;
  readonly failCount: number;
  readonly averageScore: number;
}

export interface CertificationHealth {
  readonly healthy: boolean;
  readonly failureRate: number;
  readonly message: string;
}

export interface CertificationReport {
  readonly pluginId: string;
  readonly certification: PluginCertification;
  readonly timestamp: string;
  readonly signature: string;
}

// Factory Functions

export function createPluginAuthor(params: Partial<PluginAuthor> = {}): PluginAuthor {
  return Object.freeze({
    name: params.name ?? 'Unknown',
    email: params.email,
    url: params.url,
  });
}

export function createPluginVersion(params: Partial<PluginVersion> = {}): PluginVersion {
  return Object.freeze({
    major: params.major ?? 1,
    minor: params.minor ?? 0,
    patch: params.patch ?? 0,
    prerelease: params.prerelease,
    build: params.build,
    raw: params.raw ?? `${params.major ?? 1}.${params.minor ?? 0}.${params.patch ?? 0}`,
  });
}

export function createPluginDependency(params: Partial<PluginDependency> & { id: string }): PluginDependency {
  return Object.freeze({
    id: params.id,
    versionRange: params.versionRange ?? '*',
    optional: params.optional ?? false,
  });
}

export function createPluginCapability(params: Partial<PluginCapability> & { name: string; type: string }): PluginCapability {
  return Object.freeze({
    type: params.type,
    name: params.name,
    details: Object.freeze({ ...(params.details ?? {}) }),
  });
}

export function createPluginPermission(params: Partial<PluginPermission> & { scope: PermissionScope }): PluginPermission {
  return Object.freeze({
    scope: params.scope,
    description: params.description,
    required: params.required ?? true,
  });
}

export function createPluginSandbox(params: Partial<PluginSandbox> = {}): PluginSandbox {
  return Object.freeze({
    capabilityRestrictions: Object.freeze([...(params.capabilityRestrictions ?? [])]),
    permissionRestrictions: Object.freeze([...(params.permissionRestrictions ?? [])]),
    executionIsolation: params.executionIsolation ?? true,
    resourceLimits: params.resourceLimits ? Object.freeze({ ...params.resourceLimits }) : undefined,
    runtimePolicies: params.runtimePolicies ? Object.freeze([...params.runtimePolicies]) : undefined,
  });
}

export function createPluginMetadata(params: Partial<PluginMetadata> = {}): PluginMetadata {
  return Object.freeze({
    homepage: params.homepage,
    repository: params.repository,
    license: params.license,
    keywords: params.keywords ? Object.freeze([...params.keywords]) : undefined,
  });
}

export function createPluginContribution(params: Partial<PluginContribution> & { target: string }): PluginContribution {
  return Object.freeze({
    target: params.target,
    value: Object.freeze({ ...(params.value ?? {}) }),
  });
}

export function createPluginExtensionPoint(params: Partial<PluginExtensionPoint> & { id: string }): PluginExtensionPoint {
  return Object.freeze({
    id: params.id,
    schema: params.schema ? Object.freeze({ ...params.schema }) : undefined,
  });
}

export function createPluginManifest(params: Partial<PluginManifest> & { id: string; name: string }): PluginManifest {
  return Object.freeze({
    id: params.id,
    name: params.name,
    version: params.version ?? '1.0.0',
    description: params.description ?? '',
    author: createPluginAuthor(params.author),
    main: params.main ?? 'index.js',
    dependencies: Object.freeze((params.dependencies ?? []).map(d => createPluginDependency(d))),
    capabilities: Object.freeze((params.capabilities ?? []).map(c => createPluginCapability(c))),
    permissions: Object.freeze((params.permissions ?? []).map(p => createPluginPermission(p))),
    sandbox: createPluginSandbox(params.sandbox),
    metadata: createPluginMetadata(params.metadata),
    contributions: Object.freeze((params.contributions ?? []).map(c => createPluginContribution(c))),
    extensionPoints: Object.freeze((params.extensionPoints ?? []).map(ep => createPluginExtensionPoint(ep))),
    engineVersion: params.engineVersion,
  });
}

export function createPluginDescriptor(params: Partial<PluginDescriptor> & { id: string; manifest: PluginManifest }): PluginDescriptor {
  return Object.freeze({
    id: params.id,
    manifest: params.manifest,
    loadPath: params.loadPath,
    checksum: params.checksum,
  });
}

export function createPluginContext(params: Partial<PluginContext> & { pluginId: string }): PluginContext {
  return Object.freeze({
    pluginId: params.pluginId,
    extensionApi: params.extensionApi ?? {},
    storagePath: params.storagePath,
    tempPath: params.tempPath,
  });
}

export function createPluginState(params: Partial<PluginState> & { pluginId: string }): PluginState {
  return Object.freeze({
    pluginId: params.pluginId,
    lifecycleState: params.lifecycleState ?? PluginLifecycleState.DISCOVERED,
    initialized: params.initialized ?? false,
    activated: params.activated ?? false,
    error: params.error,
    registeredAt: params.registeredAt,
    activatedAt: params.activatedAt,
  });
}

export function createPluginConfiguration(params: Partial<PluginConfiguration> & { pluginId: string }): PluginConfiguration {
  return Object.freeze({
    pluginId: params.pluginId,
    settings: Object.freeze({ ...(params.settings ?? {}) }),
    schema: params.schema ? Object.freeze({ ...params.schema }) : undefined,
  });
}

export function createPluginHealth(params: Partial<PluginHealth> & { pluginId: string }): PluginHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    pluginId: params.pluginId,
    lifecycleState: params.lifecycleState ?? PluginLifecycleState.DISCOVERED,
    issues: Object.freeze([...(params.issues ?? [])]),
    message: params.message ?? 'Plugin is operational.',
  });
}

export function createPluginStatistics(params: Partial<PluginStatistics> & { pluginId: string }): PluginStatistics {
  return Object.freeze({
    pluginId: params.pluginId,
    loadTimeMs: params.loadTimeMs ?? 0,
    activationTimeMs: params.activationTimeMs ?? 0,
    executionCount: params.executionCount ?? 0,
    errorCount: params.errorCount ?? 0,
    memoryUsageBytes: params.memoryUsageBytes,
  });
}

export function createPluginDiagnostics(params: Partial<PluginDiagnostics> & { pluginId: string }): PluginDiagnostics {
  return Object.freeze({
    pluginId: params.pluginId,
    state: params.state ?? createPluginState({ pluginId: params.pluginId }),
    health: params.health ?? createPluginHealth({ pluginId: params.pluginId }),
    statistics: params.statistics ?? createPluginStatistics({ pluginId: params.pluginId }),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createPluginSnapshot(params: Partial<PluginSnapshot> & { pluginId: string }): PluginSnapshot {
  return Object.freeze({
    pluginId: params.pluginId,
    state: params.state ?? createPluginState({ pluginId: params.pluginId }),
    configuration: params.configuration ?? createPluginConfiguration({ pluginId: params.pluginId }),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createPluginActivation(params: Partial<PluginActivation> & { pluginId: string }): PluginActivation {
  return Object.freeze({
    pluginId: params.pluginId,
    activatedAt: params.activatedAt ?? new Date().toISOString(),
    durationMs: params.durationMs ?? 0,
    success: params.success ?? true,
    error: params.error,
  });
}

export function createPluginDeactivation(params: Partial<PluginDeactivation> & { pluginId: string }): PluginDeactivation {
  return Object.freeze({
    pluginId: params.pluginId,
    deactivatedAt: params.deactivatedAt ?? new Date().toISOString(),
    durationMs: params.durationMs ?? 0,
    success: params.success ?? true,
    error: params.error,
  });
}

export function createPluginLoadResult(params: Partial<PluginLoadResult> & { pluginId: string }): PluginLoadResult {
  return Object.freeze({
    pluginId: params.pluginId,
    success: params.success ?? true,
    error: params.error,
    durationMs: params.durationMs ?? 0,
  });
}

export function createPluginUnloadResult(params: Partial<PluginUnloadResult> & { pluginId: string }): PluginUnloadResult {
  return Object.freeze({
    pluginId: params.pluginId,
    success: params.success ?? true,
    error: params.error,
    durationMs: params.durationMs ?? 0,
  });
}

export function createPluginRegistration(params: Partial<PluginRegistration> & { pluginId: string }): PluginRegistration {
  return Object.freeze({
    pluginId: params.pluginId,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
    success: params.success ?? true,
    error: params.error,
  });
}

export function createPluginValidationIssue(params: { severity: 'error' | 'warning'; path: string; message: string }): PluginValidationIssue {
  return Object.freeze({
    severity: params.severity,
    path: params.path,
    message: params.message,
  });
}

export function createPluginValidationResult(params: Partial<PluginValidationResult> & { pluginId: string }): PluginValidationResult {
  return Object.freeze({
    valid: params.valid ?? true,
    pluginId: params.pluginId,
    issues: Object.freeze((params.issues ?? []).map(i => createPluginValidationIssue(i))),
    validatedAt: params.validatedAt ?? new Date().toISOString(),
  });
}

export function createPluginCompatibilityResult(params: Partial<PluginCompatibilityResult> & { pluginId: string }): PluginCompatibilityResult {
  return Object.freeze({
    compatible: params.compatible ?? true,
    pluginId: params.pluginId,
    engineMatch: params.engineMatch ?? true,
    dependencyMatch: params.dependencyMatch ?? true,
    details: Object.freeze({ ...(params.details ?? {}) }),
  });
}

export function createPluginResolutionResult(params: Partial<PluginResolutionResult> & { pluginId: string }): PluginResolutionResult {
  return Object.freeze({
    resolved: params.resolved ?? true,
    pluginId: params.pluginId,
    missingRequired: Object.freeze([...(params.missingRequired ?? [])]),
    missingOptional: Object.freeze([...(params.missingOptional ?? [])]),
    circularDetected: params.circularDetected ?? false,
    loadOrder: Object.freeze([...(params.loadOrder ?? [])]),
  });
}

export function createPluginService(params: { id: string; pluginId: string; interfaceName: string; scope?: 'singleton' | 'transient' | 'scoped' }): PluginService {
  return Object.freeze({
    id: params.id,
    pluginId: params.pluginId,
    interfaceName: params.interfaceName,
    scope: params.scope ?? 'singleton',
  });
}

export function createPluginLifecycleRecord(params: Partial<PluginLifecycleRecord> & { pluginId: string; state: PluginLifecycleState }): PluginLifecycleRecord {
  return Object.freeze({
    pluginId: params.pluginId,
    state: params.state,
    timestamp: params.timestamp ?? new Date().toISOString(),
    description: params.description,
  });
}

export function createPluginExecutionRecord(params: Partial<PluginExecutionRecord> & { pluginId: string; action: string }): PluginExecutionRecord {
  return Object.freeze({
    pluginId: params.pluginId,
    action: params.action,
    timestamp: params.timestamp ?? new Date().toISOString(),
    durationMs: params.durationMs ?? 0,
    success: params.success ?? true,
    error: params.error,
  });
}

export function createPluginTelemetry(params: Partial<PluginTelemetry> & { pluginId: string }): PluginTelemetry {
  return Object.freeze({
    pluginId: params.pluginId,
    totalExecutions: params.totalExecutions ?? 0,
    failedExecutions: params.failedExecutions ?? 0,
    successRate: params.successRate ?? 1.0,
    averageLatencyMs: params.averageLatencyMs ?? 0,
    logs: Object.freeze([...(params.logs ?? [])]),
  });
}

export function createCertificationIssue(params: { type: string; message: string; critical?: boolean }): CertificationIssue {
  return Object.freeze({
    type: params.type,
    message: params.message,
    critical: params.critical ?? false,
  });
}

export function createPluginCertification(params: Partial<PluginCertification> & { pluginId: string }): PluginCertification {
  return Object.freeze({
    pluginId: params.pluginId,
    certified: params.certified ?? true,
    score: params.score ?? 100,
    issues: Object.freeze((params.issues ?? []).map(i => createCertificationIssue(i))),
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createPluginCertificationSummary(params: Partial<PluginCertificationSummary> = {}): PluginCertificationSummary {
  return Object.freeze({
    totalCertified: params.totalCertified ?? 0,
    totalFailed: params.totalFailed ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationStatistics(params: Partial<CertificationStatistics> = {}): CertificationStatistics {
  return Object.freeze({
    totalRuns: params.totalRuns ?? 0,
    passCount: params.passCount ?? 0,
    failCount: params.failCount ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationHealth(params: Partial<CertificationHealth> = {}): CertificationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    failureRate: params.failureRate ?? 0,
    message: params.message ?? 'Certification operations are healthy.',
  });
}

export function createCertificationReport(params: Partial<CertificationReport> & { pluginId: string }): CertificationReport {
  return Object.freeze({
    pluginId: params.pluginId,
    certification: params.certification ?? createPluginCertification({ pluginId: params.pluginId }),
    timestamp: params.timestamp ?? new Date().toISOString(),
    signature: params.signature ?? `sha256-${Date.now()}`,
  });
}

export function createPluginRuntimeState(params: Partial<PluginRuntimeState> = {}): PluginRuntimeState {
  return Object.freeze({
    runtimeState: params.runtimeState ?? PluginRuntimeStatus.UNINITIALIZED,
    initialized: params.initialized ?? false,
    activePluginsCount: params.activePluginsCount ?? 0,
    totalPluginsCount: params.totalPluginsCount ?? 0,
    startedAt: params.startedAt ?? null,
  });
}
