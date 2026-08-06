/**
 * Dependency Injection Interfaces (Phase 16.2.2).
 *
 * Defines contracts for IServiceDescriptor, IServiceCollection, IServiceProvider,
 * and IDependencyContainer.
 */

import {
  ContainerCapabilities,
  ContainerConfiguration,
  ContainerContext,
  ContainerDiagnostics,
  ContainerHealth,
  ContainerState,
  ContainerStatistics,
  ServiceDescriptorModel,
  ServiceLifetime,
} from './models';

export interface ServiceRegistrationOptions {
  descriptorId?: string;
  aliases?: string[];
  tags?: string[];
  registeredAt?: string;
}

export interface IServiceDescriptor {
  readonly descriptorId: string;
  readonly serviceType: string;
  readonly lifetime: ServiceLifetime;
  readonly implementation?: new (...args: unknown[]) => unknown;
  readonly factory?: (provider: IServiceProvider) => unknown;
  readonly instance?: unknown;
  readonly aliases: ReadonlyArray<string>;
  readonly tags: ReadonlyArray<string>;
  readonly metadata: Readonly<Record<string, unknown>>;
  readonly registeredAt: string;

  equals(other: IServiceDescriptor): boolean;
  toModel(): ServiceDescriptorModel;
}

export interface IServiceCollection {
  addSingleton(
    serviceType: string,
    implementationOrFactoryOrInstance: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection;

  addTransient(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection;

  addScoped(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
    options?: ServiceRegistrationOptions,
  ): IServiceCollection;

  register(descriptor: IServiceDescriptor): IServiceCollection;
  replace(descriptor: IServiceDescriptor): IServiceCollection;
  tryAdd(descriptor: IServiceDescriptor): boolean;

  remove(serviceType: string): boolean;
  removeAll(predicate: (descriptor: IServiceDescriptor) => boolean): number;
  contains(serviceType: string): boolean;
  containsAlias(alias: string): boolean;

  getDescriptor(serviceType: string): IServiceDescriptor | undefined;
  getDescriptorByAlias(alias: string): IServiceDescriptor | undefined;
  get(serviceType: string): IServiceDescriptor | undefined;

  listServices(): ReadonlyArray<IServiceDescriptor>;
  listByLifetime(lifetime: ServiceLifetime): ReadonlyArray<IServiceDescriptor>;
  listAliases(): ReadonlyArray<string>;

  count(): number;
  clear(): void;
  statistics(): ContainerStatistics;
}

export interface IServiceProvider {
  initialize(): ContainerHealth;
  shutdown(): ContainerHealth;
  restart(): ContainerHealth;
  health(): ContainerHealth;
  statistics(): ContainerStatistics;
  capabilities(): ContainerCapabilities;
  diagnostics(): ContainerDiagnostics;
  state(): ContainerState;
  configuration(): ContainerConfiguration;
  context(): ContainerContext;

  resolve<T>(serviceType: string): T;
  tryResolve<T>(serviceType: string): T | undefined;
}

export interface IDependencyContainer {
  initialize(): ContainerHealth;
  shutdown(): ContainerHealth;
  restart(): ContainerHealth;
  health(): ContainerHealth;
  statistics(): ContainerStatistics;
  capabilities(): ContainerCapabilities;
  diagnostics(): ContainerDiagnostics;
  state(): ContainerState;
  provider(): IServiceProvider;
  collection(): IServiceCollection;
}
