/**
 * Secure Configuration Manager & Sensitive Data Engine (Phase 16.3.5).
 *
 * Implements sensitive value registration, redaction per SensitiveValueType (PASSWORD, TOKEN, API_KEY,
 * CERTIFICATE, PRIVATE_KEY, CONNECTION_STRING, CUSTOM), policy enforcement, audit logging, and diagnostics protection.
 *
 * Note: This component is intended for runtime sensitive-data management (masking/redaction in logs/diagnostics).
 * It is NOT a secret storage vault.
 */

import {
  createSensitiveAccessRecord,
  createSensitiveConfiguration,
  createSensitiveConfigurationReference,
  createSensitiveConfigurationSnapshot,
  createSensitiveHealth,
  createSensitiveStatistics,
  createSensitiveValuePolicy,
  SensitiveAccessRecord,
  SensitiveConfiguration,
  SensitiveConfigurationSnapshot,
  SensitiveHealth,
  SensitiveStatistics,
  SensitiveValuePolicy,
  SensitiveValueType,
} from './models';
import { ConfigurationProviderException, ConfigurationValidationException } from './exceptions';

export class SecureConfigurationManager {
  private readonly _sensitiveStore = new Map<string, SensitiveConfiguration>();
  private readonly _auditLog: SensitiveAccessRecord[] = [];

  private _reads = 0;
  private _redactions = 0;
  private _blockedAccesses = 0;

  public register(
    key: string,
    rawValue: unknown,
    sensitiveType: SensitiveValueType = SensitiveValueType.CUSTOM,
    policy?: SensitiveValuePolicy,
  ): void {
    const k = key ? key.trim() : '';
    if (!k) {
      this.recordAudit(k, 'REGISTER', false, 'Key cannot be empty.');
      throw new ConfigurationProviderException('Sensitive configuration key cannot be empty.');
    }
    if (rawValue === undefined || rawValue === null) {
      this.recordAudit(k, 'REGISTER', false, 'Value cannot be null or undefined.');
      throw new ConfigurationProviderException('Sensitive value cannot be null or undefined.');
    }
    if (this._sensitiveStore.has(k)) {
      this.recordAudit(k, 'REGISTER', false, `Key '${k}' is already registered.`);
      throw new ConfigurationProviderException(`Sensitive configuration key '${k}' is already registered.`);
    }

    const config = createSensitiveConfiguration({
      key: k,
      rawValue,
      sensitiveType,
      policy: policy ?? createSensitiveValuePolicy(),
    });

    this._sensitiveStore.set(k, config);
    this.recordAudit(k, 'REGISTER', true);
  }

  public update(key: string, rawValue: unknown): void {
    const k = key ? key.trim() : '';
    const existing = this._sensitiveStore.get(k);
    if (!existing) {
      this.recordAudit(k, 'UPDATE', false, `Key '${k}' is not registered.`);
      throw new ConfigurationProviderException(`Sensitive configuration key '${k}' is not registered.`);
    }

    const updated = createSensitiveConfiguration({
      ...existing,
      rawValue,
    });

    this._sensitiveStore.set(k, updated);
    this.recordAudit(k, 'UPDATE', true);
  }

  public remove(key: string): boolean {
    const k = key ? key.trim() : '';
    const existed = this._sensitiveStore.delete(k);
    this.recordAudit(k, 'REMOVE', existed, existed ? undefined : `Key '${k}' not found.`);
    return existed;
  }

  public contains(key: string): boolean {
    return this._sensitiveStore.has(key.trim());
  }

  public getSensitiveValue(key: string): unknown | undefined {
    const k = key ? key.trim() : '';
    const config = this._sensitiveStore.get(k);

    if (!config) {
      this.recordAudit(k, 'READ', false, `Key '${k}' not found.`);
      return undefined;
    }

    if (!config.policy.allowRead) {
      this._blockedAccesses++;
      this.recordAudit(k, 'READ', false, `Reading key '${k}' blocked by policy.`);
      throw new ConfigurationValidationException(`Access to sensitive key '${k}' is restricted by policy.`);
    }

    this._reads++;
    this.recordAudit(k, 'READ', true);
    return config.rawValue;
  }

  public getRedactedValue(key: string): string | undefined {
    const k = key ? key.trim() : '';
    const config = this._sensitiveStore.get(k);

    if (!config) {
      return undefined;
    }

    this._redactions++;
    this.recordAudit(k, 'REDACT', true);
    return this.computeRedactedString(config.rawValue, config.sensitiveType);
  }

  public createSnapshot(): SensitiveConfigurationSnapshot {
    const refs = Array.from(this._sensitiveStore.values()).map((config) =>
      createSensitiveConfigurationReference({
        key: config.key,
        sensitiveType: config.sensitiveType,
        redactedValue: this.computeRedactedString(config.rawValue, config.sensitiveType),
        registeredAt: config.registeredAt,
      }),
    );

    return createSensitiveConfigurationSnapshot({
      references: refs,
      sensitiveCount: refs.length,
      timestamp: new Date().toISOString(),
    });
  }

  public statistics(): SensitiveStatistics {
    return createSensitiveStatistics({
      totalValues: this._sensitiveStore.size,
      reads: this._reads,
      redactions: this._redactions,
      blockedAccesses: this._blockedAccesses,
      auditRecordsCount: this._auditLog.length,
    });
  }

  public health(): SensitiveHealth {
    return createSensitiveHealth({
      healthy: true,
      totalValues: this._sensitiveStore.size,
    });
  }

  public auditHistory(): ReadonlyArray<SensitiveAccessRecord> {
    return Object.freeze([...this._auditLog]);
  }

  public clear(): void {
    this._sensitiveStore.clear();
    this._auditLog.length = 0;
  }

  private computeRedactedString(value: unknown, sensitiveType: SensitiveValueType): string {
    const str = String(value);

    switch (sensitiveType) {
      case SensitiveValueType.PASSWORD:
        return '********';
      case SensitiveValueType.TOKEN:
        return str.length > 4 ? `${str.slice(0, 4)}****` : '****';
      case SensitiveValueType.API_KEY:
        return str.length > 8 ? `${str.slice(0, 4)}...${str.slice(-4)}` : '****';
      case SensitiveValueType.CERTIFICATE:
        return '<CERTIFICATE>';
      case SensitiveValueType.PRIVATE_KEY:
        return '<PRIVATE_KEY>';
      case SensitiveValueType.CONNECTION_STRING:
        return '<CONNECTION_STRING>';
      case SensitiveValueType.CUSTOM:
      default:
        return '[REDACTED]';
    }
  }

  private recordAudit(
    key: string,
    action: 'REGISTER' | 'READ' | 'REDACT' | 'UPDATE' | 'REMOVE',
    success: boolean,
    reason?: string,
  ): void {
    this._auditLog.push(
      createSensitiveAccessRecord({
        key,
        action,
        success,
        reason,
      }),
    );
  }
}
