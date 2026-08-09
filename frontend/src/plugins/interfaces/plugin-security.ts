import type {
  PluginPermission,
  PluginPermissionActionValue,
  PluginPermissionScopeValue,
  PluginSecurityProfile,
  PluginSecurityDecision,
  PluginSecurityViolation,
  PluginAuditRecord,
  PluginSecurityStatistics,
  PluginSecurityHealth,
  PluginSecurityDiagnostics,
  PluginSandboxSnapshot,
  PluginResourceLimits
} from '../models/security';

export interface IPluginSecurityManager {
  registerPermission(pluginId: string, action: PluginPermissionActionValue, scope: PluginPermissionScopeValue, description?: string): PluginPermission;
  revokePermission(pluginId: string, permissionId: string): void;
  getPermission(pluginId: string, permissionId: string): PluginPermission | null;
  listPermissions(pluginId?: string): ReadonlyArray<PluginPermission>;
  checkPermission(pluginId: string, action: PluginPermissionActionValue, scope: PluginPermissionScopeValue): boolean;
  evaluate(pluginId: string, action: PluginPermissionActionValue, scope: PluginPermissionScopeValue): PluginSecurityDecision;
  
  createSecurityProfile(pluginId: string, profile: Omit<PluginSecurityProfile, 'pluginId' | 'createdAt' | 'updatedAt'>): PluginSecurityProfile;
  getSecurityProfile(pluginId: string): PluginSecurityProfile | null;
  updateSecurityProfile(pluginId: string, profile: Partial<Omit<PluginSecurityProfile, 'pluginId' | 'createdAt' | 'updatedAt'>>): PluginSecurityProfile;
  removeSecurityProfile(pluginId: string): void;
  
  recordViolation(
    pluginId: string,
    action: PluginPermissionActionValue,
    reason: string,
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    metadata?: Record<string, unknown>
  ): PluginSecurityViolation;
  
  auditHistory(): ReadonlyArray<PluginAuditRecord>;
  statistics(): PluginSecurityStatistics;
  health(): PluginSecurityHealth;
  diagnostics(): PluginSecurityDiagnostics;
  reset(): void;
}

export interface IPluginSandboxManager {
  createSandbox(pluginId: string, securityProfileId?: string): PluginSandboxSnapshot;
  destroySandbox(pluginId: string): void;
  getSandbox(pluginId: string): PluginSandboxSnapshot | null;
  listSandboxes(): ReadonlyArray<PluginSandboxSnapshot>;
  validateOperation(pluginId: string, capabilityId: string, metadata?: Record<string, unknown>): boolean;
  
  incrementUsage(pluginId: string, limitType: keyof PluginResourceLimits): void;
  decrementUsage(pluginId: string, limitType: keyof PluginResourceLimits): void;
  resourceUsage(pluginId: string): PluginResourceLimits;
  
  statistics(): Record<string, any>;
  health(): Record<string, any>;
  diagnostics(): Record<string, any>;
  reset(): void;
}
