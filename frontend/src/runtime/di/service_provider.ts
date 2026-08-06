/**
 * Service Provider Foundation Implementation (Phase 16.2.2).
 *
 * Implements IServiceProvider owning container configuration, context, health,
 * statistics, capabilities, and diagnostics telemetry.
 * Resolution methods intentionally throw "Not Implemented" pending Phase 16.2.3.
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
} from './models';
import { IServiceCollection, IServiceProvider } from './interfaces';
import { ServiceCollection } from './service_collection';
import { ServiceResolutionException } from './exceptions';

export class ServiceProvider implements IServiceProvider {
  private _state: ContainerState = ContainerState.UNINITIALIZED;
  private readonly _collection: IServiceCollection;
  private readonly _config: ContainerConfiguration;
  private readonly _capabilities: ContainerCapabilities;
  private readonly _context: ContainerContext;

  private _totalResolutionsCount = 0;
  private _failedResolutionsCount = 0;

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
      totalResolutions: this._totalResolutionsCount,
      failedResolutions: this._failedResolutionsCount,
    });
  }

  public capabilities(): ContainerCapabilities {
    return this._capabilities;
  }

  public diagnostics(): ContainerDiagnostics {
    return createContainerDiagnostics({
      state: this._state,
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
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
    this._totalResolutionsCount++;
    this._failedResolutionsCount++;
    throw new ServiceResolutionException(
      `Service resolution for '${serviceType}' is not implemented in Phase 16.2.2 (scheduled for Phase 16.2.3).`,
    );
  }

  public tryResolve<T>(serviceType: string): T | undefined {
    this._totalResolutionsCount++;
    this._failedResolutionsCount++;
    throw new ServiceResolutionException(
      `Service tryResolve for '${serviceType}' is not implemented in Phase 16.2.2 (scheduled for Phase 16.2.3).`,
    );
  }
}
