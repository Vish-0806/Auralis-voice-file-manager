/**
 * Plugin Runtime Coordinator Implementation (Phase 16.7).
 *
 * Implements IPluginRuntime acting as central coordinator delegating to IPluginProvider.
 * Contains no business logic — all operations are forwarded to the provider instance.
 */

import {
  IPluginRuntime,
  IPluginProvider,
  IPluginRegistry,
  IPluginLoader,
  IPluginLifecycleManager,
  IDependencyResolver,
  ICapabilityManager,
  IServiceRegistry,
  IPermissionManager,
  ISandboxManager,
  IPluginValidator,
  IPluginDiagnostics,
  IPluginCertifier,
} from './interfaces';
import { PluginProvider } from './plugin_provider';

export class PluginRuntime implements IPluginRuntime {
  private readonly _provider: IPluginProvider;

  constructor(provider?: IPluginProvider) {
    this._provider = provider ?? new PluginProvider();
  }

  public initialize(): void {
    this._provider.initialize();
  }

  public shutdown(): void {
    this._provider.shutdown();
  }

  public getRegistry(): IPluginRegistry {
    return this._provider.registry();
  }

  public getLoader(): IPluginLoader {
    return this._provider.loader();
  }

  public getLifecycleManager(): IPluginLifecycleManager {
    return this._provider.lifecycleManager();
  }

  public getDependencyResolver(): IDependencyResolver {
    return this._provider.dependencyResolver();
  }

  public getCapabilityManager(): ICapabilityManager {
    return this._provider.capabilityManager();
  }

  public getServiceRegistry(): IServiceRegistry {
    return this._provider.serviceRegistry();
  }

  public getPermissionManager(): IPermissionManager {
    return this._provider.permissionManager();
  }

  public getSandboxManager(): ISandboxManager {
    return this._provider.sandboxManager();
  }

  public getValidator(): IPluginValidator {
    return this._provider.validator();
  }

  public getDiagnostics(): IPluginDiagnostics {
    return this._provider.diagnostics();
  }

  public getCertifier(): IPluginCertifier {
    return this._provider.certifier();
  }
}
