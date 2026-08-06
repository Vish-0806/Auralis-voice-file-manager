/**
 * Dependency Injection Interfaces (Phase 16.2.1).
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

export interface IServiceDescriptor {
  readonly serviceType: string;
  readonly lifetime: ServiceLifetime;
  readonly implementation?: new (...args: unknown[]) => unknown;
  readonly factory?: (provider: IServiceProvider) => unknown;
  readonly instance?: unknown;
  readonly metadata: Readonly<Record<string, unknown>>;
  toModel(): ServiceDescriptorModel;
}

export interface IServiceCollection {
  addSingleton(
    serviceType: string,
    implementationOrFactoryOrInstance: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection;
  addTransient(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection;
  addScoped(
    serviceType: string,
    implementationOrFactory: unknown,
    metadata?: Record<string, unknown>,
  ): IServiceCollection;
  remove(serviceType: string): boolean;
  contains(serviceType: string): boolean;
  count(): number;
  clear(): void;
  listServices(): ReadonlyArray<IServiceDescriptor>;
  get(serviceType: string): IServiceDescriptor | undefined;
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
