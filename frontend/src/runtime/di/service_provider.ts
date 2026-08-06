/**
 * Service Provider Foundation Implementation (Phase 16.2.1).
 *
 * Implements IServiceProvider owning container configuration, context, health,
 * statistics, capabilities, and diagnostics telemetry.
 * Service resolution methods intentionally throw "Not Implemented" pending Phase 16.2.3.
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
    const services = this._collection.listServices();
    let singletons = 0;
    let transients = 0;
    let scopeds = 0;

    for (const descriptor of services) {
      if (descriptor.lifetime === ServiceLifetime.SINGLETON) singletons++;
      else if (descriptor.lifetime === ServiceLifetime.TRANSIENT) transients++;
      else if (descriptor.lifetime === ServiceLifetime.SCOPED) scopeds++;
    }

    return createContainerStatistics({
      totalRegistrations: services.length,
      singletonCount: singletons,
      transientCount: transients,
      scopedCount: scopeds,
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
      `Service resolution for '${serviceType}' is not implemented in Phase 16.2.1 (scheduled for Phase 16.2.3).`,
    );
  }

  public tryResolve<T>(serviceType: string): T | undefined {
    this._totalResolutionsCount++;
    this._failedResolutionsCount++;
    throw new ServiceResolutionException(
      `Service tryResolve for '${serviceType}' is not implemented in Phase 16.2.1 (scheduled for Phase 16.2.3).`,
    );
  }
}
