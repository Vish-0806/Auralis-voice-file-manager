/**
 * Sandbox Engine (Phase 16.7).
 *
 * Implements ISandboxManager to enforce capability restrictions, execution isolation,
 * resource constraints, and security runtime policies.
 */

import { PluginSandbox, createPluginSandbox } from './models';
import { ISandboxManager } from './interfaces';
import { PluginSandboxException } from './exceptions';

export class SandboxManager implements ISandboxManager {
  private readonly _sandboxes = new Map<string, PluginSandbox>();

  public applySandbox(pluginId: string, sandbox: PluginSandbox): void {
    this._sandboxes.set(pluginId, createPluginSandbox(sandbox));
  }

  public getSandbox(pluginId: string): PluginSandbox | undefined {
    return this._sandboxes.get(pluginId);
  }

  public validateAction(pluginId: string, actionType: string): boolean {
    const sandbox = this._sandboxes.get(pluginId);
    if (!sandbox) {
      // Default to strict restriction if sandbox metadata is missing
      throw new PluginSandboxException(`No sandbox configured for plugin '${pluginId}'.`);
    }

    if (sandbox.capabilityRestrictions.includes(actionType)) {
      return false;
    }

    if (sandbox.permissionRestrictions.includes(actionType)) {
      return false;
    }

    return true;
  }

  public clear(): void {
    this._sandboxes.clear();
  }
}
