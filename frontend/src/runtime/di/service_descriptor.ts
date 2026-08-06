/**
 * Service Descriptor Implementation (Phase 16.2.1).
 *
 * Implements IServiceDescriptor capturing service metadata, target implementation,
 * factory function, or singleton instance with immutability guarantees.
 */

import { createServiceDescriptorModel, ServiceDescriptorModel, ServiceLifetime } from './models';
import { IServiceDescriptor, IServiceProvider } from './interfaces';
import { ServiceRegistrationException } from './exceptions';

export class ServiceDescriptor implements IServiceDescriptor {
  public readonly serviceType: string;
  public readonly lifetime: ServiceLifetime;
  public readonly implementation?: new (...args: unknown[]) => unknown;
  public readonly factory?: (provider: IServiceProvider) => unknown;
  public readonly instance?: unknown;
  public readonly metadata: Readonly<Record<string, unknown>>;

  constructor(
    serviceType: string,
    lifetime: ServiceLifetime,
    target: unknown,
    metadata?: Record<string, unknown>,
  ) {
    if (!serviceType || typeof serviceType !== 'string' || serviceType.trim() === '') {
      throw new ServiceRegistrationException('Service type must be a non-empty string.');
    }
    if (target === undefined || target === null) {
      throw new ServiceRegistrationException(
        `Service target for '${serviceType}' cannot be null or undefined.`,
      );
    }

    this.serviceType = serviceType.trim();
    this.lifetime = lifetime;
    this.metadata = Object.freeze({ ...(metadata ?? {}) });

    if (typeof target === 'function') {
      // Determine if constructor or factory function
      if (this.isConstructor(target)) {
        this.implementation = target as new (...args: unknown[]) => unknown;
      } else {
        this.factory = target as (provider: IServiceProvider) => unknown;
      }
    } else {
      if (lifetime !== ServiceLifetime.SINGLETON) {
        throw new ServiceRegistrationException(
          `Instance registration for '${serviceType}' must use SINGLETON lifetime.`,
        );
      }
      this.instance = target;
    }
  }

  public toModel(): ServiceDescriptorModel {
    return createServiceDescriptorModel({
      serviceType: this.serviceType,
      lifetime: this.lifetime,
      implementationType: this.implementation ? this.implementation.name : undefined,
      hasFactory: this.factory !== undefined,
      hasInstance: this.instance !== undefined,
      metadata: this.metadata,
    });
  }

  private isConstructor(func: unknown): boolean {
    if (typeof func !== 'function') return false;
    // Native class or function with prototype.name/constructor
    try {
      const prototype = func.prototype;
      return !!(prototype && prototype.constructor === func);
    } catch {
      return false;
    }
  }
}
