import { freezeDeepSafe } from './dependency';

export const PluginPermissionScope = {
  GLOBAL: 'GLOBAL',
  PLUGIN: 'PLUGIN',
  SESSION: 'SESSION',
  WORKSPACE: 'WORKSPACE',
  USER: 'USER'
} as const;
export type PluginPermissionScopeValue = typeof PluginPermissionScope[keyof typeof PluginPermissionScope];

export const PluginPermissionAction = {
  READ_FILES: 'READ_FILES',
  WRITE_FILES: 'WRITE_FILES',
  DELETE_FILES: 'DELETE_FILES',
  EXECUTE_COMMANDS: 'EXECUTE_COMMANDS',
  NETWORK_ACCESS: 'NETWORK_ACCESS',
  CLIPBOARD_READ: 'CLIPBOARD_READ',
  CLIPBOARD_WRITE: 'CLIPBOARD_WRITE',
  VOICE_ACCESS: 'VOICE_ACCESS',
  AI_ACCESS: 'AI_ACCESS',
  SYSTEM_ACCESS: 'SYSTEM_ACCESS',
  PROCESS_ACCESS: 'PROCESS_ACCESS',
  EXTENSION_REGISTER: 'EXTENSION_REGISTER',
  EVENT_SUBSCRIBE: 'EVENT_SUBSCRIBE',
  EVENT_PUBLISH: 'EVENT_PUBLISH',
  CONFIG_READ: 'CONFIG_READ',
  CONFIG_WRITE: 'CONFIG_WRITE'
} as const;
export type PluginPermissionActionValue = typeof PluginPermissionAction[keyof typeof PluginPermissionAction] | string;

export interface PluginPermission {
  readonly id: string;
  readonly pluginId: string;
  readonly action: PluginPermissionActionValue;
  readonly scope: PluginPermissionScopeValue;
  readonly granted: boolean;
  readonly description?: string;
  readonly createdAt: number;
  readonly expiresAt?: number;
}

export interface PluginResourceLimits {
  readonly maxMemory?: number;
  readonly maxExecutionTime?: number;
  readonly maxConcurrentOperations?: number;
  readonly maxRequestsPerMinute?: number;
  readonly maxQueueDepth?: number;
  readonly maxSubscriptions?: number;
  readonly maxExtensions?: number;
}

export interface PluginSecurityPolicy {
  readonly id: string;
  readonly name: string;
  readonly description?: string;
  readonly priority: number;
  readonly enabled: boolean;
  readonly action: PluginPermissionActionValue;
  readonly scopes: ReadonlyArray<PluginPermissionScopeValue>;
  readonly effect: 'ALLOW' | 'DENY';
  readonly targetPluginId?: string;
  readonly predicateMetadata?: Record<string, unknown>;
}

export interface PluginSecurityProfile {
  readonly pluginId: string;
  readonly enabled: boolean;
  readonly permissions: ReadonlyArray<PluginPermission>;
  readonly policies: ReadonlyArray<PluginSecurityPolicy>;
  readonly resourceLimits: PluginResourceLimits;
  readonly allowedCapabilities: ReadonlyArray<string>;
  readonly deniedCapabilities: ReadonlyArray<string>;
  readonly createdAt: number;
  readonly updatedAt: number;
}

export interface PluginSecurityDecision {
  readonly decisionId: string;
  readonly pluginId: string;
  readonly action: PluginPermissionActionValue;
  readonly scope: PluginPermissionScopeValue;
  readonly allowed: boolean;
  readonly reason: string;
  readonly matchedPolicyId?: string;
  readonly matchedPermissionId?: string;
  readonly timestamp: number;
}

export interface PluginSecurityViolation {
  readonly violationId: string;
  readonly pluginId: string;
  readonly action: PluginPermissionActionValue;
  readonly reason: string;
  readonly severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  readonly timestamp: number;
  readonly metadata: Record<string, unknown>;
}

export interface PluginAuditRecord {
  readonly auditId: string;
  readonly pluginId: string;
  readonly eventType: string;
  readonly action: PluginPermissionActionValue;
  readonly allowed: boolean;
  readonly reason: string;
  readonly timestamp: number;
  readonly metadata: Record<string, unknown>;
}

export interface PluginSecurityStatistics {
  readonly totalDecisions: number;
  readonly allowedDecisions: number;
  readonly deniedDecisions: number;
  readonly violations: number;
  readonly criticalViolations: number;
  readonly policyDenials: number;
  readonly permissionDenials: number;
  readonly capabilityDenials: number;
  readonly sandboxDenials: number;
}

export interface PluginSecurityHealth {
  readonly healthy: boolean;
  readonly permissionCount: number;
  readonly policyCount: number;
  readonly activeSandboxCount: number;
  readonly violationRate: number;
  readonly denialRate: number;
  readonly message: string;
}

export interface PluginSecurityDiagnostics {
  readonly statistics: PluginSecurityStatistics;
  readonly health: PluginSecurityHealth;
  readonly registeredPermissions: number;
  readonly registeredPolicies: number;
  readonly securityProfiles: number;
  readonly activeSandboxes: number;
  readonly auditHistorySize: number;
  readonly averageEvaluationTime: number;
  readonly maximumEvaluationTime: number;
  readonly minimumEvaluationTime: number;
}

export interface PluginSandboxConfiguration {
  readonly sandboxId: string;
  readonly pluginId: string;
  readonly securityProfileId?: string;
  readonly resourceLimits: PluginResourceLimits;
  readonly allowedCapabilities: ReadonlyArray<string>;
  readonly deniedCapabilities: ReadonlyArray<string>;
}

export interface PluginSandboxSnapshot {
  readonly sandboxId: string;
  readonly pluginId: string;
  readonly state: 'CREATED' | 'ACTIVE' | 'SUSPENDED' | 'TERMINATED' | 'VIOLATION';
  readonly securityProfileId?: string;
  readonly createdAt: number;
  readonly resourceLimits: PluginResourceLimits;
  readonly allowedCapabilities: ReadonlyArray<string>;
  readonly deniedCapabilities: ReadonlyArray<string>;
}

export function createSecurityDecision(input: Omit<PluginSecurityDecision, typeof Symbol.toStringTag>): PluginSecurityDecision {
  return freezeDeepSafe(input);
}

export function createSecurityViolation(input: Omit<PluginSecurityViolation, typeof Symbol.toStringTag>): PluginSecurityViolation {
  return freezeDeepSafe(input);
}

export function createAuditRecord(input: Omit<PluginAuditRecord, typeof Symbol.toStringTag>): PluginAuditRecord {
  return freezeDeepSafe(input);
}

export function createSandboxSnapshot(input: Omit<PluginSandboxSnapshot, typeof Symbol.toStringTag>): PluginSandboxSnapshot {
  return freezeDeepSafe(input);
}
