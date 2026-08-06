/**
 * Service Provider Resolution Engine Implementation (Phase 16.2.3).
 *
 * Implements IServiceProvider owning container configuration, context, health,
 * telemetry, diagnostics, and full dependency resolution (Singletons, Transients, Factories,
 * Recursive Constructor DI, Circular Dependency Detection).
 */

import {
  ContainerCapabilities,
  ContainerConfiguration,
  ContainerContext,
  ContainerDiagnostics,
  ContainerHealth,
  ContainerState,
  ContainerStatistics,
  createContainerCapabilities,
  createContainerConfiguration,
  createContainerContext,
  createContainerDiagnostics,
  createContainerHealth,
  createContainerStatistics,
  ServiceLifetime,
} from './models';
import { IServiceCollection, IServiceDescriptor, IServiceProvider } from './interfaces';
import { ServiceCollection } from './service_collection';
import { CircularDependencyException, ServiceResolutionException } from './exceptions';

export class ServiceProvider implements IServiceProvider {
  private _state: ContainerState = ContainerState.UNINITIALIZED;
  private readonly _collection: IServiceCollection;
  private readonly _config: ContainerConfiguration;
  private readonly _capabilities: ContainerCapabilities;
  private readonly _context: ContainerContext;

  private readonly _singletonCache = new Map<string, unknown>();
  private readonly _resolutionStack: string[] = [];
  private readonly _resolvedServicesSet = new Set<string>();

  private _totalResolutions = 0;
  private _singletonCacheHits = 0;
  private _singletonCreations = 0;
  private _transientCreations = 0;
  private _factoryExecutions = 0;
  private _failedResolutions = 0;
  private _circularDependencyCount = 0;

  constructor(
    collection?: IServiceCollection,
    config?: ContainerConfiguration,
    capabilities?: ContainerCapabilities,
    context?: ContainerContext,
  ) {
    this._collection = collection ?? new ServiceCollection();
    this._config = config ?? createContainerConfiguration();
    this._capabilities = capabilities ?? createContainerCapabilities();
    this._context = context ?? createContainerContext();
  }

  public initialize(): ContainerHealth {
    if (
      this._state === ContainerState.INITIALIZING ||
      this._state === ContainerState.READY
    ) {
      return this.health();
    }

    this._state = ContainerState.INITIALIZING;
    this._state = ContainerState.READY;
    return this.health();
  }

  public shutdown(): ContainerHealth {
    if (this._state === ContainerState.STOPPED) {
      return this.health();
    }

    this._state = ContainerState.STOPPING;
    this._state = ContainerState.STOPPED;
    this._singletonCache.clear();
    return this.health();
  }

  public restart(): ContainerHealth {
    this.shutdown();
    this.initialize();
    return this.health();
  }

  public health(): ContainerHealth {
    const healthy = this._state === ContainerState.READY;
    return createContainerHealth({
      healthy,
      state: this._state,
      details: {
        containerName: this._config.name,
        totalRegistrations: this._collection.count(),
        cachedSingletons: this._singletonCache.size,
      },
      timestamp: new Date().toISOString(),
    });
  }

  public statistics(): ContainerStatistics {
    const collStats = this._collection.statistics();
    return createContainerStatistics({
      totalRegistrations: collStats.totalRegistrations,
      singletonCount: collStats.singletonCount,
      transientCount: collStats.transientCount,
      scopedCount: collStats.scopedCount,
      replacementsCount: collStats.replacementsCount,
      removalsCount: collStats.removalsCount,
      rejectedRegistrationsCount: collStats.rejectedRegistrationsCount,
      aliasCount: collStats.aliasCount,
      totalResolutions: this._totalResolutions,
      singletonCacheHits: this._singletonCacheHits,
      singletonCreations: this._singletonCreations,
      transientCreations: this._transientCreations,
      factoryExecutions: this._factoryExecutions,
      failedResolutions: this._failedResolutions,
      circularDependencyDetections: this._circularDependencyCount,
      cacheHits: this._singletonCacheHits,
    });
  }

  public capabilities(): ContainerCapabilities {
    return this._capabilities;
  }

  public diagnostics(): ContainerDiagnostics {
    const registered = this._collection.listServices().map((s) => s.serviceType);
    return createContainerDiagnostics({
      state: this._state,
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      registeredServices: registered,
      resolvedServices: Array.from(this._resolvedServicesSet),
      cachedSingletons: Array.from(this._singletonCache.keys()),
      activeResolutionStack: [...this._resolutionStack],
      failedResolutions: this._failedResolutions,
      circularDependencyCount: this._circularDependencyCount,
      metrics: {
        cacheHitRatio:
          this._totalResolutions > 0 ? this._singletonCacheHits / this._totalResolutions : 0,
      },
      timestamp: new Date().toISOString(),
    });
  }

