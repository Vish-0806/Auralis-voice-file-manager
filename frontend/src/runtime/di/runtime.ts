/**
 * Global Dependency Injection Singleton Accessors (Phase 16.2.1).
 *
 * Provides lazy-initialized singleton accessors for global DependencyContainer
 * and ServiceProvider instances.
 */

import { IDependencyContainer, IServiceProvider } from './interfaces';
import { DependencyContainer } from './dependency_container';
import { ServiceProvider } from './service_provider';

let _globalDependencyContainer: IDependencyContainer | null = null;
let _globalServiceProvider: IServiceProvider | null = null;

export function getDependencyContainer(): IDependencyContainer {
  if (!_globalDependencyContainer) {
    const provider = getServiceProvider();
    _globalDependencyContainer = new DependencyContainer(provider);
  }
  return _globalDependencyContainer;
}

export function setDependencyContainer(container: IDependencyContainer): void {
  _globalDependencyContainer = container;
}

export function resetDependencyContainer(): void {
  _globalDependencyContainer = null;
}

export function getServiceProvider(): IServiceProvider {
  if (!_globalServiceProvider) {
    _globalServiceProvider = new ServiceProvider();
  }
  return _globalServiceProvider;
}

export function setServiceProvider(provider: IServiceProvider): void {
  _globalServiceProvider = provider;
}

export function resetServiceProvider(): void {
  _globalServiceProvider = null;
}
