export interface PluginAuthor {
  readonly name: string;
  readonly email?: string;
  readonly url?: string;
}

export type PluginEntryPoint = string;

export interface PluginDependencyDeclaration {
  readonly id: string;
  readonly versionRange: string;
}

export interface PluginCapabilityDeclaration {
  readonly type: string;
  readonly properties: Record<string, unknown>;
}

export interface PluginManifest {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly description?: string;
  readonly author: string | PluginAuthor;
  readonly schemaVersion: string;
  readonly entryPoint: PluginEntryPoint;
  readonly dependencies: ReadonlyArray<PluginDependencyDeclaration>;
  readonly capabilities: ReadonlyArray<PluginCapabilityDeclaration>;
  readonly metadata?: Record<string, unknown>;
}

export interface PluginDiscoverySourceDescriptor {
  readonly id: string;
  readonly name: string;
  readonly type: string;
}

export interface PluginManifestValidationIssue {
  readonly code: string;
  readonly path: string;
  readonly severity: 'error' | 'warning';
  readonly message: string;
}

export interface PluginManifestValidationResult {
  readonly valid: boolean;
  readonly issues: ReadonlyArray<PluginManifestValidationIssue>;
}

export interface PluginDiscoveryResult {
  readonly success: boolean;
  readonly manifests: ReadonlyArray<PluginManifest>;
  readonly invalid: ReadonlyArray<{
    readonly sourceId: string;
    readonly error: string;
    readonly issues?: ReadonlyArray<PluginManifestValidationIssue>;
  }>;
  readonly duplicates: ReadonlyArray<string>;
  readonly failures: ReadonlyArray<{
    readonly sourceId: string;
    readonly error: string;
  }>;
}

export interface PluginDiscoveryStatistics {
  readonly discoveryAttempts: number;
  readonly discoveredPlugins: number;
  readonly validManifests: number;
  readonly invalidManifests: number;
  readonly duplicateAttempts: number;
  readonly discoveryFailures: number;
  readonly validationFailures: number;
  readonly registeredSources: number;
}

export interface PluginDiscoveryHealth {
  readonly healthy: boolean;
  readonly message: string;
  readonly issues: ReadonlyArray<string>;
}

export function freezeDeep<T>(value: T): T {
  if (Array.isArray(value)) {
    const arrayValue = value.map((item) => freezeDeep(item));
    return Object.freeze(arrayValue) as T;
  }

  if (value && typeof value === 'object') {
    const objectValue = value as Record<string, unknown>;
    Object.keys(objectValue).forEach((key) => {
      const nestedValue = objectValue[key];
      if (nestedValue && typeof nestedValue === 'object') {
        objectValue[key] = freezeDeep(nestedValue);
      }
    });
    return Object.freeze(objectValue) as T;
  }

  return value;
}
