/**
 * Dependency Injection Domain Models (Phase 16.2.3).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, and diagnostics telemetry
 * for the Frontend Dependency Injection Container and Resolution Engine.
 */

export enum ServiceLifetime {
  SINGLETON = 'SINGLETON',
  TRANSIENT = 'TRANSIENT',
  SCOPED = 'SCOPED',
}

export enum ContainerState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export interface ServiceDescriptorModel {
  readonly descriptorId: string;
  readonly serviceType: string;
  readonly lifetime: ServiceLifetime;
  readonly implementationType?: string;
  readonly hasFactory: boolean;
  readonly hasInstance: boolean;
  readonly aliases: ReadonlyArray<string>;
  readonly tags: ReadonlyArray<string>;
  readonly metadata: Readonly<Record<string, unknown>>;
  readonly registeredAt: string;
}

export interface ServiceRegistration {
  readonly descriptorId: string;
  readonly serviceType: string;
  readonly lifetime: ServiceLifetime;
  readonly registeredAt: string;
}

export interface DependencyNode {
  readonly serviceType: string;
  readonly dependencies: ReadonlyArray<string>;
}

export interface ContainerCapabilities {
  readonly supportsScoped: boolean;
  readonly supportsFactories: boolean;
  readonly supportsInstances: boolean;
  readonly supportsCircularDetection: boolean;
  readonly supportsAliases: boolean;
  readonly supportsTags: boolean;
  readonly supportsReplacement: boolean;
  readonly maxDepth: number;
}

export interface ContainerStatistics {
  readonly totalRegistrations: number;
  readonly singletonCount: number;
  readonly transientCount: number;
  readonly scopedCount: number;
  readonly replacementsCount: number;
  readonly removalsCount: number;
  readonly rejectedRegistrationsCount: number;
  readonly aliasCount: number;
  readonly totalResolutions: number;
  readonly singletonCacheHits: number;
  readonly singletonCreations: number;
  readonly transientCreations: number;
  readonly factoryExecutions: number;
  readonly failedResolutions: number;
  readonly circularDependencyDetections: number;
  readonly cacheHits: number;
}

export interface ContainerHealth {
  readonly healthy: boolean;
  readonly state: ContainerState;
  readonly details: Readonly<Record<string, unknown>>;
  readonly timestamp: string;
}

export interface ContainerConfiguration {
  readonly name: string;
  readonly enableCircularCheck: boolean;
  readonly maxDepth: number;
  readonly validateOnBuild: boolean;
}

export interface ContainerContext {
  readonly containerId: string;
  readonly environment: string;
  readonly version: string;
}

export interface ContainerDiagnostics {
  readonly state: ContainerState;
  readonly health: ContainerHealth;
  readonly statistics: ContainerStatistics;
  readonly capabilities: ContainerCapabilities;
  readonly context: ContainerContext;
  readonly registeredServices: ReadonlyArray<string>;
  readonly resolvedServices: ReadonlyArray<string>;
  readonly cachedSingletons: ReadonlyArray<string>;
  readonly activeResolutionStack: ReadonlyArray<string>;
  readonly failedResolutions: number;
  readonly circularDependencyCount: number;
  readonly metrics: Readonly<Record<string, unknown>>;
  readonly timestamp: string;
}

