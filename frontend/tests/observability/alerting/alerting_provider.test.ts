import { describe, it, expect } from 'vitest';
import {
  AlertingProvider,
  AlertingRuntimeState,
  AlertingStateError,
  createAlertRecord
} from '../../../src/observability';

describe('AlertingProvider Lifecycle & API Tests', () => {
  it('1. should start in UNINITIALIZED state', () => {
    const provider = new AlertingProvider();
    expect(provider.getRuntimeState()).toBe(AlertingRuntimeState.UNINITIALIZED);
  });

  it('2. should initialize to READY state, and be idempotent', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();
    expect(provider.getRuntimeState()).toBe(AlertingRuntimeState.READY);

    // Repeated call should be idempotent
    await provider.initialize();
    expect(provider.getRuntimeState()).toBe(AlertingRuntimeState.READY);
  });

  it('3. should shutdown to STOPPED state, and be idempotent', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();
    await provider.shutdown();
    expect(provider.getRuntimeState()).toBe(AlertingRuntimeState.STOPPED);

    // Repeated call should be idempotent
    await provider.shutdown();
    expect(provider.getRuntimeState()).toBe(AlertingRuntimeState.STOPPED);
  });

  it('4. should throw state errors for invalid transitions', async () => {
    const provider = new AlertingProvider();

    // Cannot shutdown when UNINITIALIZED
    await expect(provider.shutdown()).rejects.toThrow(AlertingStateError);

    await provider.initialize();
    await provider.shutdown();

    // Cannot initialize from STOPPED state
    await expect(provider.initialize()).rejects.toThrow(AlertingStateError);
  });

  it('5. should restrict API access to READY state', async () => {
    const provider = new AlertingProvider();
    const alert = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    // Check throws when UNINITIALIZED
    expect(() => provider.registerAlert(alert)).toThrow(AlertingStateError);
    expect(() => provider.getAlert('alert-1')).toThrow(AlertingStateError);
    expect(() => provider.hasAlert('alert-1')).toThrow(AlertingStateError);
    expect(() => provider.listAlerts()).toThrow(AlertingStateError);
    expect(() => provider.getStatistics()).toThrow(AlertingStateError);
    expect(() => provider.getDiagnostics()).toThrow(AlertingStateError);
    expect(() => provider.removeAlert('alert-1')).toThrow(AlertingStateError);
    expect(() => provider.clearAlerts()).toThrow(AlertingStateError);

    await provider.initialize();

    // Works when READY
    provider.registerAlert(alert);
    expect(provider.getAlert('alert-1')).toBeDefined();
    expect(provider.hasAlert('alert-1')).toBe(true);
    expect(provider.listAlerts()).toHaveLength(1);
    expect(provider.getStatistics().registeredAlertCount).toBe(1);
    expect(provider.getDiagnostics().registeredAlertCount).toBe(1);
    provider.removeAlert('alert-1');
    expect(provider.listAlerts()).toHaveLength(0);

    provider.registerAlert(alert);
    provider.clearAlerts();
    expect(provider.listAlerts()).toHaveLength(0);

    await provider.shutdown();

    // Throws when STOPPED
    expect(() => provider.registerAlert(alert)).toThrow(AlertingStateError);
    expect(() => provider.getAlert('alert-1')).toThrow(AlertingStateError);
  });

  it('6. benchmark: alert registration, lookup, and diagnostics generation via provider', async () => {
    const provider = new AlertingProvider();
    await provider.initialize();
    const count = 1000;

    const alerts = [];
    for (let i = 0; i < count; i++) {
      alerts.push(createAlertRecord({
        id: `alert-${i}`,
        sourceId: `src-${i}`,
        severity: 'INFO',
        state: 'ACTIVE',
        title: `Title ${i}`,
        message: `Msg ${i}`,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        metadata: {}
      }));
    }

    const startReg = performance.now();
    for (let i = 0; i < count; i++) {
      provider.registerAlert(alerts[i]);
    }
    const endReg = performance.now();
    const regTime = endReg - startReg;

    const startLookup = performance.now();
    for (let i = 0; i < count; i++) {
      provider.getAlert(`alert-${i}`);
    }
    const endLookup = performance.now();
    const lookupTime = endLookup - startLookup;

    const startDiag = performance.now();
    for (let i = 0; i < count; i++) {
      provider.getDiagnostics();
    }
    const endDiag = performance.now();
    const diagTime = endDiag - startDiag;

    console.log(`\n=== ALERTING FOUNDATION BENCHMARK RESULTS (${count} iterations) ===`);
    console.log(`Alert Registration: ${regTime.toFixed(3)} ms (${(regTime / count).toFixed(4)} ms/op)`);
    console.log(`Alert Lookup:       ${lookupTime.toFixed(3)} ms (${(lookupTime / count).toFixed(4)} ms/op)`);
    console.log(`Diagnostics Gen:    ${diagTime.toFixed(3)} ms (${(diagTime / count).toFixed(4)} ms/op)`);
    console.log(`==================================================================\n`);
  }, 30000);
});

