/**
 * Dependency Container Coordinator Implementation (Phase 16.2.5).
 *
 * Coordinates container lifecycle operations, child container scope management,
 * graph analysis, production certification, and delegates provider/collection operations.
 */

import {
  ContainerCapabilities,
  ContainerDiagnostics,
  ContainerHealth,
  ContainerState,
  ContainerStatistics,
  DependencyAnalysis,
  DependencyCertification,
  DependencyIssue,
} from './models';
import { IDependencyContainer, IServiceCollection, IServiceProvider } from './interfaces';
import { ServiceProvider } from './service_provider';
import { ServiceCollection } from './service_collection';

export class DependencyContainer implements IDependencyContainer {
  private readonly _provider: IServiceProvider;
  private readonly _collection: IServiceCollection;

  constructor(provider?: IServiceProvider, collection?: IServiceCollection) {
    this._collection = collection ?? (provider?.configuration ? (provider as any)._collection : new ServiceCollection());
    this._provider = provider ?? new ServiceProvider(this._collection);
  }

  public initialize(): ContainerHealth {
    return this._provider.initialize();
  }

  public shutdown(): ContainerHealth {
    return this._provider.shutdown();
  }

  public restart(): ContainerHealth {
    return this._provider.restart();
  }

  public health(): ContainerHealth {
    return this._provider.health();
  }

  public statistics(): ContainerStatistics {
    return this._provider.statistics();
  }

  public capabilities(): ContainerCapabilities {
    return this._provider.capabilities();
  }

  public diagnostics(): ContainerDiagnostics {
    return this._provider.diagnostics();
  }

  public state(): ContainerState {
    return this._provider.state();
  }

  public provider(): IServiceProvider {
    return this._provider;
  }

  public collection(): IServiceCollection {
    return this._collection;
  }

  public resolve<T>(serviceType: string): T {
    return this._provider.resolve<T>(serviceType);
  }

  public resolveRequired<T>(serviceType: string): T {
    return this._provider.resolveRequired<T>(serviceType);
  }

  public tryResolve<T>(serviceType: string): T | undefined {
    return this._provider.tryResolve<T>(serviceType);
  }

  public resolveAll<T>(serviceType: string): ReadonlyArray<T> {
    return this._provider.resolveAll<T>(serviceType);
  }

  public createInstance<T>(constructorFn: new (...args: any[]) => T): T {
    return this._provider.createInstance<T>(constructorFn);
  }

  public createScope(): IDependencyContainer {
    const childProvider = this._provider.createScope();
    return new DependencyContainer(childProvider, this._collection);
  }

  public disposeScope(): void {
    this._provider.disposeScope();
  }

  public analyzeGraph(): DependencyAnalysis {
    return this._provider.analyzeGraph();
  }

  public validateGraph(): ReadonlyArray<DependencyIssue> {
    return this._provider.validateGraph();
  }

  public certify(): DependencyCertification {
    return this._provider.certify();
  }

  public exportGraph(format: 'mermaid' | 'dot' | 'adjacency-list' | 'adjacency-map'): string {
    return this._provider.exportGraph(format);
  }
}
