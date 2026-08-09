import { freezeDeepSafe } from './dependency';

export const PluginCapabilityType = {
  COMMAND: 'COMMAND',
  SERVICE: 'SERVICE',
  EVENT: 'EVENT',
  VIEW: 'VIEW',
  WORKSPACE: 'WORKSPACE',
  FILE_OPERATION: 'FILE_OPERATION',
  ASSISTANT: 'ASSISTANT',
  CUSTOM: 'CUSTOM'
} as const;
export type PluginCapabilityTypeValue = typeof PluginCapabilityType[keyof typeof PluginCapabilityType] | string;

export interface PluginCapability {
  readonly id: string;
  readonly pluginId: string;
  readonly name: string;
  readonly type: PluginCapabilityTypeValue;
  readonly version: string;
  readonly description?: string;
  readonly metadata: Record<string, unknown>;
  readonly enabled: boolean;
  readonly registeredAt: number;
}

export interface PluginCapabilityRegistration {
  readonly id: string;
  readonly name: string;
  readonly type: PluginCapabilityTypeValue;
  readonly version: string;
  readonly description?: string;
  readonly metadata?: Record<string, unknown>;
}

export interface PluginCapabilityResult {
  readonly success: boolean;
  readonly capabilityId: string;
  readonly pluginId: string;
  readonly currentState: string;
  readonly warnings: ReadonlyArray<string>;
  readonly errors: ReadonlyArray<string>;
  readonly timestamp: number;
}

export interface ExtensionPoint {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly description?: string;
  readonly acceptedTypes: ReadonlyArray<PluginCapabilityTypeValue>;
  readonly cardinality: 'SINGLE' | 'MANY';
  readonly enabled: boolean;
  readonly metadata: Record<string, unknown>;
}

export interface ExtensionRegistration {
  readonly extensionId: string;
  readonly pluginId: string;
  readonly extensionPointId: string;
  readonly capabilityId?: string;
  readonly priority: number;
  readonly enabled: boolean;
  readonly metadata: Record<string, unknown>;
  readonly registeredAt: number;
}

export interface ExtensionResult {
  readonly success: boolean;
  readonly extensionId: string;
  readonly pluginId: string;
  readonly extensionPointId: string;
  readonly warnings: ReadonlyArray<string>;
  readonly errors: ReadonlyArray<string>;
  readonly timestamp: number;
}

export interface CapabilityStatistics {
  readonly registeredCapabilities: number;
  readonly removedCapabilities: number;
  readonly activeCapabilities: number;
  readonly failedRegistrations: number;
  readonly duplicateAttempts: number;
  readonly conflictAttempts: number;
  readonly capabilityLookups: number;
}

export interface ExtensionStatistics {
  readonly registeredExtensions: number;
  readonly removedExtensions: number;
  readonly activeExtensions: number;
  readonly failedRegistrations: number;
  readonly duplicateAttempts: number;
  readonly conflictAttempts: number;
  readonly extensionLookups: number;
}

export interface CapabilityHealth {
  readonly healthy: boolean;
  readonly capabilityCount: number;
  readonly pluginCount: number;
  readonly failureRate: number;
  readonly duplicateCount: number;
  readonly conflictCount: number;
  readonly message: string;
}

export interface ExtensionHealth {
  readonly healthy: boolean;
  readonly extensionCount: number;
  readonly extensionPointCount: number;
  readonly pluginCount: number;
  readonly failureRate: number;
  readonly conflictCount: number;
  readonly message: string;
}

export interface CapabilityDiagnostics {
  readonly statistics: CapabilityStatistics;
  readonly health: CapabilityHealth;
  readonly capabilityCount: number;
  readonly extensionCount: number;
  readonly extensionPointCount: number;
  readonly registeredPluginCount: number;
  readonly lastRegistrationMetadata?: {
    readonly pluginId: string;
    readonly id: string;
    readonly type: 'capability' | 'extension' | 'extensionPoint';
    readonly timestamp: number;
  };
}

export function createCapabilityResult(input: Omit<PluginCapabilityResult, typeof Symbol.toStringTag>): PluginCapabilityResult {
  return freezeDeepSafe(input);
}

export function createExtensionResult(input: Omit<ExtensionResult, typeof Symbol.toStringTag>): ExtensionResult {
  return freezeDeepSafe(input);
}