  public state(): ContainerState {
    return this._state;
  }

  public configuration(): ContainerConfiguration {
    return this._config;
  }

  public context(): ContainerContext {
    return this._context;
  }

  public resolve<T>(serviceType: string): T {
    this._totalResolutions++;
    const key = serviceType.trim();

    const descriptor = this._collection.getDescriptor(key);
    if (!descriptor) {
      this._failedResolutions++;
      throw new ServiceResolutionException(`Service '${serviceType}' is not registered.`);
    }

    const primaryKey = descriptor.serviceType;

    // Circular Dependency Detection
    if (this._config.enableCircularCheck && this._resolutionStack.includes(primaryKey)) {
      this._circularDependencyCount++;
      this._failedResolutions++;
      const chain = [...this._resolutionStack, primaryKey].join(' -> ');
      throw new CircularDependencyException(`Circular dependency detected: ${chain}`);
    }

    this._resolutionStack.push(primaryKey);

    try {
      const instance = this.resolveDescriptor<T>(descriptor);
      this._resolvedServicesSet.add(primaryKey);
      return instance;
    } catch (err) {
      if (!(err instanceof CircularDependencyException)) {
        this._failedResolutions++;
      }
      throw err;
    } finally {
      this._resolutionStack.pop();
    }
  }

  public resolveRequired<T>(serviceType: string): T {
    return this.resolve<T>(serviceType);
  }

  public tryResolve<T>(serviceType: string): T | undefined {
    try {
      return this.resolve<T>(serviceType);
    } catch (err) {
      if (err instanceof ServiceResolutionException) {
        return undefined;
      }
      throw err;
    }
  }

  public resolveAll<T>(serviceType: string): ReadonlyArray<T> {
    const key = serviceType.trim();
    if (!this._collection.contains(key)) {
      return Object.freeze([]);
    }
    return Object.freeze([this.resolve<T>(key)]);
  }

  public createInstance<T>(constructorFn: new (...args: any[]) => T): T {
    if (!constructorFn) {
      throw new ServiceResolutionException('Constructor function cannot be null or undefined.');
    }
    const deps = (constructorFn as any).$dependencies ?? [];
    const resolvedDeps = deps.map((d: string) => this.resolve(d));
    return new constructorFn(...resolvedDeps);
  }

  private resolveDescriptor<T>(descriptor: IServiceDescriptor): T {
    const key = descriptor.serviceType;

    if (descriptor.lifetime === ServiceLifetime.SCOPED) {
      throw new ServiceResolutionException(
        `Scoped lifetime resolution for '${key}' is not supported in root provider. Use a child scope (scheduled for Phase 16.2.4).`,
      );
    }

    if (descriptor.lifetime === ServiceLifetime.SINGLETON) {
      if (this._singletonCache.has(key)) {
        this._singletonCacheHits++;
        return this._singletonCache.get(key) as T;
      }
      if (descriptor.instance !== undefined) {
        this._singletonCache.set(key, descriptor.instance);
        return descriptor.instance as T;
      }

      let instance: T;
      if (descriptor.factory) {
        this._factoryExecutions++;
        instance = descriptor.factory(this) as T;
      } else if (descriptor.implementation) {
        instance = this.instantiateClass<T>(descriptor.implementation, descriptor.metadata);
      } else {
        throw new ServiceResolutionException(`No implementation or factory defined for '${key}'.`);
      }

      this._singletonCreations++;
      this._singletonCache.set(key, instance);
      return instance;
    }

    // TRANSIENT Lifetime
    let instance: T;
    if (descriptor.factory) {
      this._factoryExecutions++;
      instance = descriptor.factory(this) as T;
    } else if (descriptor.implementation) {
      instance = this.instantiateClass<T>(descriptor.implementation, descriptor.metadata);
    } else {
      throw new ServiceResolutionException(`No implementation or factory defined for '${key}'.`);
    }

    this._transientCreations++;
    return instance;
  }

  private instantiateClass<T>(
    implementation: new (...args: any[]) => any,
    metadata?: Readonly<Record<string, unknown>>,
  ): T {
    const rawDeps = metadata?.dependencies;
    let resolvedArgs: unknown[] = [];

    if (Array.isArray(rawDeps)) {
      resolvedArgs = rawDeps.map((depKey: string) => this.resolve(depKey));
    } else {
      const staticDeps = (implementation as any).$dependencies;
      if (Array.isArray(staticDeps)) {
        resolvedArgs = staticDeps.map((depKey: string) => this.resolve(depKey));
      }
    }

    return new implementation(...resolvedArgs);
  }
}
