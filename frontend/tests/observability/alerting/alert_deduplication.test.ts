import { describe, it, expect } from 'vitest';
import {
  AlertDeduplicator,
  AlertingProvider,
  AlertingRuntime,
  createAlertRecord,
  DeduplicationPolicy,
  AlertDeduplicationError
} from '../../../src/observability';

describe('AlertDeduplicator & Cooldown Tests', () => {
  const deduplicator = new AlertDeduplicator();

  const mockAlert = createAlertRecord({
    id: 'alert-1',
    sourceId: 'src-1',
    severity: 'ERROR',
    state: 'ACTIVE',
    title: 'Alert 1',
    message: 'Message 1',
    createdAt: 1000,
    updatedAt: 1000,
    metadata: {}
  });

  const alertWithFingerprint = {
    ...mockAlert,
    ruleId: 'rule-1',
    fingerprint: 'fp-1'
  };

  const defaultPolicy: DeduplicationPolicy = {
    enabled: true,
    cooldownMs: 5000,
    scope: 'PER_RULE',
    maxHistorySize: 100
  };

  it('1. First occurrence is ACCEPTED', () => {
    deduplicator.clear();
    const decision = deduplicator.check(alertWithFingerprint, defaultPolicy, 1000);

    expect(decision.decision).toBe('ACCEPTED');
    expect(decision.duplicate).toBe(false);
    expect(decision.cooldownSuppressed).toBe(false);
    expect(decision.firstSeenAt).toBe(1000);
    expect(decision.lastSeenAt).toBe(1000);
    expect(decision.nextEligibleAt).toBe(6000); // 1000 + 5000
    expect(decision.occurrenceCount).toBe(1);
  });

  it('2. Same fingerprint during cooldown is COOLDOWN_SUPPRESSED', () => {
    const decision = deduplicator.check(alertWithFingerprint, defaultPolicy, 2000);

    expect(decision.decision).toBe('COOLDOWN_SUPPRESSED');
    expect(decision.duplicate).toBe(true);
    expect(decision.cooldownSuppressed).toBe(true);
    expect(decision.firstSeenAt).toBe(1000);
    expect(decision.nextEligibleAt).toBe(6000); // unchanged
    expect(decision.occurrenceCount).toBe(2);
  });

  it('3. Same fingerprint exactly at nextEligibleAt is ACCEPTED', () => {
    const decision = deduplicator.check(alertWithFingerprint, defaultPolicy, 6000);

    expect(decision.decision).toBe('ACCEPTED');
    expect(decision.duplicate).toBe(false);
    expect(decision.cooldownSuppressed).toBe(false);
    expect(decision.lastSeenAt).toBe(6000);
    expect(decision.nextEligibleAt).toBe(11000); // 6000 + 5000
    expect(decision.occurrenceCount).toBe(3);
  });

  it('4. Cooldown boundary checks', () => {
    deduplicator.clear();
    deduplicator.check(alertWithFingerprint, defaultPolicy, 1000);
    const resDuring = deduplicator.check(alertWithFingerprint, defaultPolicy, 5999);
    expect(resDuring.decision).toBe('COOLDOWN_SUPPRESSED');

    const resAfter = deduplicator.check(alertWithFingerprint, defaultPolicy, 6000);
    expect(resAfter.decision).toBe('ACCEPTED');
  });

  it('5. Different fingerprints are independent', () => {
    deduplicator.clear();
    const alert1 = { ...alertWithFingerprint, fingerprint: 'fp-1' };
    const alert2 = { ...alertWithFingerprint, fingerprint: 'fp-2' };

    const dec1 = deduplicator.check(alert1, defaultPolicy, 1000);
    const dec2 = deduplicator.check(alert2, defaultPolicy, 1000);

    expect(dec1.decision).toBe('ACCEPTED');
    expect(dec2.decision).toBe('ACCEPTED');
  });

  it('6. Cooldown disabled with 0ms', () => {
    deduplicator.clear();
    const zeroPolicy = { ...defaultPolicy, cooldownMs: 0 };

    const res1 = deduplicator.check(alertWithFingerprint, zeroPolicy, 1000);
    const res2 = deduplicator.check(alertWithFingerprint, zeroPolicy, 1500);

    expect(res1.decision).toBe('ACCEPTED');
    expect(res2.decision).toBe('ACCEPTED');
    expect(res2.occurrenceCount).toBe(2);
  });

  it('7. Rejects invalid policies and timestamps', () => {
    const badPolicy = { ...defaultPolicy, cooldownMs: -100 };
    expect(() => deduplicator.check(alertWithFingerprint, badPolicy, 1000)).toThrow(AlertDeduplicationError);

    const infPolicy = { ...defaultPolicy, cooldownMs: Infinity };
    expect(() => deduplicator.check(alertWithFingerprint, infPolicy, 1000)).toThrow(AlertDeduplicationError);

    expect(() => deduplicator.check(alertWithFingerprint, defaultPolicy, -1000)).toThrow(AlertDeduplicationError);

    expect(() => deduplicator.check(alertWithFingerprint, defaultPolicy, NaN)).toThrow(AlertDeduplicationError);
  });

  it('8. GLOBAL, PER_RULE, and PER_SOURCE scope checks', () => {
    const globalPolicy = { ...defaultPolicy, scope: 'GLOBAL' as const };
    deduplicator.clear();
    const a1 = { ...alertWithFingerprint, ruleId: 'rule-a', fingerprint: 'fp-1' };
    const a2 = { ...alertWithFingerprint, ruleId: 'rule-b', fingerprint: 'fp-1' };

    expect(deduplicator.check(a1, globalPolicy, 1000).decision).toBe('ACCEPTED');
    expect(deduplicator.check(a2, globalPolicy, 2000).decision).toBe('COOLDOWN_SUPPRESSED');

    const rulePolicy = { ...defaultPolicy, scope: 'PER_RULE' as const };
    deduplicator.clear();
    expect(deduplicator.check(a1, rulePolicy, 1000).decision).toBe('ACCEPTED');
    expect(deduplicator.check(a2, rulePolicy, 2000).decision).toBe('ACCEPTED');

    const sourcePolicy = { ...defaultPolicy, scope: 'PER_SOURCE' as const };
    deduplicator.clear();
    const a3 = { ...alertWithFingerprint, sourceId: 'src-a', fingerprint: 'fp-1' };
    const a4 = { ...alertWithFingerprint, sourceId: 'src-b', fingerprint: 'fp-1' };

    expect(deduplicator.check(a3, sourcePolicy, 1000).decision).toBe('ACCEPTED');
    expect(deduplicator.check(a4, sourcePolicy, 2000).decision).toBe('ACCEPTED');
  });

  it('9. FIFO Eviction for bounded retention', () => {
    deduplicator.clear();
    const capPolicy = { ...defaultPolicy, scope: 'GLOBAL' as const, maxHistorySize: 3 };

    const a1 = { ...alertWithFingerprint, fingerprint: 'fp-1' };
    const a2 = { ...alertWithFingerprint, fingerprint: 'fp-2' };
    const a3 = { ...alertWithFingerprint, fingerprint: 'fp-3' };
    const a4 = { ...alertWithFingerprint, fingerprint: 'fp-4' };

    deduplicator.check(a1, capPolicy, 1000);
    deduplicator.check(a2, capPolicy, 1000);
    deduplicator.check(a3, capPolicy, 1000);

    expect(deduplicator.getRecord('fp-1')).toBeDefined();

    deduplicator.check(a4, capPolicy, 1000);

    expect(deduplicator.getRecord('fp-1')).toBeNull();
    expect(deduplicator.getRecord('fp-4')).toBeDefined();
  });

  it('10. Immutability checks', () => {
    deduplicator.clear();
    const decision = deduplicator.check(alertWithFingerprint, defaultPolicy, 1000);
    expect(Object.isFrozen(decision)).toBe(true);

    const record = deduplicator.getRecord('rule-1:fp-1')!;
    expect(Object.isFrozen(record)).toBe(true);

    expect(() => {
      (decision as any).occurrenceCount = 100;
    }).toThrow();
  });

  it('11. Provider and Runtime delegation & Statistics updates', async () => {
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    const now = Date.now();
    const decision1 = runtime.checkDeduplication(alertWithFingerprint, now);
    expect(decision1.decision).toBe('ACCEPTED');

    const decision2 = runtime.checkDeduplication(alertWithFingerprint, now + 1000);
    expect(decision2.decision).toBe('COOLDOWN_SUPPRESSED');

    const stats = runtime.getStatistics();
    expect(stats.totalDeduplicationChecks).toBe(2);
    expect(stats.acceptedAlertCount).toBe(1);
    expect(stats.duplicateAlertCount).toBe(1);
    expect(stats.cooldownSuppressedCount).toBe(1);
    expect(stats.activeCooldownCount).toBe(1);
    expect(stats.trackedFingerprintCount).toBe(1);

    runtime.clearDeduplication();
    expect(runtime.getStatistics().trackedFingerprintCount).toBe(0);
  });
});
