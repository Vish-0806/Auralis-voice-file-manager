/**
 * Permission Engine (Phase 16.7).
 *
 * Implements IPermissionManager to manage plugin permissions, evaluate scopes
 * (filesystem, configuration, network, clipboard, etc.), and enforce security.
 */

import { PluginPermission, createPluginPermission } from './models';
import { IPermissionManager } from './interfaces';

export class PermissionManager implements IPermissionManager {
  private readonly _permissions = new Map<string, Map<string, PluginPermission>>();

  public grantPermission(pluginId: string, permission: PluginPermission): void {
    if (!this._permissions.has(pluginId)) {
      this._permissions.set(pluginId, new Map<string, PluginPermission>());
    }
    const pluginMap = this._permissions.get(pluginId)!;
    pluginMap.set(permission.scope, createPluginPermission(permission));
  }

  public revokePermission(pluginId: string, scope: string): boolean {
    const pluginMap = this._permissions.get(pluginId);
    if (!pluginMap) return false;
    return pluginMap.delete(scope);
  }

  public evaluatePermission(pluginId: string, scope: string): boolean {
    const pluginMap = this._permissions.get(pluginId);
    if (!pluginMap) return false;
    const perm = pluginMap.get(scope);
    return perm ? perm.required === true : false;
  }

  public listPermissions(pluginId: string): ReadonlyArray<PluginPermission> {
    const pluginMap = this._permissions.get(pluginId);
    if (!pluginMap) return [];
    return Array.from(pluginMap.values());
  }

  public clear(): void {
    this._permissions.clear();
  }
}
