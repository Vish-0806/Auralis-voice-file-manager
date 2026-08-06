/**
 * Service Provider Foundation & Resolution Engine Implementation (Phase 16.2.5).
 *
 * Implements IServiceProvider owning container configuration, context, health,
 * telemetry, diagnostics, full resolution engine, hierarchical child container scopes,
 * dependency graph analysis, and production certification.
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
  DependencyAnalysis,
  DependencyCertification,
  DependencyIssue,
  ServiceLifetime,
} from './models';
import { IServiceCollection, IServiceDescriptor, IServiceProvider } from './interfaces';
import { ServiceCollection } from './service_collection';
import { CircularDependencyException, ServiceResolutionException } from './exceptions';
import { DependencyGraphAnalyzer } from './dependency_graph_analyzer';

let _scopeIdCounter = 0;

export class ServiceProvider implements IServiceProvider {
  private _state: ContainerState = ContainerState.UNINITIALIZED;
  private readonly _collection: IServiceCollection;
  private readonly _config: ContainerConfiguration;
  private readonly _capabilities: ContainerCapabilities;
  private readonly _context: ContainerContext;
  private readonly _analyzer: DependencyGraphAnalyzer;

  private readonly _scopeId: string;
  private readonly _parentProvider?: ServiceProvider;
  private readonly _singletonCache: Map<string, unknown>;
  private readonly _scopedCache = new Map<string, unknown>();
  private readonly _childScopes = new Map<string, ServiceProvider>();
  private _active = true;

  private readonly _resolutionStack: string[] = [];
  private readonly _resolvedServicesSet = new Set<string>();

  private _totalResolutions = 0;
  private _singletonCacheHits = 0;
  private _singletonCreations = 0;
  private _transientCreations = 0;
  private _factoryExecutions = 0;
  private _failedResolutions = 0;
  private _circularDependencyCount = 0;

  private _scopesCreated = 0;
  private _scopesDisposed = 0;
  private _scopedInstancesCreated = 0;
  private _scopedCacheHits = 0;

  constructor(
    collection?: IServiceCollection,
    config?: ContainerConfiguration,
    capabilities?: ContainerCapabilities,
    context?: ContainerContext,
    parentProvider?: ServiceProvider,
    sharedSingletonCache?: Map<string, unknown>,
  ) {
    this._collection = collection ?? parentProvider?._collection ?? new ServiceCollection();
    this._config = config ?? parentProvider?._config ?? createContainerConfiguration();
    this._capabilities = capabilities ?? parentProvider?._capabilities ?? createContainerCapabilities();
    this._context = context ?? parentProvider?._context ?? createContainerContext();
    this._analyzer = new DependencyGraphAnalyzer();

    this._parentProvider = parentProvider;
    this._singletonCache = sharedSingletonCache ?? parentProvider?._singletonCache ?? new Map<string, unknown>();

    if (parentProvider) {
      _scopeIdCounter++;
      this._scopeId = `scope_${Date.now()}_${_scopeIdCounter}`;
      this._state = parentProvider._state;
    } else {
      this._scopeId = 'root';
    }
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

    this.disposeScope();
    this._state = ContainerState.STOPPING;
    this._state = ContainerState.STOPPED;
    this._singletonCache.clear();
    return this.health();
  }

  public restart(): ContainerHealth {
    this.shutdown();
    this._active = true;
    this.initialize();
    return this.health();
  }

  public health(): ContainerHealth {
    const healthy = this._state === ContainerState.READY && this._active;
    return createContainerHealth({
      healthy,
      state: this._state,
      details: {
        containerName: this._config.name,
        scopeId: this._scopeId,
        isScope: this.isScope(),
        active: this._active,
        totalRegistrations: this._collection.count(),
        cachedSingletons: this._singletonCache.size,
        scopedCacheSize: this._scopedCache.size,
        activeChildScopes: this._childScopes.size,
      },
      timestamp: new Date().toISOString(),
    });
  }

  public statistics(): ContainerStatistics {
    const collStats = this._collection.statistics();

    let aggregatedScopesCreated = this._scopesCreated;
    let aggregatedScopesDisposed = this._scopesDisposed;
    let aggregatedScopedInstancesCreated = this._scopedInstancesCreated;
    let aggregatedScopedCacheHits = this._scopedCacheHits;
    let aggregatedTotalResolutions = this._totalResolutions;
    let aggregatedSingletonHits = this._singletonCacheHits;

    for (const child of Array.from(this._childScopes.values())) {
      const childStats = child.statistics();
      aggregatedScopesCreated += childStats.scopesCreated;
      aggregatedScopesDisposed += childStats.scopesDisposed;
      aggregatedScopedInstancesCreated += childStats.scopedInstancesCreated;
      aggregatedScopedCacheHits += childStats.scopedCacheHits;
      aggregatedTotalResolutions += childStats.totalResolutions;
      aggregatedSingletonHits += childStats.singletonCacheHits;
    }

    return createContainerStatistics({
      totalRegistrations: collStats.totalRegistrations,
      singletonCount: collStats.singletonCount,
      transientCount: collStats.transientCount,
      scopedCount: collStats.scopedCount,
      replacementsCount: collStats.replacementsCount,
      removalsCount: collStats.removalsCount,
      rejectedRegistrationsCount: collStats.rejectedRegistrationsCount,
      aliasCount: collStats.aliasCount,
      totalResolutions: aggregatedTotalResolutions,
      singletonCacheHits: aggregatedSingletonHits,
      singletonCreations: this._singletonCreations,
      transientCreations: this._transientCreations,
      factoryExecutions: this._factoryExecutions,
      failedResolutions: this._failedResolutions,
      circularDependencyDetections: this._circularDependencyCount,
      cacheHits: aggregatedSingletonHits + aggregatedScopedCacheHits,
      scopesCreated: aggregatedScopesCreated,
      scopesDisposed: aggregatedScopesDisposed,
      activeScopes: this.calculateActiveScopesCount(),
      scopedInstancesCreated: aggregatedScopedInstancesCreated,
      scopedCacheHits: aggregatedScopedCacheHits,
    });
  }

  public capabilities(): ContainerCapabilities {
    return this._capabilities;
  }

  public diagnostics(): ContainerDiagnostics {
    const registered = this._collection.listServices().map((s) => s.serviceType);
    const scopeHierarchyMap: Record<string, string | null> = {};
    const activeScopesList: string[] = [this._scopeId];

    this.buildScopeDiagnostics(scopeHierarchyMap, activeScopesList);

    const cert = this.certify();

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
      activeScopes: activeScopesList,
      scopeHierarchy: scopeHierarchyMap,
      scopedCacheSize: this._scopedCache.size,
      failedResolutions: this._failedResolutions,
      circularDependencyCount: this._circularDependencyCount,
      metrics: {
        cacheHitRatio:
          this._totalResolutions > 0
            ? (this._singletonCacheHits + this._scopedCacheHits) / this._totalResolutions
            : 0,
      },
      graphSummary: cert.analysis.statistics,
      certification: cert,
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

  public analyzeGraph(): DependencyAnalysis {
    return this._analyzer.analyze(this._collection);
  }

  public validateGraph(): ReadonlyArray<DependencyIssue> {
    return this._analyzer.validate(this._collection);
  }

  public certify(): DependencyCertification {
    return this._analyzer.certify(this._collection);
  }

  public exportGraph(format: 'mermaid' | 'dot' | 'adjacency-list' | 'adjacency-map'): string {
    const analysis = this.analyzeGraph();
    return this._analyzer.exportGraph(analysis, format);
  }

  public createScope(): IServiceProvider {
    if (!this._active) {
      throw new ServiceResolutionException('Cannot create child scope from a disposed scope.');
    }
    const child = new ServiceProvider(
      this._collection,
      this._config,
      this._capabilities,
      this._context,
      this,
      this._singletonCache,
    );
    this._childScopes.set(child.scopeId(), child);
    this._scopesCreated++;
    return child;
  }

  public disposeScope(): void {
    if (!this._active) return;

    for (const child of Array.from(this._childScopes.values())) {
      child.disposeScope();
    }
    this._childScopes.clear();
    this._scopedCache.clear();
    this._active = false;
    this._scopesDisposed++;

    if (this._parentProvider) {
      this._parentProvider._scopesDisposed++;
      this._parentProvider._childScopes.delete(this._scopeId);
    }
  }

  public isScope(): boolean {
    return this._parentProvider !== undefined;
  }

  public scopeId(): string {
    return this._scopeId;
  }

  public parentScope(): IServiceProvider | undefined {
    return this._parentProvider;
  }

  public resolve<T>(serviceType: string): T {
    if (!this._active) {
      throw new ServiceResolutionException(`Cannot resolve service '${serviceType}' from a disposed scope.`);
    }

    this._totalResolutions++;
    const key = serviceType.trim();

    const descriptor = this.getDescriptorRecursive(key);
    if (!descriptor) {
      this._failedResolutions++;
      throw new ServiceResolutionException(`Service '${serviceType}' is not registered.`);
    }

    const primaryKey = descriptor.serviceType;

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
    if (!this.getDescriptorRecursive(key)) {
      return Object.freeze([]);
    }
    return Object.freeze([this.resolve<T>(key)]);
  }

  public createInstance<T>(constructorFn: new (...args: any[]) => T): T {
    if (!this._active) {
      throw new ServiceResolutionException('Cannot create instance from a disposed scope.');
    }
    if (!constructorFn) {
      throw new ServiceResolutionException('Constructor function cannot be null or undefined.');
    }
    const deps = (constructorFn as any).$dependencies ?? [];
    const resolvedDeps = deps.map((d: string) => this.resolve(d));
    return new constructorFn(...resolvedDeps);
  }

  private getDescriptorRecursive(key: string): IServiceDescriptor | undefined {
    const descriptor = this._collection.getDescriptor(key);
    if (descriptor) return descriptor;
    if (this._parentProvider) {
      return this._parentProvider.getDescriptorRecursive(key);
    }
    return undefined;
  }

  private resolveDescriptor<T>(descriptor: IServiceDescriptor): T {
    const key = descriptor.serviceType;

    // SCOPED Lifetime
    if (descriptor.lifetime === ServiceLifetime.SCOPED) {
      if (this._scopedCache.has(key)) {
        this._scopedCacheHits++;
        return this._scopedCache.get(key) as T;
      }

      let instance: T;
      if (descriptor.factory) {
        this._factoryExecutions++;
        instance = descriptor.factory(this) as T;
      } else if (descriptor.implementation) {
        instance = this.instantiateClass<T>(descriptor.implementation, descriptor.metadata);
      } else {
        throw new ServiceResolutionException(`No implementation or factory defined for scoped service '${key}'.`);
      }

      this._scopedInstancesCreated++;
      this._scopedCache.set(key, instance);
      return instance;
    }

    // SINGLETON Lifetime
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

  private calculateActiveScopesCount(): number {
    let count = this._active ? 1 : 0;
    for (const child of Array.from(this._childScopes.values())) {
      count += child.calculateActiveScopesCount();
    }
    return count;
  }

  private buildScopeDiagnostics(hierarchy: Record<string, string | null>, activeList: string[]): void {
    hierarchy[this._scopeId] = this._parentProvider ? this._parentProvider._scopeId : null;
    for (const [childId, child] of Array.from(this._childScopes.entries())) {
      activeList.push(childId);
      child.buildScopeDiagnostics(hierarchy, activeList);
    }
  }
}
