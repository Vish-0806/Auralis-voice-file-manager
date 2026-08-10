import { describe, it, expect, vi } from 'vitest';
import {
  MonitoringRuntime,
  MonitoringProvider,
  MonitoringRegistry,
  MonitoringRuntimeState,
  MonitorStatus,
  MonitoringComponentType,
  MonitoringRegistrationError,
  MonitoringStateError,
  MonitoringComponentNotFoundError,
  MonitoringCheckNotFoundError
} from '../../src/observability';

describe('Monitoring Foundation Tests (Phase 18.1)', () => {
  // 1. default provider creation
  it('1. verifies default provider creation in runtime constructor', () => {
    const runtime = new MonitoringRuntime();
    expect(runtime.provider()).toBeInstanceOf(MonitoringProvider);
  });

  // 2. injected provider creation
  it('2. verifies injected provider creation in runtime constructor', () => {
    const provider = new MonitoringProvider();
    const runtime = new MonitoringRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  // 3. runtime initialization
  it('3. verifies runtime initialization successfully transitions to READY', async () => {
    const runtime = new MonitoringRuntime();
    expect(runtime.getState()).toBe(MonitoringRuntimeState.UNINITIALIZED);
    await runtime.initialize();
    expect(runtime.getState()).toBe(MonitoringRuntimeState.READY);
  });

  // 4. runtime shutdown
  it('4. verifies runtime shutdown transitions from READY to STOPPED', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    expect(runtime.getState()).toBe(MonitoringRuntimeState.READY);
    await runtime.shutdown();
    expect(runtime.getState()).toBe(MonitoringRuntimeState.STOPPED);
  });

  // 5. initialization idempotency
  it('5. verifies initialization is idempotent', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    const state1 = runtime.getState();
    await runtime.initialize();
    const state2 = runtime.getState();
    expect(state1).toBe(MonitoringRuntimeState.READY);
    expect(state2).toBe(MonitoringRuntimeState.READY);
  });

  // 6. shutdown idempotency
  it('6. verifies shutdown is idempotent', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    await runtime.shutdown();
    const state1 = runtime.getState();
    await runtime.shutdown();
    const state2 = runtime.getState();
    expect(state1).toBe(MonitoringRuntimeState.STOPPED);
    expect(state2).toBe(MonitoringRuntimeState.STOPPED);
  });

  // 7. invalid lifecycle handling
  it('7. verifies invalid lifecycle state transitions throw errors', async () => {
    const runtime = new MonitoringRuntime();
    // Cannot shutdown before initialized
    await expect(runtime.shutdown()).rejects.toThrow(MonitoringStateError);

    await runtime.initialize();
    await runtime.shutdown();
    // Cannot initialize from STOPPED state
    await expect(runtime.initialize()).rejects.toThrow(MonitoringStateError);

    // Operations when not ready should throw
    expect(() => runtime.listComponents()).toThrow(MonitoringStateError);
  });

  // 8. component registration
  it('8. verifies component registration registers successfully', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    const comp = runtime.registerComponent({
      id: 'c1',
      name: 'Component 1',
      type: MonitoringComponentType.SERVICE,
      metadata: { env: 'prod' }
    });
    expect(comp.id).toBe('c1');
    expect(comp.name).toBe('Component 1');
    expect(comp.type).toBe(MonitoringComponentType.SERVICE);
    expect(comp.status).toBe(MonitorStatus.UNKNOWN);
    expect(comp.metadata.env).toBe('prod');
  });

  // 9. duplicate component rejection
  it('9. verifies duplicate component registration throws error', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'Comp 1', type: MonitoringComponentType.SERVICE });
    expect(() => {
      runtime.registerComponent({ id: 'c1', name: 'Comp 2', type: MonitoringComponentType.SERVICE });
    }).toThrow(MonitoringRegistrationError);
  });

  // 10. component lookup
  it('10. verifies component lookup and list methods', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'b_comp', name: 'B', type: MonitoringComponentType.SERVICE });
    runtime.registerComponent({ id: 'a_comp', name: 'A', type: MonitoringComponentType.SERVICE });

    const comp = runtime.getComponent('a_comp');
    expect(comp?.name).toBe('A');

    const list = runtime.listComponents();
    expect(list.length).toBe(2);
    // Deterministic sorting (alphabetical by ID)
    expect(list[0].id).toBe('a_comp');
    expect(list[1].id).toBe('b_comp');
  });

  // 11. component removal
  it('11. unregisters a component and its associated checks', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      execute: () => {}
    });

    expect(runtime.listComponents().length).toBe(1);
    expect(runtime.listChecks().length).toBe(1);

    runtime.unregisterComponent('c1');
    expect(runtime.listComponents().length).toBe(0);
    expect(runtime.listChecks().length).toBe(0); // Checks cleaned up!
  });

  // 12. check registration
  it('12. verifies check registration succeeds', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    const check = runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      description: 'Test check',
      enabled: true,
      executionOrder: 2,
      timeoutMs: 1000,
      execute: () => {}
    });

    expect(check.id).toBe('check1');
    expect(check.componentId).toBe('c1');
    expect(check.executionOrder).toBe(2);
    expect(check.timeoutMs).toBe(1000);
  });

  // 13. duplicate check rejection
  it('13. verifies duplicate check registration throws error', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });

    expect(() => {
      runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 2', execute: () => {} });
    }).toThrow(MonitoringRegistrationError);
  });

  // 14. check lookup
  it('14. verifies check lookup and list sorting methods', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check_b', componentId: 'c1', name: 'B', executionOrder: 2, execute: () => {} });
    runtime.registerCheck({ id: 'check_a', componentId: 'c1', name: 'A', executionOrder: 1, execute: () => {} });
    runtime.registerCheck({ id: 'check_c', componentId: 'c1', name: 'C', executionOrder: 2, execute: () => {} });

    const check = runtime.getCheck('check_a');
    expect(check?.name).toBe('A');

    const list = runtime.listChecks();
    expect(list.length).toBe(3);
    // Sorted by executionOrder ascending, then alphabetically by ID
    expect(list[0].id).toBe('check_a');
    expect(list[1].id).toBe('check_b');
    expect(list[2].id).toBe('check_c');
  });

  // 15. check removal
  it('15. unregisters a single check', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });

    expect(runtime.listChecks().length).toBe(1);
    runtime.unregisterCheck('check1');
    expect(runtime.listChecks().length).toBe(0);
  });

  // 16. synchronous check execution
  it('16. executes a synchronous check successfully', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      execute: () => {}
    });

    const result = await runtime.executeCheck('check1');
    expect(result.status).toBe(MonitorStatus.HEALTHY);
    expect(result.durationMs).toBeLessThanOrEqual(50);
    expect(runtime.getComponent('c1')?.status).toBe(MonitorStatus.HEALTHY);
  });

  // 17. asynchronous check execution
  it('17. executes an asynchronous check successfully', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      execute: async () => {
        await new Promise(r => setTimeout(r, 10));
      }
    });

    const result = await runtime.executeCheck('check1');
    expect(result.status).toBe(MonitorStatus.HEALTHY);
    expect(result.durationMs).toBeGreaterThanOrEqual(10);
  });

  // 18. failed check isolation
  it('18. verifies check failures are isolated and do not crash runtime', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      execute: () => {
        throw new Error('Forced failure');
      }
    });

    const result = await runtime.executeCheck('check1');
    expect(result.status).toBe(MonitorStatus.UNHEALTHY);
    expect(result.message).toBe('Forced failure');
    expect(runtime.getComponent('c1')?.status).toBe(MonitorStatus.UNHEALTHY);
  });

  // 19. thrown check exception handling
  it('19. handles thrown custom exceptions with status properties', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({
      id: 'check1',
      componentId: 'c1',
      name: 'Check 1',
      execute: () => {
        const error = new Error('Degraded status message') as any;
        error.status = MonitorStatus.DEGRADED;
        throw error;
      }
    });

    const result = await runtime.executeCheck('check1');
    expect(result.status).toBe(MonitorStatus.DEGRADED);
    expect(runtime.getComponent('c1')?.status).toBe(MonitorStatus.DEGRADED);
  });

  // 20. health aggregation
  it('20. verifies health aggregation rules', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    
    // No registered components: UNKNOWN
    expect(runtime.evaluateHealth().status).toBe(MonitorStatus.UNKNOWN);

    // 1 component, healthy
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });
    await runtime.executeCheck('check1');
    expect(runtime.evaluateHealth().status).toBe(MonitorStatus.HEALTHY);

    // 1 component degraded, 1 component healthy: DEGRADED
    runtime.registerComponent({ id: 'c2', name: 'C2', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check2', componentId: 'c2', name: 'Check 2', execute: () => MonitorStatus.DEGRADED });
    await runtime.executeCheck('check2');
    expect(runtime.evaluateHealth().status).toBe(MonitorStatus.DEGRADED);

    // 1 component unhealthy, 1 component degraded, 1 component healthy: UNHEALTHY
    runtime.registerComponent({ id: 'c3', name: 'C3', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check3', componentId: 'c3', name: 'Check 3', execute: () => MonitorStatus.UNHEALTHY });
    await runtime.executeCheck('check3');
    expect(runtime.evaluateHealth().status).toBe(MonitorStatus.UNHEALTHY);

    // Disabled components should not override unhealthy
    runtime.registerComponent({ id: 'c4', name: 'C4', type: MonitoringComponentType.SERVICE, enabled: false, status: MonitorStatus.DISABLED });
    expect(runtime.evaluateHealth().status).toBe(MonitorStatus.UNHEALTHY);
  });

  // 21. statistics aggregation
  it('21. verifies statistics counters aggregate correctly', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });
    runtime.registerCheck({ id: 'check2', componentId: 'c1', name: 'Check 2', execute: () => MonitorStatus.DEGRADED });
    runtime.registerCheck({ id: 'check3', componentId: 'c1', name: 'Check 3', execute: () => { throw new Error(); } });
    runtime.registerCheck({ id: 'check4', componentId: 'c1', name: 'Check 4', enabled: false, execute: () => {} });

    await runtime.executeAllChecks();

    const stats = runtime.getStatistics();
    expect(stats.totalChecks).toBe(4);
    expect(stats.successfulChecks).toBe(1);
    expect(stats.degradedChecks).toBe(1);
    expect(stats.failedChecks).toBe(1);
    expect(stats.skippedChecks).toBe(1);
    expect(stats.lastCheckAt).toBeDefined();
    expect(stats.averageExecutionTimeMs).toBeLessThanOrEqual(50);
  });

  // 22. immutable models
  it('22. verifies deep freezing of domain models', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    const comp = runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE, metadata: { info: { a: 1 } } });
    expect(Object.isFrozen(comp)).toBe(true);
    expect(Object.isFrozen(comp.metadata)).toBe(true);
    expect(Object.isFrozen(comp.metadata.info)).toBe(true);
  });

  // 23. defensive snapshots
  it('23. verifies snapshots cannot be mutated by caller', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    const list = runtime.listComponents();
    expect(() => {
      (list as any)[0] = null;
    }).toThrow();
  });

  // 24. missing component errors
  it('24. throws error when registering a check for missing component', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    expect(() => {
      runtime.registerCheck({ id: 'check1', componentId: 'missing', name: 'Check', execute: () => {} });
    }).toThrow(MonitoringComponentNotFoundError);
  });

  // 25. missing check errors
  it('25. throws error when executing missing check', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    await expect(runtime.executeCheck('missing')).rejects.toThrow(MonitoringCheckNotFoundError);
  });

  // 26. provider delegation
  it('26. verifies runtime delegates state and metadata getters to provider', async () => {
    const provider = new MonitoringProvider();
    const runtime = new MonitoringRuntime(provider);
    const spy = vi.spyOn(provider, 'getState');
    runtime.getState();
    expect(spy).toHaveBeenCalled();
  });

  // 27. runtime delegation
  it('27. verifies runtime delegates register operations to provider', async () => {
    const provider = new MonitoringProvider();
    const runtime = new MonitoringRuntime(provider);
    const spy = vi.spyOn(provider, 'registerComponent');
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    expect(spy).toHaveBeenCalled();
  });

  // 28. dependency injection
  it('28. verifies custom provider DI works', () => {
    const customProvider = new MonitoringProvider();
    const runtime = new MonitoringRuntime(customProvider);
    expect(runtime.provider()).toBe(customProvider);
  });

  // 29. registry clear
  it('29. clears components and checks in registry', async () => {
    const registry = new MonitoringRegistry();
    registry.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    registry.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });

    expect(registry.listComponents().length).toBe(1);
    expect(registry.listChecks().length).toBe(1);

    registry.clear();
    expect(registry.listComponents().length).toBe(0);
    expect(registry.listChecks().length).toBe(0);
  });

  // 30. diagnostics snapshot
  it('30. generates complete diagnostics snapshot', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    runtime.registerCheck({ id: 'check1', componentId: 'c1', name: 'Check 1', execute: () => {} });

    const diag = runtime.getDiagnostics();
    expect(diag.runtimeState).toBe(MonitoringRuntimeState.READY);
    expect(diag.componentCount).toBe(1);
    expect(diag.checkCount).toBe(1);
    expect(diag.statistics).toBeDefined();
    expect(diag.health).toBeDefined();
    expect(diag.generatedAt).toBeDefined();
  });

  // 31. performance sanity checks
  it('31. verifies registration and lookup times are low', async () => {
    const runtime = new MonitoringRuntime();
    await runtime.initialize();

    const startReg = performance.now();
    runtime.registerComponent({ id: 'c1', name: 'C1', type: MonitoringComponentType.SERVICE });
    const endReg = performance.now();
    expect(endReg - startReg).toBeLessThan(10); // Check under 10ms allowance for CI/CD

    const startLookup = performance.now();
    runtime.getComponent('c1');
    const endLookup = performance.now();
    expect(endLookup - startLookup).toBeLessThan(10);
  });
});
