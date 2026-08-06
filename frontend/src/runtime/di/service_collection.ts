/**
 * Service Collection Implementation (Phase 16.2.2).
 *
 * Production Service Registration Engine providing O(1) lookups for primary service types
 * and aliases, conflict detection, replacement semantics, lifetime filtering, and registration statistics.
 */

import { ContainerStatistics, createContainerStatistics, ServiceLifetime } from './models';
import { IServiceCollection, IServiceDescriptor, ServiceRegistrationOptions } from './interfaces';
import { ServiceDescriptor } from './service_descriptor';
import { ServiceRegistrationException } from './exceptions';

export class ServiceCollection implements IServiceCollection {
  private readonly _descriptors = new Map<string, IServiceDescriptor>();
  private readonly _aliasMap = new Map<string, string>();

  private _replacementsCount = 0;
  private _removalsCount = 0;
  private _rejectedRegistrationsCount = 0;

  public addSingleton(
    serviceType: string,
    implementationOrFactoryOrInstance: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.SINGLETON,
      implementationOrFactoryOrInstance,
      metadata,
      options,
    );
    return this.register(descriptor);
  }

  public addTransient(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.TRANSIENT,
      implementationOrFactory,
      metadata,
      options,
    );
    return this.register(descriptor);
  }

  public addScoped(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection {
    const descriptor = new ServiceDescriptor(
      serviceType,
      ServiceLifetime.SCOPED,
      implementationOrFactory,
      metadata,
      options,
    );
    return this.register(descriptor);
  }

  public register(descriptor: IServiceDescriptor): IServiceCollection {
    if (!descriptor) {
      this._rejectedRegistrationsCount++;
      throw new ServiceRegistrationException('Service descriptor cannot be null or undefined.');
    }

    const serviceType = descriptor.serviceType.trim();

    // Check primary duplicate conflict
    if (this._descriptors.has(serviceType)) {
      this._rejectedRegistrationsCount++;
      throw new ServiceRegistrationException(
        `Service type '${serviceType}' is already registered. Use replace() to overwrite.`,
      );
    }

    // Check if serviceType conflicts with an existing alias
    if (this._aliasMap.has(serviceType)) {
      this._rejectedRegistrationsCount++;
      throw new ServiceRegistrationException(
        `Service type '${serviceType}' conflicts with an existing alias.`,
      );
    }

    // Check alias conflicts
    for (const alias of descriptor.aliases) {
      if (this._descriptors.has(alias) || this._aliasMap.has(alias)) {
        this._rejectedRegistrationsCount++;
        throw new ServiceRegistrationException(
          `Alias '${alias}' for service '${serviceType}' conflicts with an existing service type or alias.`,
        );
      }
    }

    // Register descriptor and aliases
    this._descriptors.set(serviceType, descriptor);
    for (const alias of descriptor.aliases) {
      this._aliasMap.set(alias, serviceType);
    }

    return this;
  }

  public replace(descriptor: IServiceDescriptor): IServiceCollection {
    if (!descriptor) {
      this._rejectedRegistrationsCount++;
      throw new ServiceRegistrationException('Service descriptor cannot be null or undefined.');
    }

    const serviceType = descriptor.serviceType.trim();
    if (this.contains(serviceType)) {
      this.remove(serviceType);
      this._replacementsCount++;
    }

    this.register(descriptor);
    return this;
  }

  public tryAdd(descriptor: IServiceDescriptor): boolean {
    if (!descriptor) {
      this._rejectedRegistrationsCount++;
      return false;
    }

    const serviceType = descriptor.serviceType.trim();
    if (this._descriptors.has(serviceType) || this._aliasMap.has(serviceType)) {
      this._rejectedRegistrationsCount++;
      return false;
    }

    for (const alias of descriptor.aliases) {
      if (this._descriptors.has(alias) || this._aliasMap.has(alias)) {
        this._rejectedRegistrationsCount++;
        return false;
      }
    }

    try {
      this.register(descriptor);
      return true;
    } catch {
      this._rejectedRegistrationsCount++;
      return false;
    }
  }

  public remove(serviceType: string): boolean {
    const key = serviceType.trim();
    const existing = this._descriptors.get(key);
    if (!existing) {
      return false;
    }

    // Remove aliases associated with descriptor
    for (const alias of existing.aliases) {
      this._aliasMap.delete(alias);
    }

    this._descriptors.delete(key);
    this._removalsCount++;
    return true;
  }

  public removeAll(predicate: (descriptor: IServiceDescriptor) => boolean): number {
    let removedCount = 0;
    for (const descriptor of Array.from(this._descriptors.values())) {
      if (predicate(descriptor)) {
        if (this.remove(descriptor.serviceType)) {
          removedCount++;
        }
      }
    }
    return removedCount;
  }

  public contains(serviceType: string): boolean {
    const key = serviceType.trim();
    return this._descriptors.has(key) || this._aliasMap.has(key);
  }

  public containsAlias(alias: string): boolean {
    return this._aliasMap.has(alias.trim());
  }

  public getDescriptor(serviceType: string): IServiceDescriptor | undefined {
    const key = serviceType.trim();
    if (this._descriptors.has(key)) {
      return this._descriptors.get(key);
    }
    const mappedType = this._aliasMap.get(key);
    if (mappedType) {
      return this._descriptors.get(mappedType);
    }
    return undefined;
  }

  public getDescriptorByAlias(alias: string): IServiceDescriptor | undefined {
    const mappedType = this._aliasMap.get(alias.trim());
    if (mappedType) {
      return this._descriptors.get(mappedType);
    }
    return undefined;
  }

  public get(serviceType: string): IServiceDescriptor | undefined {
    return this.getDescriptor(serviceType);
  }

  public listServices(): ReadonlyArray<IServiceDescriptor> {
    return Object.freeze(Array.from(this._descriptors.values()));
  }

  public listByLifetime(lifetime: ServiceLifetime): ReadonlyArray<IServiceDescriptor> {
    const matches = Array.from(this._descriptors.values()).filter((d) => d.lifetime === lifetime);
    return Object.freeze(matches);
  }

  public listAliases(): ReadonlyArray<string> {
    return Object.freeze(Array.from(this._aliasMap.keys()));
  }

  public count(): number {
    return this._descriptors.size;
  }

  public clear(): void {
    this._descriptors.clear();
    this._aliasMap.clear();
  }

  public statistics(): ContainerStatistics {
    const services = this.listServices();
    let singletons = 0;
    let transients = 0;
    let scopeds = 0;

    for (const d of services) {
      if (d.lifetime === ServiceLifetime.SINGLETON) singletons++;
      else if (d.lifetime === ServiceLifetime.TRANSIENT) transients++;
      else if (d.lifetime === ServiceLifetime.SCOPED) scopeds++;
    }

    return createContainerStatistics({
      totalRegistrations: services.length,
      singletonCount: singletons,
      transientCount: transients,
      scopedCount: scopeds,
      replacementsCount: this._replacementsCount,
      removalsCount: this._removalsCount,
      rejectedRegistrationsCount: this._rejectedRegistrationsCount,
      aliasCount: this._aliasMap.size,
    });
  }
}
