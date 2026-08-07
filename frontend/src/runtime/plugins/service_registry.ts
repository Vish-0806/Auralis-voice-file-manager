/**
 * Service Registry Engine (Phase 16.7).
 *
 * Implements IServiceRegistry to handle dynamic plugin service registration,
 * dependency injection, and scope resolution (singleton, transient, scoped).
 */

import { PluginService, createPluginService } from './models';
import { IServiceRegistry } from './interfaces';

interface RegisteredService {
  service: PluginService;
  factory: () => unknown;
  instance?: unknown;
}

export class ServiceRegistry implements IServiceRegistry {
  private readonly _services = new Map<string, RegisteredService>();

  public registerService(pluginId: string, service: PluginService, instanceFactory: () => unknown): void {
    const key = service.interfaceName;
    if (this._services.has(key)) {
      throw new Error(`Service '${key}' is already registered.`);
    }
    this._services.set(key, {
      service: createPluginService({ ...service, pluginId }),
      factory: instanceFactory,
    });
  }

  public resolveService<T = unknown>(interfaceName: string): T | undefined {
    const registration = this._services.get(interfaceName);
    if (!registration) return undefined;

    if (registration.service.scope === 'singleton') {
      if (registration.instance === undefined) {
        registration.instance = registration.factory();
      }
      return registration.instance as T;
    }

    // For transient/transient or scoped, execute factory every time (or use scoped logic)
    return registration.factory() as T;
  }

  public replaceService(pluginId: string, service: PluginService, instanceFactory: () => unknown): void {
    const key = service.interfaceName;
    this._services.set(key, {
      service: createPluginService({ ...service, pluginId }),
      factory: instanceFactory,
    });
  }

  public clear(): void {
    this._services.clear();
  }
}
