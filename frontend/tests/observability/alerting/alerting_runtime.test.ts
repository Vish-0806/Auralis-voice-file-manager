import { describe, it, expect, vi } from 'vitest';
import {
  AlertingRuntime,
  AlertingProvider,
  createAlertRecord
} from '../../../src/observability';

describe('AlertingRuntime Coordination & DI Tests', () => {
  it('1. should construct with default AlertingProvider when none is supplied', () => {
    const runtime = new AlertingRuntime();
    expect(runtime.provider()).toBeInstanceOf(AlertingProvider);
  });

  it('2. should use supplied custom provider', () => {
    const customProvider = new AlertingProvider();
    const runtime = new AlertingRuntime(customProvider);
    expect(runtime.provider()).toBe(customProvider);
  });

  it('3. should have zero global mutable state (multiple instances are isolated)', async () => {
    const runtime1 = new AlertingRuntime();
    const runtime2 = new AlertingRuntime();

    await runtime1.initialize();
    await runtime2.initialize();

    const alert = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Message 1',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    runtime1.registerAlert(alert);
    expect(runtime1.listAlerts()).toHaveLength(1);
    expect(runtime2.listAlerts()).toHaveLength(0); // isolated!
  });

  it('4. should correctly delegate all interface methods to provider', async () => {
    const customProvider = new AlertingProvider();
    const runtime = new AlertingRuntime(customProvider);

    const initializeSpy = vi.spyOn(customProvider, 'initialize');
    const shutdownSpy = vi.spyOn(customProvider, 'shutdown');
    const getRuntimeStateSpy = vi.spyOn(customProvider, 'getRuntimeState');
    const getStateSpy = vi.spyOn(customProvider, 'getState');

    await runtime.initialize();
    expect(initializeSpy).toHaveBeenCalled();

    runtime.getRuntimeState();
    expect(getRuntimeStateSpy).toHaveBeenCalled();

    runtime.getState();
    expect(getStateSpy).toHaveBeenCalled();

    const alert = createAlertRecord({
      id: 'alert-2',
      sourceId: 'src-2',
      severity: 'WARNING',
      state: 'ACTIVE',
      title: 'Alert 2',
      message: 'Message 2',
      createdAt: Date.now(),
      updatedAt: Date.now()
    });

    const registerSpy = vi.spyOn(customProvider, 'registerAlert');
    const getSpy = vi.spyOn(customProvider, 'getAlert');
    const hasSpy = vi.spyOn(customProvider, 'hasAlert');
    const listSpy = vi.spyOn(customProvider, 'listAlerts');
    const statsSpy = vi.spyOn(customProvider, 'getStatistics');
    const diagSpy = vi.spyOn(customProvider, 'getDiagnostics');
    const removeSpy = vi.spyOn(customProvider, 'removeAlert');
    const clearSpy = vi.spyOn(customProvider, 'clearAlerts');

    runtime.registerAlert(alert);
    expect(registerSpy).toHaveBeenCalledWith(alert);

    runtime.getAlert('alert-2');
    expect(getSpy).toHaveBeenCalledWith('alert-2');

    runtime.hasAlert('alert-2');
    expect(hasSpy).toHaveBeenCalledWith('alert-2');

    runtime.listAlerts();
    expect(listSpy).toHaveBeenCalled();

    runtime.getStatistics();
    expect(statsSpy).toHaveBeenCalled();

    runtime.getDiagnostics();
    expect(diagSpy).toHaveBeenCalled();

    runtime.removeAlert('alert-2');
    expect(removeSpy).toHaveBeenCalledWith('alert-2');

    runtime.clearAlerts();
    expect(clearSpy).toHaveBeenCalled();

    const registerRuleSpy = vi.spyOn(customProvider, 'registerRule');
    const getRuleSpy = vi.spyOn(customProvider, 'getRule');
    const hasRuleSpy = vi.spyOn(customProvider, 'hasRule');
    const listRulesSpy = vi.spyOn(customProvider, 'listRules');
    const updateRuleSpy = vi.spyOn(customProvider, 'updateRule');
    const unregisterRuleSpy = vi.spyOn(customProvider, 'unregisterRule');
    const clearRulesSpy = vi.spyOn(customProvider, 'clearRules');

    const rule = {
      id: 'rule-x',
      name: 'Rule X',
      description: 'Desc',
      enabled: true,
      severity: 'ERROR' as const,
      conditions: { operator: 'ALL' as const, conditions: [] },
      sourceId: 'src-1',
      tags: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      metadata: {}
    };

    runtime.registerRule(rule);
    expect(registerRuleSpy).toHaveBeenCalledWith(rule);

    runtime.getRule('rule-x');
    expect(getRuleSpy).toHaveBeenCalledWith('rule-x');

    runtime.hasRule('rule-x');
    expect(hasRuleSpy).toHaveBeenCalledWith('rule-x');

    runtime.listRules();
    expect(listRulesSpy).toHaveBeenCalled();

    runtime.updateRule(rule);
    expect(updateRuleSpy).toHaveBeenCalledWith(rule);

    runtime.unregisterRule('rule-x');
    expect(unregisterRuleSpy).toHaveBeenCalledWith('rule-x');

    runtime.clearRules();
    expect(clearRulesSpy).toHaveBeenCalled();

    await runtime.shutdown();
    expect(shutdownSpy).toHaveBeenCalled();
  });
});
