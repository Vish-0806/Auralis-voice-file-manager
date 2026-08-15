import { describe, it, expect } from 'vitest';
import {
  AlertRegistry,
  AlertValidationError,
  AlertNotFoundError,
  createAlertRecord
} from '../../../src/observability';

describe('AlertRegistry Tests', () => {
  it('1. should register alerts and list them in deterministic insertion order', () => {
    const registry = new AlertRegistry();

    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const a2 = createAlertRecord({
      id: 'alert-2',
      sourceId: 'src-2',
      severity: 'WARNING',
      state: 'ACTIVE',
      title: 'Alert 2',
      message: 'Msg 2',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    registry.registerAlert(a2);

    const alerts = registry.listAlerts();
    expect(alerts).toHaveLength(2);
    expect(alerts[0].id).toBe('alert-1');
    expect(alerts[1].id).toBe('alert-2');
  });

  it('2. should reject duplicate alert IDs', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    expect(() => registry.registerAlert(a1)).toThrow(AlertValidationError);
  });

  it('3. should lookup alerts in O(1) conceptually', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    expect(registry.getAlert('alert-1')).toBeDefined();
    expect(registry.getAlert('alert-missing')).toBeNull();
  });

  it('4. should handle missing alerts on removal', () => {
    const registry = new AlertRegistry();
    expect(() => registry.removeAlert('missing')).toThrow(AlertNotFoundError);
  });

  it('5. should support removal and clear operations', () => {
    const registry = new AlertRegistry();
    const a1 = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Msg 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });
    const a2 = createAlertRecord({
      id: 'alert-2',
      sourceId: 'src-2',
      severity: 'WARNING',
      state: 'ACTIVE',
      title: 'Alert 2',
      message: 'Msg 2',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    registry.registerAlert(a1);
    registry.registerAlert(a2);

    registry.removeAlert('alert-1');
    expect(registry.listAlerts()).toHaveLength(1);
    expect(registry.listAlerts()[0].id).toBe('alert-2');

    registry.clear();
    expect(registry.listAlerts()).toHaveLength(0);
  });
});
