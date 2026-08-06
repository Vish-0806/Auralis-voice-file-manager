/**
 * Service Collection Implementation (Phase 16.2.1).
 *
 * Registry store for managing service descriptors (Singletons, Transients, Scoped).
 */

import { ServiceLifetime } from './models';
import { IServiceCollection, IServiceDescriptor } from './interfaces';
import { ServiceDescriptor } from './service_descriptor';

export class ServiceCollection implements IServiceCollection {
  private readonly _descriptors = new Map<string, IServiceDescriptor>();

  public addSingleton(
    serviceType: string,
    implementationOrFactoryOrInstance: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.SINGLETON,
      implementationOrFactoryOrInstance,
      metadata,
    );
    this._descriptors.set(descriptor.serviceType, descriptor);
    return this;
  }

  public addTransient(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.TRANSIENT,
      implementationOrFactory,
      metadata,
    );
    this._descriptors.set(descriptor.serviceType, descriptor);
    return this;
  }

  public addScoped(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.SCOPED,
      implementationOrFactory,
      metadata,
    );
    this._descriptors.set(descriptor.serviceType, descriptor);
    return this;
  }

  public remove(serviceType: string): boolean {
    return this._descriptors.delete(serviceType.trim());
  }

  public contains(serviceType: string): boolean {
    return this._descriptors.has(serviceType.trim());
  }

  public count(): number {
    return this._descriptors.size;
  }

  public clear(): void {
    this._descriptors.clear();
  }

  public listServices(): ReadonlyArray<IServiceDescriptor> {
    return Object.freeze(Array.from(this._descriptors.values()));
  }

  public get(serviceType: string): IServiceDescriptor | undefined {
    return this._descriptors.get(serviceType.trim());
  }
}
