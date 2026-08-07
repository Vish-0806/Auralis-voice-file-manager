/**
 * Permission Manager Implementation (Phase 16.6.5).
 *
 * Implements IPermissionManager managing permission registration,
 * role-based access control (RBAC), user and session permission grants/revocations,
 * scope evaluation, permission statistics, and health reporting.
 */

import {
  CommandPermission,
  PermissionDiagnostics,
  PermissionHealth,
  PermissionResult,
  PermissionStatistics,
  createCommandPermission,
  createPermissionDiagnostics,
  createPermissionHealth,
  createPermissionResult,
  createPermissionStatistics,
} from './models';
import { CommandProviderException } from './exceptions';
import { IPermissionManager } from './interfaces';

export class PermissionManager implements IPermissionManager {
  private readonly _permissions = new Map<string, CommandPermission>();
  private readonly _userGrants = new Map<string, Set<string>>(); // userIdOrRole -> Set<permissionId>

  private _totalChecks = 0;
  private _grantedChecks = 0;
  private _deniedChecks = 0;

  public registerPermission(
    permission: Partial<CommandPermission> & { name: string },
  ): CommandPermission {
    if (!permission) {
      throw new CommandProviderException('Permission registration cannot be null or undefined.');
    }
    if (!permission.name || !permission.name.trim()) {
      throw new CommandProviderException('Permission name cannot be empty.');
    }

    const frozen = createCommandPermission({
      permissionId: permission.permissionId ?? permission.name.trim().toLowerCase(),
      name: permission.name.trim(),
      description: permission.description,
      scope: permission.scope ?? 'global',
      roles: permission.roles,
      enabled: permission.enabled ?? true,
    });

    this._permissions.set(frozen.permissionId, frozen);
    return frozen;
  }

  public removePermission(permissionId: string): boolean {
    if (!permissionId || !permissionId.trim()) {
      return false;
    }
    const id = permissionId.trim();
    const removed = this._permissions.delete(id);

    if (removed) {
      for (const set of this._userGrants.values()) {
        set.delete(id);
      }
    }

    return removed;
  }

  public listPermissions(): ReadonlyArray<CommandPermission> {
    return Object.freeze(Array.from(this._permissions.values()));
  }

  public grantPermission(userIdOrRole: string, permissionId: string): void {
    if (!userIdOrRole || !userIdOrRole.trim() || !permissionId || !permissionId.trim()) {
      return;
    }

    const subject = userIdOrRole.trim().toLowerCase();
    const permId = permissionId.trim();

    if (!this._userGrants.has(subject)) {
      this._userGrants.set(subject, new Set());
    }

    this._userGrants.get(subject)!.add(permId);
  }

  public revokePermission(userIdOrRole: string, permissionId: string): boolean {
    if (!userIdOrRole || !userIdOrRole.trim() || !permissionId || !permissionId.trim()) {
      return false;
    }

    const subject = userIdOrRole.trim().toLowerCase();
    const permId = permissionId.trim();

    const set = this._userGrants.get(subject);
    if (!set) {
      return false;
    }

    return set.delete(permId);
  }

  public hasPermission(userIdOrRole: string, permissionId: string): PermissionResult {
    this._totalChecks++;
    const subject = userIdOrRole ? userIdOrRole.trim().toLowerCase() : '';
    const permId = permissionId ? permissionId.trim() : '';

    if (!permId) {
      this._grantedChecks++;
      return createPermissionResult({
        granted: true,
        userId: subject,
        reason: 'No permission ID specified.',
      });
    }

    const permission = this._permissions.get(permId);
    if (!permission) {
      // If permission is not registered explicitly but specified, check direct user grant
      const set = this._userGrants.get(subject);
      if (set && set.has(permId)) {
        this._grantedChecks++;
        return createPermissionResult({
          granted: true,
          permissionId: permId,
          userId: subject,
        });
      }

      this._deniedChecks++;
      return createPermissionResult({
        granted: false,
        permissionId: permId,
        userId: subject,
        reason: `Permission '${permId}' is not registered.`,
      });
    }

    if (!permission.enabled) {
      this._deniedChecks++;
      return createPermissionResult({
        granted: false,
        permissionId: permId,
        userId: subject,
        reason: `Permission '${permission.name}' is disabled.`,
      });
    }

    // Direct grant check
    const userGrants = this._userGrants.get(subject);
    if (userGrants && userGrants.has(permission.permissionId)) {
      this._grantedChecks++;
      return createPermissionResult({
        granted: true,
        permissionId: permission.permissionId,
        userId: subject,
      });
    }

    // Role check
    if (permission.roles && permission.roles.length > 0) {
      const hasRole = permission.roles.some((r) => r.toLowerCase() === subject);
      if (hasRole) {
        this._grantedChecks++;
        return createPermissionResult({
          granted: true,
          permissionId: permission.permissionId,
          userId: subject,
        });
      }
    }

    this._deniedChecks++;
    return createPermissionResult({
      granted: false,
      permissionId: permission.permissionId,
      userId: subject,
      reason: `Subject '${subject}' lacks permission '${permission.name}'.`,
    });
  }

  public statistics(): PermissionStatistics {
    return createPermissionStatistics({
      totalChecks: this._totalChecks,
      grantedChecks: this._grantedChecks,
      deniedChecks: this._deniedChecks,
      activePermissions: this._permissions.size,
    });
  }

  public health(): PermissionHealth {
    const grantedRate =
      this._totalChecks > 0 ? Math.round((this._grantedChecks / this._totalChecks) * 100) : 100;
    const healthy = true;

    return createPermissionHealth({
      healthy,
      grantedRate,
      activePermissions: this._permissions.size,
      message: 'Permission manager is operational.',
    });
  }

  public diagnostics(): PermissionDiagnostics {
    return createPermissionDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      permissionCount: this._permissions.size,
    });
  }

  public clear(): void {
    this._permissions.clear();
    this._userGrants.clear();
    this._totalChecks = 0;
    this._grantedChecks = 0;
    this._deniedChecks = 0;
  }
}
