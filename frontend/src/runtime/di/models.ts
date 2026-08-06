/**
 * Dependency Injection Domain Models (Phase 16.2.1).
 *
 * Provides immutable state models, configuration objects, capabilities telemetry,
 * health evaluation snapshots, statistics metrics, context metadata, and diagnostics telemetry
 * for the Frontend Dependency Injection Container.
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
  readonly serviceType: string;
  readonly lifetime: ServiceLifetime;
  readonly implementationType?: string;
  readonly hasFactory: boolean;
  readonly hasInstance: boolean;
  readonly metadata: Readonly<Record<string, unknown>>;
}

export interface ServiceRegistration {
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
  readonly maxDepth: number;
}

export interface ContainerStatistics {
  readonly totalRegistrations: number;
  readonly singletonCount: number;
  readonly transientCount: number;
  readonly scopedCount: number;
  readonly totalResolutions: number;
  readonly failedResolutions: number;
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
  readonly timestamp: string;
}

export function createServiceDescriptorModel(
  params: Partial<ServiceDescriptorModel> & { serviceType: string; lifetime: ServiceLifetime },
): ServiceDescriptorModel {
  return Object.freeze({
    serviceType: params.serviceType,
    lifetime: params.lifetime,
    implementationType: params.implementationType,
    hasFactory: params.hasFactory ?? false,
    hasInstance: params.hasInstance ?? false,
    metadata: Object.freeze({ ...(params.metadata ?? {}) }),
  });
}

export function createServiceRegistration(
  params: Partial<ServiceRegistration> & { serviceType: string; lifetime: ServiceLifetime },
): ServiceRegistration {
  return Object.freeze({
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
    totalResolutions: params.totalResolutions ?? 0,
    failedResolutions: params.failedResolutions ?? 0,
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
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
