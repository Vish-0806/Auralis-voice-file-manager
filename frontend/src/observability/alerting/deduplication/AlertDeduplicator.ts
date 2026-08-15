import { AlertRecord } from '../models/alert';
import {
  DeduplicationPolicy,
  DeduplicationDecision,
  DeduplicationRecord
} from '../models/deduplication';
import { AlertDeduplicationError } from '../errors/AlertingErrors';
import {
  createDeduplicationDecision,
  createDeduplicationRecord
} from '../factories/alertingFactories';

export class AlertDeduplicator {
  private readonly _records = new Map<string, DeduplicationRecord>();
  private readonly _insertionOrder: string[] = [];

  public check(alert: AlertRecord, policy: DeduplicationPolicy, now: number): DeduplicationDecision {
    if (!alert) {
      throw new AlertDeduplicationError('alert is required');
    }
    if (!alert.fingerprint) {
      throw new AlertDeduplicationError('alert fingerprint is required for deduplication');
    }
    if (!policy) {
      throw new AlertDeduplicationError('deduplication policy is required');
    }
    if (typeof policy.cooldownMs !== 'number' || isNaN(policy.cooldownMs) || !isFinite(policy.cooldownMs) || policy.cooldownMs < 0) {
      throw new AlertDeduplicationError(`Invalid policy cooldownMs: ${policy.cooldownMs}. Must be a finite non-negative number.`);
    }
    if (typeof now !== 'number' || isNaN(now) || !isFinite(now) || now < 0) {
      throw new AlertDeduplicationError(`Invalid evaluation timestamp: ${now}. Must be a finite non-negative number.`);
    }

    if (!policy.enabled) {
      return createDeduplicationDecision({
        fingerprint: alert.fingerprint,
        alertId: alert.id,
        decision: 'ACCEPTED',
        duplicate: false,
        cooldownSuppressed: false,
        firstSeenAt: now,
        lastSeenAt: now,
        nextEligibleAt: now,
        occurrenceCount: 1,
        evaluatedAt: now,
        reason: 'Deduplication policy is disabled'
      });
    }

    // Determine scope key
    let scopeKey = '';
    if (policy.scope === 'GLOBAL') {
      scopeKey = alert.fingerprint;
    } else if (policy.scope === 'PER_RULE') {
      if (!alert.ruleId) {
        throw new AlertDeduplicationError('alert ruleId is required for PER_RULE deduplication scope');
      }
      scopeKey = `${alert.ruleId}:${alert.fingerprint}`;
    } else if (policy.scope === 'PER_SOURCE') {
      if (!alert.sourceId) {
        throw new AlertDeduplicationError('alert sourceId is required for PER_SOURCE deduplication scope');
      }
      scopeKey = `${alert.sourceId}:${alert.fingerprint}`;
    } else {
      throw new AlertDeduplicationError(`Invalid deduplication scope configuration: ${policy.scope}`);
    }

    const existing = this._records.get(scopeKey);

    if (!existing) {
      // First occurrence
      const cooldownMs = policy.cooldownMs;
      const nextEligibleAt = now + cooldownMs;

      const record = createDeduplicationRecord({
        fingerprint: alert.fingerprint,
        firstSeenAt: now,
        lastSeenAt: now,
        occurrenceCount: 1,
        acceptedCount: 1,
        duplicateCount: 0,
        cooldownSuppressionCount: 0,
        nextEligibleAt,
        ruleId: alert.ruleId,
        sourceId: alert.sourceId
      });

      this.saveRecord(scopeKey, record, policy.maxHistorySize || 1000);

      return createDeduplicationDecision({
        fingerprint: alert.fingerprint,
        alertId: alert.id,
        decision: 'ACCEPTED',
        duplicate: false,
        cooldownSuppressed: false,
        firstSeenAt: now,
        lastSeenAt: now,
        nextEligibleAt,
        occurrenceCount: 1,
        evaluatedAt: now,
        reason: 'First occurrence of fingerprint'
      });
    }

    // Repeated occurrence
    const cooldownMs = policy.cooldownMs;

    if (now < existing.nextEligibleAt) {
      // Suppressed during cooldown
      const updatedRecord = createDeduplicationRecord({
        ...existing,
        occurrenceCount: existing.occurrenceCount + 1,
        cooldownSuppressionCount: existing.cooldownSuppressionCount + 1,
        duplicateCount: existing.duplicateCount + 1
      });

      this.saveRecord(scopeKey, updatedRecord, policy.maxHistorySize || 1000);

      return createDeduplicationDecision({
        fingerprint: alert.fingerprint,
        alertId: alert.id,
        decision: 'COOLDOWN_SUPPRESSED',
        duplicate: true,
        cooldownSuppressed: true,
        firstSeenAt: existing.firstSeenAt,
        lastSeenAt: existing.lastSeenAt,
        nextEligibleAt: existing.nextEligibleAt,
        occurrenceCount: updatedRecord.occurrenceCount,
        evaluatedAt: now,
        reason: `Suppressed during cooldown window (next eligible: ${existing.nextEligibleAt})`
      });
    } else {
      // Accepted after cooldown window has elapsed
      const nextEligibleAt = now + cooldownMs;

      const updatedRecord = createDeduplicationRecord({
        ...existing,
        lastSeenAt: now,
        occurrenceCount: existing.occurrenceCount + 1,
        acceptedCount: existing.acceptedCount + 1,
        nextEligibleAt
      });

      this.saveRecord(scopeKey, updatedRecord, policy.maxHistorySize || 1000);

      return createDeduplicationDecision({
        fingerprint: alert.fingerprint,
        alertId: alert.id,
        decision: 'ACCEPTED',
        duplicate: false,
        cooldownSuppressed: false,
        firstSeenAt: existing.firstSeenAt,
        lastSeenAt: now,
        nextEligibleAt,
        occurrenceCount: updatedRecord.occurrenceCount,
        evaluatedAt: now,
        reason: 'Accepted after cooldown elapsed'
      });
    }
  }

  public getRecord(identityKey: string): DeduplicationRecord | null {
    return this._records.get(identityKey) || null;
  }

  public clear(): void {
    this._records.clear();
    this._insertionOrder.length = 0;
  }

  public getDiagnostics(now: number): { trackedFingerprintCount: number; activeCooldownCount: number } {
    let activeCooldownCount = 0;
    for (const record of this._records.values()) {
      if (now < record.nextEligibleAt) {
        activeCooldownCount++;
      }
    }

    return {
      trackedFingerprintCount: this._records.size,
      activeCooldownCount
    };
  }

  private saveRecord(key: string, record: DeduplicationRecord, maxSize: number): void {
    if (!this._records.has(key)) {
      this._insertionOrder.push(key);
    }
    this._records.set(key, record);

    if (this._records.size > maxSize) {
      const oldestKey = this._insertionOrder.shift();
      if (oldestKey !== undefined) {
        this._records.delete(oldestKey);
      }
    }
  }
}
