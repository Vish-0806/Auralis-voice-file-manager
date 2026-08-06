/**
 * Service Descriptor Implementation (Phase 16.2.2).
 *
 * Implements IServiceDescriptor capturing unique descriptor ID, service type,
 * lifetime, implementation class, factory function, instance, aliases, tags,
 * registration timestamp, and immutable metadata.
 */

import { createServiceDescriptorModel, ServiceDescriptorModel, ServiceLifetime } from './models';
import { IServiceDescriptor, IServiceProvider, ServiceRegistrationOptions } from './interfaces';
import { ServiceRegistrationException } from './exceptions';

let _idCounter = 0;

export class ServiceDescriptor implements IServiceDescriptor {
  public readonly descriptorId: string;
  public readonly serviceType: string;
  public readonly lifetime: ServiceLifetime;
  public readonly implementation?: new (...args: unknown[]) => unknown;
  public readonly factory?: (provider: IServiceProvider) => unknown;
  public readonly instance?: unknown;
  public readonly aliases: ReadonlyArray<string>;
  public readonly tags: ReadonlyArray<string>;
  public readonly metadata: Readonly<Record<string, unknown>>;
  public readonly registeredAt: string;

  constructor(
    serviceType: string,
    lifetime: ServiceLifetime,
    target: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
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

    _idCounter++;
    this.descriptorId =
      options?.descriptorId ?? `desc_${Date.now()}_${_idCounter}_${Math.random().toString(36).substring(2, 7)}`;
    this.registeredAt = options?.registeredAt ?? new Date().toISOString();

    const rawAliases = options?.aliases ?? [];
    const cleanedAliases: string[] = [];
    for (const a of rawAliases) {
      if (typeof a !== 'string' || a.trim() === '') {
        throw new ServiceRegistrationException(
          `Alias for service '${this.serviceType}' must be a non-empty string.`,
        );
      }
      cleanedAliases.push(a.trim());
    }
    this.aliases = Object.freeze(cleanedAliases);

    const rawTags = options?.tags ?? [];
    const cleanedTags: string[] = [];
    for (const t of rawTags) {
      if (typeof t === 'string' && t.trim() !== '') {
        cleanedTags.push(t.trim());
      }
    }
    this.tags = Object.freeze(cleanedTags);

    if (typeof target === 'function') {
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

  public equals(other: IServiceDescriptor): boolean {
    if (!other) return false;
    return this.descriptorId === other.descriptorId || this.serviceType === other.serviceType;
  }

  public toModel(): ServiceDescriptorModel {
    return createServiceDescriptorModel({
      descriptorId: this.descriptorId,
      serviceType: this.serviceType,
      lifetime: this.lifetime,
      implementationType: this.implementation ? this.implementation.name : undefined,
      hasFactory: this.factory !== undefined,
      hasInstance: this.instance !== undefined,
      aliases: this.aliases,
      tags: this.tags,
      metadata: this.metadata,
      registeredAt: this.registeredAt,
    });
  }

  private isConstructor(func: unknown): boolean {
    if (typeof func !== 'function') return false;
    try {
      const prototype = func.prototype;
      return !!(prototype && prototype.constructor === func);
    } catch {
      return false;
    }
  }
}
