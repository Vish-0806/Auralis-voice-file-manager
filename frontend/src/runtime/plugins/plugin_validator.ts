/**
 * Validation Engine (Phase 16.7).
 *
 * Implements IPluginValidator to validate plugin manifests, capabilities constraints,
 * and permissions schemas.
 */

import {
  PluginManifest,
  PluginCapability,
  PluginPermission,
  PluginValidationResult,
  createPluginValidationResult,
  createPluginValidationIssue,
} from './models';
import { IPluginValidator } from './interfaces';
import { PluginManifestLoader } from './plugin_manifest';

export class PluginValidator implements IPluginValidator {
  private readonly _manifestLoader = new PluginManifestLoader();

  public validateManifest(manifest: PluginManifest): PluginValidationResult {
    return this._manifestLoader.validate(manifest);
  }

  public validateCapabilities(pluginId: string, capabilities: ReadonlyArray<PluginCapability>): PluginValidationResult {
    const issues: any[] = [];

    capabilities.forEach((cap, index) => {
      if (!cap.type || typeof cap.type !== 'string') {
        issues.push(createPluginValidationIssue({
          severity: 'error',
          path: `capabilities[${index}].type`,
          message: 'Capability type must be a non-empty string.',
        }));
      }
      if (!cap.name || typeof cap.name !== 'string') {
        issues.push(createPluginValidationIssue({
          severity: 'error',
          path: `capabilities[${index}].name`,
          message: 'Capability name must be a non-empty string.',
        }));
      }
    });

    return createPluginValidationResult({
      pluginId,
      valid: issues.length === 0,
      issues,
    });
  }

  public validatePermissions(pluginId: string, permissions: ReadonlyArray<PluginPermission>): PluginValidationResult {
    const issues: any[] = [];

    permissions.forEach((perm, index) => {
      if (!perm.scope || typeof perm.scope !== 'string') {
        issues.push(createPluginValidationIssue({
          severity: 'error',
          path: `permissions[${index}].scope`,
          message: 'Permission scope must be a non-empty string.',
        }));
      }
    });

    return createPluginValidationResult({
      pluginId,
      valid: issues.length === 0,
      issues,
    });
  }
}
