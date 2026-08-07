/**
 * Plugin Manifest Engine (Phase 16.7).
 *
 * Implements IPluginManifestLoader to parse plugin manifests, validate schemas,
 * verify engine and semantic version range compatibility.
 */

import {
  PluginManifest,
  PluginValidationResult,
  PluginCompatibilityResult,
  createPluginManifest,
  createPluginValidationResult,
  createPluginValidationIssue,
  createPluginCompatibilityResult,
  createPluginVersion,
} from './models';
import { IPluginManifestLoader } from './interfaces';
import { PluginValidationException } from './exceptions';

export class PluginManifestLoader implements IPluginManifestLoader {
  public parse(rawJson: string): PluginManifest {
    try {
      const parsed = JSON.parse(rawJson);
      if (!parsed.id || !parsed.name) {
        throw new PluginValidationException("Manifest must contain at least 'id' and 'name'.");
      }
      return createPluginManifest(parsed);
    } catch (e: any) {
      throw new PluginValidationException(`Failed to parse manifest: ${e.message}`);
    }
  }

  public validate(manifest: PluginManifest): PluginValidationResult {
    const issues: any[] = [];

    if (!manifest.id || typeof manifest.id !== 'string' || manifest.id.trim() === '') {
      issues.push(createPluginValidationIssue({
        severity: 'error',
        path: 'id',
        message: "Plugin ID must be a non-empty string.",
      }));
    }

    if (!manifest.name || typeof manifest.name !== 'string' || manifest.name.trim() === '') {
      issues.push(createPluginValidationIssue({
        severity: 'error',
        path: 'name',
        message: "Plugin name must be a non-empty string.",
      }));
    }

    if (!manifest.version || !this.isValidSemVer(manifest.version)) {
      issues.push(createPluginValidationIssue({
        severity: 'error',
        path: 'version',
        message: `Version '${manifest.version}' is not a valid Semantic Version.`,
      }));
    }

    // Validate main entrypoint
    if (!manifest.main || typeof manifest.main !== 'string' || manifest.main.trim() === '') {
      issues.push(createPluginValidationIssue({
        severity: 'error',
        path: 'main',
        message: "Main entry point must be a non-empty string.",
      }));
    }

    // Validate dependencies
    if (manifest.dependencies) {
      manifest.dependencies.forEach((dep, index) => {
        if (!dep.id || typeof dep.id !== 'string') {
          issues.push(createPluginValidationIssue({
            severity: 'error',
            path: `dependencies[${index}].id`,
            message: "Dependency ID must be a string.",
          }));
        }
        if (!dep.versionRange || typeof dep.versionRange !== 'string') {
          issues.push(createPluginValidationIssue({
            severity: 'error',
            path: `dependencies[${index}].versionRange`,
            message: "Dependency versionRange must be a string.",
          }));
        }
      });
    }

    return createPluginValidationResult({
      pluginId: manifest.id,
      valid: issues.every(i => i.severity !== 'error'),
      issues,
    });
  }

  public verifyCompatibility(manifest: PluginManifest, engineVersion: string): PluginCompatibilityResult {
    let engineMatch = true;
    const details: Record<string, string> = {};

    if (manifest.engineVersion && engineVersion) {
      engineMatch = this.satisfiesRange(engineVersion, manifest.engineVersion);
      details.engineVersionConstraint = manifest.engineVersion;
      details.currentEngineVersion = engineVersion;
      details.engineMatch = engineMatch ? 'compatible' : 'incompatible';
    }

    return createPluginCompatibilityResult({
      pluginId: manifest.id,
      compatible: engineMatch,
      engineMatch,
      dependencyMatch: true, // evaluated separately by dependency resolver
      details,
    });
  }

  // SemVer Helper methods
  public isValidSemVer(version: string): boolean {
    const semverRegex = /^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$/;
    return semverRegex.test(version);
  }

  public satisfiesRange(version: string, range: string): boolean {
    if (range === '*' || range === '') {
      return true;
    }

    // Simple parser for ^x.y.z or ~x.y.z or >=x.y.z
    const cleanRange = range.trim();
    const current = this.parseSemVer(version);

    if (cleanRange.startsWith('^')) {
      const target = this.parseSemVer(cleanRange.slice(1));
      if (target.major !== current.major) return false;
      if (target.major === 0) {
        if (target.minor === 0) {
          return current.minor === 0 && current.patch === target.patch;
        }
        if (current.minor !== target.minor) return false;
        return current.patch >= target.patch;
      }
      if (current.minor < target.minor) return false;
      if (current.minor === target.minor && current.patch < target.patch) return false;
      return true;
    }

    if (cleanRange.startsWith('~')) {
      const target = this.parseSemVer(cleanRange.slice(1));
      if (target.major !== current.major || target.minor !== current.minor) return false;
      if (current.patch < target.patch) return false;
      return true;
    }

    if (cleanRange.startsWith('>=')) {
      const target = this.parseSemVer(cleanRange.slice(2));
      if (current.major > target.major) return true;
      if (current.major < target.major) return false;
      if (current.minor > target.minor) return true;
      if (current.minor < target.minor) return false;
      return current.patch >= target.patch;
    }

    if (cleanRange.startsWith('=')) {
      return version === cleanRange.slice(1);
    }

    return version === cleanRange;
  }

  private parseSemVer(version: string) {
    const parts = version.split('-');
    const mainParts = parts[0].split('.');
    return {
      major: parseInt(mainParts[0], 10) || 0,
      minor: parseInt(mainParts[1], 10) || 0,
      patch: parseInt(mainParts[2], 10) || 0,
    };
  }
}
