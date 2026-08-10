import type { IPluginLifecycleManager } from '../interfaces/plugin-lifecycle';
import type { IPluginSecurityManager } from '../interfaces/plugin-security';
import type {
  IPluginConfigurationManager,
  IPluginConfigurationStore
} from '../interfaces/plugin-configuration';
import {
  type PluginConfigurationSchema,
  type PluginConfiguration,
  type PluginConfigurationProfile,
  type PluginConfigurationOverride,
  type PluginConfigurationChange,
  type PluginConfigurationValidationResult,
  type PluginConfigurationStatistics,
  type PluginConfigurationHealth,
  type PluginConfigurationDiagnostics,
  createPluginConfiguration,
  createPluginConfigurationProfile,
  createPluginConfigurationOverride,
  createPluginConfigurationChange,
  createPluginConfigurationStatistics,
  createPluginConfigurationHealth
} from '../models/configuration';
import { InMemoryPluginConfigurationStore } from './InMemoryPluginConfigurationStore';
import { PluginConfigurationValidator } from './PluginConfigurationValidator';
import {
  PluginConfigurationSchemaError,
  PluginConfigurationValidationError,
  PluginConfigurationNotFoundError,
  PluginConfigurationConflictError,
  PluginConfigurationPermissionError,
  PluginConfigurationProfileError,
  PluginConfigurationOverrideError
} from '../errors/PluginErrors';
import { freezeDeepSafe } from '../models/dependency';

const SourcePriorityMap: Record<string, number> = {
  DEFAULT: 0,
  PROFILE: 1,
  USER: 2,
  SESSION: 3,
  WORKSPACE: 4,
  SYSTEM: 5
};

export class PluginConfigurationManager implements IPluginConfigurationManager {
  private readonly schemas = new Map<string, PluginConfigurationSchema>();
  private readonly configurations = new Map<string, PluginConfiguration>();
  private readonly userValues = new Map<string, Record<string, any>>();
  private readonly profiles = new Map<string, PluginConfigurationProfile[]>();
  private readonly overrides = new Map<string, PluginConfigurationOverride[]>();
  private readonly overrideRegTimes = new Map<string, number>();
  private readonly auditHistoryLog: PluginConfigurationChange[] = [];

  private schemasRegisteredCount = 0;
  private configurationsCreatedCount = 0;
  private configurationsUpdatedCount = 0;
  private configurationsResetCount = 0;
  private validationRequestsCount = 0;
  private validationFailuresCount = 0;
  private overridesRegisteredCount = 0;
  private overridesAppliedCount = 0;
  private profilesCreatedCount = 0;
  private profilesDeletedCount = 0;
  private importOperationsCount = 0;
  private exportOperationsCount = 0;

  private maxHistorySize = 100;
  private updateTimes: number[] = [];
  private validationTimes: number[] = [];

  constructor(
    private readonly lifecycleManager: IPluginLifecycleManager,
    private readonly securityManager: IPluginSecurityManager,
    private readonly store: IPluginConfigurationStore = new InMemoryPluginConfigurationStore(),
    options?: { maxHistorySize?: number }
  ) {
    if (options?.maxHistorySize !== undefined) {
      this.maxHistorySize = options.maxHistorySize;
    }

    this.lifecycleManager.addDisposeListener((pluginId) => {
      this.schemas.delete(pluginId);
      this.configurations.delete(pluginId);
      this.profiles.delete(pluginId);
      this.overrides.delete(pluginId);
      this.store.remove(pluginId).catch(() => {});
    });

    // Lifecycle activation validation
    this.lifecycleManager.addActivateListener((pluginId) => {
      const schema = this.schemas.get(pluginId);
      if (schema) {
        // Enforce secure read check on activation
        this.checkSecurity(pluginId, 'CONFIG_READ');
        const resolved = this.resolveConfiguration(pluginId);
        const validation = PluginConfigurationValidator.validate(schema, resolved);
        if (!validation.valid) {
          throw new PluginConfigurationValidationError(`Mandatory configuration validation failed on activation.`, pluginId);
        }
      }
    });
  }

  private checkSecurity(pluginId: string, action: 'CONFIG_READ' | 'CONFIG_WRITE'): void {
    const authorized = this.securityManager.checkPermission(pluginId, action, 'PLUGIN');
    if (!authorized) {
      throw new PluginConfigurationPermissionError(`Unauthorized configuration operation '${action}' for plugin '${pluginId}'.`, pluginId);
    }
  }

