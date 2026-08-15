import { describe, it, expect } from 'vitest';
import {
  AlertLifecycleManager,
  AlertingProvider,
  AlertingRuntime,
  AlertLifecycleTransitionError,
  createAlertRecord
} from '../../../src/observability';

describe('Alert Lifecycle Manager Tests', () => {
  const manager = new AlertLifecycleManager();

  it('1. Lifecycle initialization & duplicate initialization (idempotency)', () => {
    manager.clearAll();
    const r1 = manager.initializeRecord('alert-1', 'fp-1', 1000);
    expect(r1.alertId).toBe('alert-1');
    expect(r1.state).toBe('ACTIVE');
    expect(r1.createdAt).toBe(1000);
    expect(r1.history).toHaveLength(1);
    expect(r1.history[0].operation).toBe('INITIALIZE');

    const r2 = manager.initializeRecord('alert-1', 'fp-1', 2000);
    expect(r2).toBe(r1);
    expect(r2.history).toHaveLength(1);
  });

  it('2. Legal Transitions (ACTIVE -> ACKNOWLEDGED -> RESOLVED -> ACTIVE -> CLOSED)', () => {
    manager.clearAll();
    manager.initializeRecord('alert-1', 'fp-1', 1000);

    const rAcknowledge = manager.transition('alert-1', 'ACKNOWLEDGED', 'USER', 'ACKNOWLEDGE', 'Assigned to dev', {}, 1100);
    expect(rAcknowledge.state).toBe('ACKNOWLEDGED');
    expect(rAcknowledge.history).toHaveLength(2);
    expect(rAcknowledge.history[1].actor).toBe('USER');
    expect(rAcknowledge.history[1].reason).toBe('Assigned to dev');

    const rResolve = manager.transition('alert-1', 'RESOLVED', 'AUTOMATION', 'RESOLVE', 'Auto fixed', {}, 1200);
    expect(rResolve.state).toBe('RESOLVED');
    expect(rResolve.history).toHaveLength(3);

    const rReopen = manager.transition('alert-1', 'ACTIVE', 'SYSTEM', 'REOPEN', 'Triggered again', {}, 1300);
    expect(rReopen.state).toBe('ACTIVE');
    expect(rReopen.history).toHaveLength(4);

    const rClose = manager.transition('alert-1', 'CLOSED', 'USER', 'CLOSE', 'Resolved manually', {}, 1400);
    expect(rClose.state).toBe('CLOSED');
    expect(rClose.history).toHaveLength(5);
  });

  it('3. Terminal CLOSED behavior & invalid transitions', () => {
    manager.clearAll();
    manager.initializeRecord('alert-1', 'fp-1', 1000);
    manager.transition('alert-1', 'CLOSED', 'USER', 'CLOSE', 'Done', {}, 1100);

    expect(() => manager.transition('alert-1', 'ACTIVE', 'USER', 'REOPEN', 'Try to reopen', {}, 1200)).toThrow(AlertLifecycleTransitionError);

    expect(manager.getRecord('alert-1')?.state).toBe('CLOSED');
  });

  it('4. Invalid transition rejection (state remains unchanged)', () => {
    manager.clearAll();
    manager.initializeRecord('alert-1', 'fp-1', 1000);
    manager.transition('alert-1', 'RESOLVED', 'SYSTEM', 'RESOLVE', 'resolved', {}, 1100);

    expect(() => manager.transition('alert-1', 'ACKNOWLEDGED', 'USER', 'ACK', 'invalid', {}, 1200)).toThrow(AlertLifecycleTransitionError);

    expect(manager.getRecord('alert-1')?.state).toBe('RESOLVED');
  });

  it('5. Immutability checks', () => {
    manager.clearAll();
    const record = manager.initializeRecord('alert-1', 'fp-1', 1000);
    expect(Object.isFrozen(record)).toBe(true);
    expect(Object.isFrozen(record.history)).toBe(true);

    expect(() => {
      (record as any).state = 'CLOSED';
    }).toThrow();
  });

  it('6. Bounded history behavior (FIFO eviction)', () => {
    const smallManager = new AlertLifecycleManager(2);
    smallManager.initializeRecord('alert-1', 'fp-1', 1000);
    smallManager.initializeRecord('alert-2', 'fp-2', 1000);
    smallManager.initializeRecord('alert-3', 'fp-3', 1000);

    expect(smallManager.getRecord('alert-1')).toBeNull();
    expect(smallManager.getRecord('alert-2')).toBeDefined();
    expect(smallManager.getRecord('alert-3')).toBeDefined();
  });

  it('7. Lifecycle statistics and diagnostics checks', () => {
    manager.clearAll();
    manager.initializeRecord('alert-1', 'fp-1', 1000);
    manager.transition('alert-1', 'ACKNOWLEDGED', 'USER', 'ACK', 'Acked', {}, 1100);
    manager.transition('alert-1', 'RESOLVED', 'USER', 'RESOLVE', 'Fixed', {}, 1200);

    const stats = manager.getTransitionStats();
    expect(stats.lifecycleTransitions).toBe(2);
    expect(stats.acknowledgements).toBe(1);
    expect(stats.resolutions).toBe(1);
    expect(stats.activeAlerts).toBe(0);
    expect(stats.resolvedAlerts).toBe(1);

    const diagnostics = manager.getDiagnostics();
    expect(diagnostics.resolvedCount).toBe(1);
    expect(diagnostics.historySize).toBe(3);
    expect(diagnostics.lastTransitionTimestamp).toBe(1200);
  });

  it('8. Provider and Runtime delegation', async () => {
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    const alert = createAlertRecord({
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

    runtime.registerAlert(alert);

    const record = runtime.getAlertLifecycle('alert-1');
    expect(record).toBeDefined();
    expect(record?.state).toBe('ACTIVE');

    runtime.acknowledgeAlert('alert-1', 'USER', 'Acked in test', {}, 1100);
    expect(runtime.getAlertLifecycle('alert-1')?.state).toBe('ACKNOWLEDGED');

    const history = runtime.getAlertLifecycleHistory('alert-1');
    expect(history).toHaveLength(2);
    expect(history[1].actor).toBe('USER');
    expect(history[1].reason).toBe('Acked in test');
  });
});
