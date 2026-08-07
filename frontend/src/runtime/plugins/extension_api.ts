/**
 * Extension API Adapter Engine (Phase 16.7).
 *
 * Implements IExtensionAPI to expose safe, decoupled access to Configuration,
 * Events, State, Commands, Logging, and Services for registered plugins.
 */

import { IExtensionAPI, ICapabilityManager, IServiceRegistry } from './interfaces';
import { PluginCapability, PluginConfiguration, createPluginConfiguration } from './models';

// Import getters from sibling runtimes to delegate features
import { getEventRuntime } from '../events/runtime';
import { getCommandRuntime } from '../commands/runtime';
import { getConfigurationRuntime } from '../config/runtime';

export class ExtensionAPI implements IExtensionAPI {
  private readonly _capabilityManager: ICapabilityManager;
  private readonly _serviceRegistry: IServiceRegistry;

  constructor(capabilityManager: ICapabilityManager, serviceRegistry: IServiceRegistry) {
    this._capabilityManager = capabilityManager;
    this._serviceRegistry = serviceRegistry;
  }

  public getConfiguration(pluginId: string): PluginConfiguration {
    try {
      const configRuntime = getConfigurationRuntime();
      // Assume getConfigurationRuntime returns a configuration object. Let's fetch settings.
      const settings = configRuntime.get(`plugins.${pluginId}`) as Record<string, unknown>;
      return createPluginConfiguration({
        pluginId,
        settings: settings ?? {},
      });
    } catch {
      // Fallback if config runtime is not fully initialized or throws
      return createPluginConfiguration({
        pluginId,
        settings: {},
      });
    }
  }

  public dispatchEvent(eventName: string, payload: unknown): void {
    try {
      const eventRuntime = getEventRuntime();
      // Assume event runtime uses publish/dispatch event schema
      eventRuntime.publish({
        id: `evt_${Date.now()}`,
        type: eventName,
        payload,
        timestamp: new Date().toISOString(),
      });
    } catch {
      // Fail-silent or fallback log
    }
  }

  public async executeCommand(commandId: string, args: unknown): Promise<unknown> {
    try {
      const commandRuntime = getCommandRuntime();
      const result = await commandRuntime.execute({
        commandId,
        parameters: args as Record<string, unknown>,
      });
      return result.result;
    } catch (e: any) {
      throw new Error(`Failed to execute command '${commandId}' via Extension API: ${e.message}`);
    }
  }

  public log(pluginId: string, level: string, message: string): void {
    const formatted = `[Plugin:${pluginId}] [${level.toUpperCase()}] ${message}`;
    if (level === 'error') {
      console.error(formatted);
    } else if (level === 'warn') {
      console.warn(formatted);
    } else {
      console.log(formatted);
    }
  }

  public registerCapability(pluginId: string, capability: PluginCapability): void {
    this._capabilityManager.registerCapability(pluginId, capability);
  }

  public resolveService<T = unknown>(interfaceName: string): T | undefined {
    return this._serviceRegistry.resolveService<T>(interfaceName);
  }
}
