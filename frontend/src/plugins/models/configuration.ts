import { freezeDeepSafe } from './dependency';

export const PluginConfigurationValueType = {
  STRING: 'string',
  NUMBER: 'number',
  BOOLEAN: 'boolean',
  OBJECT: 'object',
  ARRAY: 'array',
  NULL: 'null'
} as const;
export type PluginConfigurationValueTypeValue = typeof PluginConfigurationValueType[keyof typeof PluginConfigurationValueType];

export interface PluginConfigurationField {
  readonly key: string;
  readonly type: PluginConfigurationValueTypeValue;
  readonly description?: string;
  readonly required: boolean;
  readonly defaultValue?: any;
  readonly sensitive: boolean;
  readonly readOnly: boolean;
  readonly nullable: boolean;
  readonly minimum?: number;
  readonly maximum?: number;
  readonly minLength?: number;
  readonly maxLength?: number;
  readonly allowedValues?: ReadonlyArray<any>;
  readonly pattern?: string;
}

export interface PluginConfigurationSchema {
  readonly schemaId: string;
  readonly pluginId: string;
  readonly version: string;
  readonly fields: ReadonlyArray<PluginConfigurationField>;
  readonly strict: boolean;
  readonly createdAt: number;
  readonly updatedAt: number;
}

export interface PluginConfiguration {
  readonly pluginId: string;
  readonly schemaId: string;
  readonly schemaVersion: string;
  readonly values: Record<string, any>;
  readonly version: number;
  readonly createdAt: number;
  readonly updatedAt: number;
}

export interface PluginConfigurationProfile {
  readonly profileId: string;
  readonly pluginId: string;
  readonly name: string;
  readonly description?: string;
  readonly values: Record<string, any>;
  readonly active: boolean;
  readonly createdAt: number;
  readonly updatedAt: number;
}

export interface PluginConfigurationOverride {
  readonly overrideId: string;
  readonly pluginId: string;
  readonly profileId?: string;
  readonly key: string;
  readonly value: any;
  readonly source: 'DEFAULT' | 'PROFILE' | 'USER' | 'SESSION' | 'WORKSPACE' | 'SYSTEM';
  readonly priority: number;
  readonly enabled: boolean;
  readonly createdAt: number;
  readonly expiresAt?: number;
}

export interface PluginConfigurationChange {
  readonly changeId: string;
  readonly pluginId: string;
  readonly key: string;
  readonly previousValueChanged: boolean;
  readonly newValueChanged: boolean;
  readonly source: string;
  readonly timestamp: number;
  readonly version: number;
}

export interface PluginConfigurationValidationIssue {
  readonly key: string;
  readonly code: string;
  readonly message: string;
  readonly severity: 'WARNING' | 'ERROR';
  readonly expected?: string;
  readonly actual?: string;
}

export interface PluginConfigurationValidationResult {
  readonly valid: boolean;
  readonly issues: ReadonlyArray<PluginConfigurationValidationIssue>;
  readonly validatedAt: number;
}

export interface PluginConfigurationStatistics {
  readonly schemasRegistered: number;
  readonly configurationsCreated: number;
  readonly configurationsUpdated: number;
  readonly configurationsReset: number;
  readonly validationRequests: number;
  readonly validationFailures: number;
  readonly overridesRegistered: number;
  readonly overridesApplied: number;
  readonly profilesCreated: number;
  readonly profilesDeleted: number;
  readonly changesRecorded: number;
  readonly persistenceReads: number;
  readonly persistenceWrites: number;
  readonly importOperations: number;
  readonly exportOperations: number;
}

export interface PluginConfigurationHealth {
  readonly healthy: boolean;
  readonly schemaCount: number;
  readonly configurationCount: number;
  readonly profileCount: number;
  readonly overrideCount: number;
  readonly validationFailureRate: number;
  readonly activeProfiles: number;
  readonly message: string;
}

export interface PluginConfigurationDiagnostics {
  readonly statistics: PluginConfigurationStatistics;
  readonly health: PluginConfigurationHealth;
  readonly registeredSchemaCount: number;
  readonly configurationCount: number;
  readonly profileCount: number;
  readonly overrideCount: number;
  readonly activeProfileCount: number;
  readonly configurationHistoryDepth: number;
  readonly validationFailureCount: number;
  readonly persistenceOperationCounts: {
    readonly reads: number;
    readonly writes: number;
  };
  readonly importExportCounts: {
    readonly imports: number;
    readonly exports: number;
  };
  readonly averageValidationTime: number;
  readonly averageUpdateTime: number;
  readonly maximumUpdateTime: number;
  readonly minimumUpdateTime: number;
}

// Factory Methods returning Deeply Frozen Snapshots
export function createPluginConfigurationField(input: PluginConfigurationField): PluginConfigurationField {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationSchema(input: PluginConfigurationSchema): PluginConfigurationSchema {
  return freezeDeepSafe(input);
}

export function createPluginConfiguration(input: PluginConfiguration): PluginConfiguration {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationProfile(input: PluginConfigurationProfile): PluginConfigurationProfile {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationOverride(input: PluginConfigurationOverride): PluginConfigurationOverride {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationChange(input: PluginConfigurationChange): PluginConfigurationChange {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationValidationResult(input: PluginConfigurationValidationResult): PluginConfigurationValidationResult {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationStatistics(input: PluginConfigurationStatistics): PluginConfigurationStatistics {
  return freezeDeepSafe(input);
}

export function createPluginConfigurationHealth(input: PluginConfigurationHealth): PluginConfigurationHealth {
  return freezeDeepSafe(input);
}
