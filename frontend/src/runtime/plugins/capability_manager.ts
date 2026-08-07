/**
 * Capability Manager Engine (Phase 16.7).
 *
 * Implements ICapabilityManager to register, remove, and list plugin capabilities
 * like commands, menus, panels, and views.
 */

import { PluginCapability, createPluginCapability } from './models';
import { ICapabilityManager } from './interfaces';

export class CapabilityManager implements ICapabilityManager {
  private readonly _capabilities = new Map<string, PluginCapability[]>();

  public registerCapability(pluginId: string, capability: PluginCapability): void {
    if (!this._capabilities.has(pluginId)) {
      this._capabilities.set(pluginId, []);
    }
    const list = this._capabilities.get(pluginId)!;
    list.push(createPluginCapability(capability));
  }

  public removeCapability(pluginId: string, capabilityName: string): boolean {
    const list = this._capabilities.get(pluginId);
    if (!list) return false;
    const index = list.findIndex(c => c.name === capabilityName);
    if (index === -1) return false;
    list.splice(index, 1);
    return true;
  }

  public listCapabilities(pluginId?: string): ReadonlyArray<PluginCapability> {
    if (pluginId) {
      return this._capabilities.get(pluginId) ?? [];
    }
    const all: PluginCapability[] = [];
    this._capabilities.forEach(list => all.push(...list));
    return all;
  }

  public resolveCapability(name: string): PluginCapability | undefined {
    const all = this.listCapabilities();
    return all.find(c => c.name === name);
  }

  public clear(): void {
    this._capabilities.clear();
  }
}