  public registerSchema(
    pluginId: string,
    schema: Omit<PluginConfigurationSchema, 'pluginId' | 'createdAt' | 'updatedAt'>
  ): PluginConfigurationSchema {
    if (this.schemas.has(pluginId)) {
      throw new PluginConfigurationConflictError(`Schema for plugin '${pluginId}' already registered.`, pluginId);
    }

    const regSchema: PluginConfigurationSchema = {
      ...schema,
      pluginId,
      createdAt: Date.now(),
      updatedAt: Date.now()
    };

    // Validate defaults immediately
    const defaults: Record<string, any> = {};
    for (const f of schema.fields) {
      if (f.defaultValue !== undefined) {
        defaults[f.key] = f.defaultValue;
      }
    }
    const val = PluginConfigurationValidator.validate(regSchema, defaults, undefined, { skipRequired: true });
    if (!val.valid) {
      throw new PluginConfigurationSchemaError(`Default values in schema violate validation constraints.`, pluginId);
    }

    this.schemas.set(pluginId, regSchema);
    this.schemasRegisteredCount += 1;
    return freezeDeepSafe(regSchema);
  }

  public removeSchema(pluginId: string): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');
    this.schemas.delete(pluginId);
  }

  public getSchema(pluginId: string): PluginConfigurationSchema | null {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const schema = this.schemas.get(pluginId);
    return schema ? freezeDeepSafe(schema) : null;
  }

  public listSchemas(): ReadonlyArray<PluginConfigurationSchema> {
    const list = Array.from(this.schemas.values());
    return Object.freeze(list.map(s => freezeDeepSafe(s)));
  }

  public createConfiguration(pluginId: string, values: Record<string, any>): PluginConfiguration {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    // Store the raw user-provided values
    this.userValues.set(pluginId, { ...values });

    // Validate the full resolved result (defaults + profile + user values + overrides)
    const resolved = this.resolveMergedValues(pluginId, values);
    const valResult = PluginConfigurationValidator.validate(schema, resolved);
    if (!valResult.valid) {
      this.validationFailuresCount += 1;
      this.userValues.delete(pluginId);
      throw new PluginConfigurationValidationError(`Initial configuration validation failed.`, pluginId);
    }

    // Store the resolved values as the configuration snapshot
    const config = createPluginConfiguration({
      pluginId,
      schemaId: schema.schemaId,
      schemaVersion: schema.version,
      values: resolved,
      version: 1,
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    this.configurations.set(pluginId, config);
    this.store.write(pluginId, config).catch(() => {});
    this.configurationsCreatedCount += 1;

    return config;
  }

  public getConfiguration(pluginId: string): PluginConfiguration | null {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const config = this.configurations.get(pluginId);
    return config ? freezeDeepSafe(config) : null;
  }

  public updateConfiguration(pluginId: string, values: Record<string, any>): PluginConfiguration {
    const startTime = Date.now();
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    const existing = this.configurations.get(pluginId);
    if (!existing) {
      throw new PluginConfigurationNotFoundError(`Configuration for plugin '${pluginId}' not found.`, pluginId);
    }

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    // Merge new values into the raw user values
    const rawPrev = this.userValues.get(pluginId) || {};
    const updatedUserValues = { ...rawPrev, ...values };

    // Re-resolve the full configuration (defaults + profile + user values + overrides)
    const resolved = this.resolveMergedValues(pluginId, updatedUserValues);

    const valResult = PluginConfigurationValidator.validate(schema, resolved, existing.values);
    if (!valResult.valid) {
      this.validationFailuresCount += 1;
      throw new PluginConfigurationValidationError(`Configuration update validation failed.`, pluginId);
    }

    this.userValues.set(pluginId, updatedUserValues);

    const updated = createPluginConfiguration({
      ...existing,
      values: resolved,
      version: existing.version + 1,
      updatedAt: Date.now()
    });

    this.configurations.set(pluginId, updated);
    this.store.write(pluginId, updated).catch(() => {});
    this.configurationsUpdatedCount += 1;

    // Log changes to audit history (redacting sensitive fields)
    for (const key of Object.keys(values)) {
      const field = schema.fields.find(f => f.key === key);
      const isSensitive = field?.sensitive || false;

      this.logChange(
        pluginId,
        key,
        isSensitive,
        existing.version + 1
      );
    }

    this.updateTimes.push(Date.now() - startTime);
    return updated;
  }

  public resetConfiguration(pluginId: string): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const defaults: Record<string, any> = {};
    for (const f of schema.fields) {
      if (f.defaultValue !== undefined) {
        defaults[f.key] = f.defaultValue;
      }
    }

    this.createConfiguration(pluginId, defaults);
    this.configurationsResetCount += 1;
  }

  public validateConfiguration(pluginId: string, values: Record<string, any>): PluginConfigurationValidationResult {
    const startTime = Date.now();
    this.validationRequestsCount += 1;

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const existing = this.configurations.get(pluginId);
    const result = PluginConfigurationValidator.validate(schema, values, existing?.values);

    if (!result.valid) {
      this.validationFailuresCount += 1;
    }

    this.validationTimes.push(Date.now() - startTime);
    return result;
  }

  public getConfigurationValue(pluginId: string, key: string): any {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const resolved = this.resolveConfiguration(pluginId);
    return resolved[key];
  }

  public setConfigurationValue(pluginId: string, key: string, value: any): void {
    this.updateConfiguration(pluginId, { [key]: value });
  }

  public removeConfigurationValue(pluginId: string, key: string): void {
    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const field = schema.fields.find(f => f.key === key);
    if (field?.required) {
      throw new PluginConfigurationValidationError(`Cannot remove required field '${key}'.`, pluginId);
    }

    const values = { ...this.resolveConfiguration(pluginId) };
    delete values[key];

    this.updateConfiguration(pluginId, values);
  }

  public createProfile(
    pluginId: string,
    profile: Omit<PluginConfigurationProfile, 'pluginId' | 'createdAt' | 'updatedAt'>
  ): PluginConfigurationProfile {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    let list = this.profiles.get(pluginId) || [];
    if (list.some(p => p.profileId === profile.profileId)) {
      throw new PluginConfigurationProfileError(`Profile '${profile.profileId}' already exists.`, pluginId);
    }

    const regProfile = createPluginConfigurationProfile({
      ...profile,
      pluginId,
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    list.push(regProfile);
    this.profiles.set(pluginId, list);
    this.profilesCreatedCount += 1;

    return regProfile;
  }

  public removeProfile(pluginId: string, profileId: string): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    let list = this.profiles.get(pluginId) || [];
    const index = list.findIndex(p => p.profileId === profileId);
    if (index === -1) {
      throw new PluginConfigurationProfileError(`Profile '${profileId}' not found.`, pluginId);
    }

    const profile = list[index];
    if (profile.active) {
      throw new PluginConfigurationProfileError(`Cannot delete active configuration profile '${profileId}'.`, pluginId);
    }

    list.splice(index, 1);
    this.profiles.set(pluginId, list);
    this.profilesDeletedCount += 1;
  }

  public activateProfile(pluginId: string, profileId: string): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    let list = this.profiles.get(pluginId) || [];
    if (!list.some(p => p.profileId === profileId)) {
      throw new PluginConfigurationProfileError(`Profile '${profileId}' not found.`, pluginId);
    }

    const updated = list.map(p => createPluginConfigurationProfile({
      ...p,
      active: p.profileId === profileId,
      updatedAt: Date.now()
    }));

    this.profiles.set(pluginId, updated);

    // Re-resolve active config using raw user values
    const rawValues = this.userValues.get(pluginId);
    if (rawValues) {
      this.createConfiguration(pluginId, rawValues);
    }
  }

  public getProfile(pluginId: string, profileId: string): PluginConfigurationProfile | null {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const list = this.profiles.get(pluginId) || [];
    const prof = list.find(p => p.profileId === profileId);
    return prof ? freezeDeepSafe(prof) : null;
  }

  public listProfiles(pluginId: string): ReadonlyArray<PluginConfigurationProfile> {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const list = this.profiles.get(pluginId) || [];
    return Object.freeze(list.map(p => freezeDeepSafe(p)));
  }

  public registerOverride(
    pluginId: string,
    override: Omit<PluginConfigurationOverride, 'overrideId' | 'pluginId' | 'createdAt'>
  ): PluginConfigurationOverride {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const overrideId = Math.random().toString(36).substring(2, 11);
    const regOverride = createPluginConfigurationOverride({
      ...override,
      overrideId,
      pluginId,
      createdAt: Date.now()
    });

    const list = this.overrides.get(pluginId) || [];
    list.push(regOverride);
    this.overrides.set(pluginId, list);
    this.overrideRegTimes.set(overrideId, Date.now());
    this.overridesRegisteredCount += 1;

    return regOverride;
  }

  public removeOverride(pluginId: string, overrideId: string): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    let list = this.overrides.get(pluginId) || [];
    const index = list.findIndex(o => o.overrideId === overrideId);
    if (index === -1) {
      throw new PluginConfigurationOverrideError(`Override '${overrideId}' not found.`, pluginId);
    }

    list.splice(index, 1);
    this.overrides.set(pluginId, list);
    this.overrideRegTimes.delete(overrideId);
  }

  public listOverrides(pluginId: string): ReadonlyArray<PluginConfigurationOverride> {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const list = this.overrides.get(pluginId) || [];
    return Object.freeze(list.map(o => freezeDeepSafe(o)));
  }

  public resolveConfiguration(pluginId: string): Record<string, any> {
    this.checkSecurity(pluginId, 'CONFIG_READ');
    const rawValues = this.userValues.get(pluginId);
    if (!rawValues) {
      return {};
    }
    return this.resolveMergedValues(pluginId, rawValues);
  }

  private resolveMergedValues(pluginId: string, values: Record<string, any>): Record<string, any> {
    const schema = this.schemas.get(pluginId);
    if (!schema) {
      return { ...values };
    }

    // 1. Schema default values
    const result: Record<string, any> = {};
    for (const f of schema.fields) {
      if (f.defaultValue !== undefined) {
        result[f.key] = f.defaultValue;
      }
    }

    // 2. Active profile values
    const list = this.profiles.get(pluginId) || [];
    const activeProf = list.find(p => p.active);
    if (activeProf) {
      Object.assign(result, activeProf.values);
    }

    // 3. User configuration values
    Object.assign(result, values);

    // 4. Overrides matching priorities (FIFO fallback)
    const overrideList = this.overrides.get(pluginId) || [];
    const activeOverrides = overrideList.filter(o => o.enabled && (!o.expiresAt || o.expiresAt > Date.now()));

    // Sort: priority asc, source priority asc, registration order asc (FIFO)
    activeOverrides.sort((a, b) => {
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }
      const sa = SourcePriorityMap[a.source] || 0;
      const sb = SourcePriorityMap[b.source] || 0;
      if (sa !== sb) {
        return sa - sb;
      }
      const ta = this.overrideRegTimes.get(a.overrideId) || 0;
      const tb = this.overrideRegTimes.get(b.overrideId) || 0;
      return ta - tb;
    });

    for (const o of activeOverrides) {
      result[o.key] = o.value;
      this.overridesAppliedCount += 1;
    }

    return result;
  }

  public configurationHistory(pluginId?: string): ReadonlyArray<PluginConfigurationChange> {
    if (pluginId) {
      this.checkSecurity(pluginId, 'CONFIG_READ');
      return Object.freeze(this.auditHistoryLog.filter(c => c.pluginId === pluginId));
    }
    return Object.freeze([...this.auditHistoryLog]);
  }

  public importConfiguration(
    pluginId: string,
    payload: Record<string, any>,
    options?: { allowSensitive?: boolean }
  ): void {
    this.checkSecurity(pluginId, 'CONFIG_WRITE');

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const incoming = { ...payload };

    // Redact sensitive inputs unless allowSensitive option set
    if (!options?.allowSensitive) {
      for (const field of schema.fields) {
        if (field.sensitive && keyIn(incoming, field.key)) {
          delete incoming[field.key];
        }
      }
    }

    this.createConfiguration(pluginId, incoming);
    this.importOperationsCount += 1;
  }

  public exportConfiguration(pluginId: string, options?: { allowSensitive?: boolean }): Record<string, any> {
    this.checkSecurity(pluginId, 'CONFIG_READ');

    const schema = this.schemas.get(pluginId);
    if (!schema) {
      throw new PluginConfigurationSchemaError(`No schema registered for plugin '${pluginId}'.`, pluginId);
    }

    const resolved = this.resolveConfiguration(pluginId);
    const exported: Record<string, any> = {};

    for (const key of Object.keys(resolved)) {
      const field = schema.fields.find(f => f.key === key);
      if (field?.sensitive && !options?.allowSensitive) {
        exported[key] = '[REDACTED]';
      } else {
        exported[key] = resolved[key];
      }
    }

    this.exportOperationsCount += 1;
    return freezeDeepSafe(exported);
  }

  public statistics(): PluginConfigurationStatistics {
    return createPluginConfigurationStatistics({
      schemasRegistered: this.schemasRegisteredCount,
      configurationsCreated: this.configurationsCreatedCount,
      configurationsUpdated: this.configurationsUpdatedCount,
      configurationsReset: this.configurationsResetCount,
      validationRequests: this.validationRequestsCount,
      validationFailures: this.validationFailuresCount,
      overridesRegistered: this.overridesRegisteredCount,
      overridesApplied: this.overridesAppliedCount,
      profilesCreated: this.profilesCreatedCount,
      profilesDeleted: this.profilesDeletedCount,
      changesRecorded: this.auditHistoryLog.length,
      persistenceReads: (this.store as any).readOperations || 0,
      persistenceWrites: (this.store as any).writeOperations || 0,
      importOperations: this.importOperationsCount,
      exportOperations: this.exportOperationsCount
    });
  }

  public health(): PluginConfigurationHealth {
    const list = Array.from(this.configurations.values());
    const invalidCount = list.filter(c => {
      const schema = this.schemas.get(c.pluginId);
      if (!schema) return true;
      return !PluginConfigurationValidator.validate(schema, c.values).valid;
    }).length;

    const healthy = invalidCount === 0;

    return createPluginConfigurationHealth({
      healthy,
      schemaCount: this.schemas.size,
      configurationCount: this.configurations.size,
      profileCount: Array.from(this.profiles.values()).reduce((a, b) => a + b.length, 0),
      overrideCount: Array.from(this.overrides.values()).reduce((a, b) => a + b.length, 0),
      validationFailureRate: this.validationRequestsCount > 0 ? this.validationFailuresCount / this.validationRequestsCount : 0,
      activeProfiles: Array.from(this.profiles.values()).reduce((a, b) => a + b.filter(p => p.active).length, 0),
      message: healthy ? 'Configuration system healthy' : `${invalidCount} invalid configurations detected.`
    });
  }

  public diagnostics(): PluginConfigurationDiagnostics {
    const avgVal = this.validationTimes.length > 0 ? this.validationTimes.reduce((a, b) => a + b, 0) / this.validationTimes.length : 0;
    const avgUp = this.updateTimes.length > 0 ? this.updateTimes.reduce((a, b) => a + b, 0) / this.updateTimes.length : 0;
    const maxUp = this.updateTimes.length > 0 ? Math.max(...this.updateTimes) : 0;
    const minUp = this.updateTimes.length > 0 ? Math.min(...this.updateTimes) : 0;

    return freezeDeepSafe({
      statistics: this.statistics(),
      health: this.health(),
      registeredSchemaCount: this.schemas.size,
      configurationCount: this.configurations.size,
      profileCount: Array.from(this.profiles.values()).reduce((a, b) => a + b.length, 0),
      overrideCount: Array.from(this.overrides.values()).reduce((a, b) => a + b.length, 0),
      activeProfileCount: Array.from(this.profiles.values()).reduce((a, b) => a + b.filter(p => p.active).length, 0),
      configurationHistoryDepth: this.auditHistoryLog.length,
      validationFailureCount: this.validationFailuresCount,
      persistenceOperationCounts: {
        reads: (this.store as any).readOperations || 0,
        writes: (this.store as any).writeOperations || 0
      },
      importExportCounts: {
        imports: this.importOperationsCount,
        exports: this.exportOperationsCount
      },
      averageValidationTime: avgVal,
      averageUpdateTime: avgUp,
      maximumUpdateTime: maxUp,
      minimumUpdateTime: minUp
    });
  }

  public reset(): void {
    this.schemas.clear();
    this.configurations.clear();
    this.userValues.clear();
    this.profiles.clear();
    this.overrides.clear();
    this.overrideRegTimes.clear();
    this.auditHistoryLog.length = 0;
    this.updateTimes.length = 0;
    this.validationTimes.length = 0;

    this.schemasRegisteredCount = 0;
    this.configurationsCreatedCount = 0;
    this.configurationsUpdatedCount = 0;
    this.configurationsResetCount = 0;
    this.validationRequestsCount = 0;
    this.validationFailuresCount = 0;
    this.overridesRegisteredCount = 0;
    this.overridesAppliedCount = 0;
    this.profilesCreatedCount = 0;
    this.profilesDeletedCount = 0;
    this.importOperationsCount = 0;
    this.exportOperationsCount = 0;

    this.store.remove('*').catch(() => {});
  }

  private logChange(
    pluginId: string,
    key: string,
    _sensitive: boolean,
    version: number
  ): void {
    const changeId = Math.random().toString(36).substring(2, 11);
    const change = createPluginConfigurationChange({
      changeId,
      pluginId,
      key,
      previousValueChanged: true,
      newValueChanged: true,
      source: 'USER_UPDATE',
      timestamp: Date.now(),
      version
    });

    this.auditHistoryLog.push(change);
    if (this.auditHistoryLog.length > this.maxHistorySize) {
      this.auditHistoryLog.shift();
    }
  }
}

function keyIn(obj: Record<string, any>, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(obj, key);
}
