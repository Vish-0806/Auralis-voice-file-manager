/**
 * Plugin Provider Implementation (Phase 16.7).
 *
 * Implements IPluginProvider which instantiates and holds references to all
 * runtime subsystems, delegating APIs and coordinating lifecycle events.
 */

import {
  IPluginProvider,
  IPluginRegistry,
  IPluginManifestLoader,
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

import { PluginRegistry } from './plugin_registry';
import { PluginManifestLoader } from './plugin_manifest';
import { PluginLoader } from './plugin_loader';
import { PluginLifecycleManager } from './plugin_lifecycle';
import { DependencyResolver } from './dependency_resolver';
import { CapabilityManager } from './capability_manager';
import { ServiceRegistry } from './service_registry';
import { PermissionManager } from './plugin_permissions';
import { SandboxManager } from './plugin_sandbox';
import { PluginValidator } from './plugin_validator';
import { PluginDiagnosticsManager } from './plugin_diagnostics';
import { PluginCertifier } from './plugin_certifier';

export class PluginProvider implements IPluginProvider {
  private readonly _registry: IPluginRegistry;
  private readonly _manifestLoader: IPluginManifestLoader;
  private readonly _loader: IPluginLoader;
  private readonly _lifecycleManager: IPluginLifecycleManager;
  private readonly _dependencyResolver: IDependencyResolver;
  private readonly _capabilityManager: ICapabilityManager;
  private readonly _serviceRegistry: IServiceRegistry;
  private readonly _permissionManager: IPermissionManager;
  private readonly _sandboxManager: ISandboxManager;
  private readonly _validator: IPluginValidator;
  private readonly _diagnostics: IPluginDiagnostics;
  private readonly _certifier: IPluginCertifier;

  constructor(
    registry?: IPluginRegistry,
    manifestLoader?: IPluginManifestLoader,
    loader?: IPluginLoader,
    lifecycleManager?: IPluginLifecycleManager,
    dependencyResolver?: IDependencyResolver,
    capabilityManager?: ICapabilityManager,
    serviceRegistry?: IServiceRegistry,
    permissionManager?: IPermissionManager,
    sandboxManager?: ISandboxManager,
    validator?: IPluginValidator,
    diagnostics?: IPluginDiagnostics,
    certifier?: IPluginCertifier,
  ) {
    this._registry = registry ?? new PluginRegistry();
    this._manifestLoader = manifestLoader ?? new PluginManifestLoader();
    this._loader = loader ?? new PluginLoader();
    this._lifecycleManager = lifecycleManager ?? new PluginLifecycleManager();
    this._dependencyResolver = dependencyResolver ?? new DependencyResolver();
    this._capabilityManager = capabilityManager ?? new CapabilityManager();
    this._serviceRegistry = serviceRegistry ?? new ServiceRegistry();
    this._permissionManager = permissionManager ?? new PermissionManager();
    this._sandboxManager = sandboxManager ?? new SandboxManager();
    this._validator = validator ?? new PluginValidator();

    this._diagnostics =
      diagnostics ?? new PluginDiagnosticsManager(this._registry, this._loader);

    this._certifier =
      certifier ??
      new PluginCertifier(
        this._registry,
        this._validator,
        this._diagnostics,
        this._sandboxManager,
      );
  }

  public initialize(): void {
    // Initial setup if required by subclasses
  }

  public shutdown(): void {
    this._registry.clear();
    this._capabilityManager.clear();
    this._serviceRegistry.clear();
    this._permissionManager.clear();
    this._sandboxManager.clear();
    this._certifier.clear();
  }

  public registry(): IPluginRegistry {
    return this._registry;
  }

  public manifestLoader(): IPluginManifestLoader {
    return this._manifestLoader;
  }

  public loader(): IPluginLoader {
    return this._loader;
  }

  public lifecycleManager(): IPluginLifecycleManager {
    return this._lifecycleManager;
  }

  public dependencyResolver(): IDependencyResolver {
    return this._dependencyResolver;
  }

  public capabilityManager(): ICapabilityManager {
    return this._capabilityManager;
  }

  public serviceRegistry(): IServiceRegistry {
    return this._serviceRegistry;
  }

  public permissionManager(): IPermissionManager {
    return this._permissionManager;
  }

  public sandboxManager(): ISandboxManager {
    return this._sandboxManager;
  }

  public validator(): IPluginValidator {
    return this._validator;
  }

  public diagnostics(): IPluginDiagnostics {
    return this._diagnostics;
  }

  public certifier(): IPluginCertifier {
    return this._certifier;
  }
}