export function createServiceDescriptorModel(
  params: Partial<ServiceDescriptorModel> & {
    descriptorId: string;
    serviceType: string;
    lifetime: ServiceLifetime;
  },
): ServiceDescriptorModel {
  return Object.freeze({
    descriptorId: params.descriptorId,
    serviceType: params.serviceType,
    lifetime: params.lifetime,
    implementationType: params.implementationType,
    hasFactory: params.hasFactory ?? false,
    hasInstance: params.hasInstance ?? false,
    aliases: Object.freeze([...(params.aliases ?? [])]),
    tags: Object.freeze([...(params.tags ?? [])]),
    metadata: Object.freeze({ ...(params.metadata ?? {}) }),
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createServiceRegistration(
  params: Partial<ServiceRegistration> & {
    descriptorId: string;
    serviceType: string;
    lifetime: ServiceLifetime;
  },
): ServiceRegistration {
  return Object.freeze({
    descriptorId: params.descriptorId,
    serviceType: params.serviceType,
    lifetime: params.lifetime,
    registeredAt: params.registeredAt ?? new Date().toISOString(),
  });
}

export function createDependencyNode(
  params: Partial<DependencyNode> & { serviceType: string },
): DependencyNode {
  return Object.freeze({
    serviceType: params.serviceType,
    dependencies: Object.freeze([...(params.dependencies ?? [])]),
  });
}

export function createContainerCapabilities(
  params: Partial<ContainerCapabilities> = {},
): ContainerCapabilities {
  return Object.freeze({
    supportsScoped: params.supportsScoped ?? true,
    supportsFactories: params.supportsFactories ?? true,
    supportsInstances: params.supportsInstances ?? true,
    supportsCircularDetection: params.supportsCircularDetection ?? true,
    supportsAliases: params.supportsAliases ?? true,
    supportsTags: params.supportsTags ?? true,
    supportsReplacement: params.supportsReplacement ?? true,
    maxDepth: params.maxDepth ?? 32,
  });
}

export function createContainerStatistics(
  params: Partial<ContainerStatistics> = {},
): ContainerStatistics {
  return Object.freeze({
    totalRegistrations: params.totalRegistrations ?? 0,
    singletonCount: params.singletonCount ?? 0,
    transientCount: params.transientCount ?? 0,
    scopedCount: params.scopedCount ?? 0,
    replacementsCount: params.replacementsCount ?? 0,
    removalsCount: params.removalsCount ?? 0,
    rejectedRegistrationsCount: params.rejectedRegistrationsCount ?? 0,
    aliasCount: params.aliasCount ?? 0,
    totalResolutions: params.totalResolutions ?? 0,
    singletonCacheHits: params.singletonCacheHits ?? 0,
    singletonCreations: params.singletonCreations ?? 0,
    transientCreations: params.transientCreations ?? 0,
    factoryExecutions: params.factoryExecutions ?? 0,
    failedResolutions: params.failedResolutions ?? 0,
    circularDependencyDetections: params.circularDependencyDetections ?? 0,
    cacheHits: params.cacheHits ?? params.singletonCacheHits ?? 0,
  });
}

export function createContainerHealth(params: Partial<ContainerHealth> = {}): ContainerHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    state: params.state ?? ContainerState.UNINITIALIZED,
    details: Object.freeze({ ...(params.details ?? {}) }),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createContainerConfiguration(
  params: Partial<ContainerConfiguration> = {},
): ContainerConfiguration {
  return Object.freeze({
    name: params.name ?? 'Auralis Container',
    enableCircularCheck: params.enableCircularCheck ?? true,
    maxDepth: params.maxDepth ?? 32,
    validateOnBuild: params.validateOnBuild ?? true,
  });
}

export function createContainerContext(params: Partial<ContainerContext> = {}): ContainerContext {
  return Object.freeze({
    containerId: params.containerId ?? 'default-container',
    environment: params.environment ?? 'production',
    version: params.version ?? '1.0.0',
  });
}

export function createContainerDiagnostics(
  params: Partial<ContainerDiagnostics> = {},
): ContainerDiagnostics {
  return Object.freeze({
    state: params.state ?? ContainerState.UNINITIALIZED,
    health: params.health ?? createContainerHealth(),
    statistics: params.statistics ?? createContainerStatistics(),
    capabilities: params.capabilities ?? createContainerCapabilities(),
    context: params.context ?? createContainerContext(),
    registeredServices: Object.freeze([...(params.registeredServices ?? [])]),
    resolvedServices: Object.freeze([...(params.resolvedServices ?? [])]),
    cachedSingletons: Object.freeze([...(params.cachedSingletons ?? [])]),
    activeResolutionStack: Object.freeze([...(params.activeResolutionStack ?? [])]),
    failedResolutions: params.failedResolutions ?? 0,
    circularDependencyCount: params.circularDependencyCount ?? 0,
    metrics: Object.freeze({ ...(params.metrics ?? {}) }),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
