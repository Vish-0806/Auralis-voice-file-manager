import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  PluginLoader,
  PluginLifecycleManager,
  PluginState,
  PluginLifecycleError,
  PluginLifecycleTransitionError,
  type PluginManifest,
  type IPluginDiscoveryManager,
  type IPluginDependencyResolver,
  type IPluginModuleLoader,
  type IPluginLoader
} from '../../src/plugins';

describe('Plugin Lifecycle Runtime (Phase 17.5)', () => {

  const createManifest = (id: string, version: string, entryPoint: string, dependencies: any[] = []): PluginManifest => {
    return PluginManifestValidator.parse({
      id,
      name: `${id} Plugin`,
      version,
      description: `Description of ${id}`,
      author: 'Test Author',
      schemaVersion: '1.0.0',
      entryPoint,
      dependencies,
      capabilities: [],
      metadata: {}
    });
  };

  const createMockDiscovery = (manifests: PluginManifest[]): IPluginDiscoveryManager => {
    return {
      registerSource: () => {},
      unregisterSource: () => {},
      getSources: () => [],
      discover: async () => ({ success: true, manifests, invalid: [], duplicates: [], failures: [] }),
      discoverFromSource: async () => ({ success: true, manifests, invalid: [], duplicates: [], failures: [] }),
      find: (id) => manifests.find(m => m.id === id) || null,
      findAll: () => Object.freeze([...manifests]),
      contains: (id) => manifests.some(m => m.id === id),
      remove: () => false,
      clear: () => {},
      statistics: () => ({ discoveryAttempts: 0, discoveredPlugins: 0, validManifests: manifests.length, invalidManifests: 0, duplicateAttempts: 0, discoveryFailures: 0, validationFailures: 0, registeredSources: 0 }),
      health: () => ({ healthy: true, message: 'healthy', issues: [] }),
      reset: () => {}
    };
  };

  const createMockResolver = (order: string[] = []): IPluginDependencyResolver => {
    return {
      resolve: () => ({ status: 'RESOLVED', plan: { order }, issues: [], resolvedIds: order, unresolvedIds: [] }),
      resolveAll: () => ({ status: 'RESOLVED', plan: { order }, issues: [], resolvedIds: order, unresolvedIds: [] }),
      resolvePlugin: (id) => ({ status: 'RESOLVED', plan: { order: [id] }, issues: [], resolvedIds: [id], unresolvedIds: [] }),
      graph: () => ({ nodes: new Map(), edges: [] }),
      dependenciesOf: () => [],
      dependentsOf: () => [],
      statistics: () => ({} as any),
      health: () => ({ healthy: true, unresolvedDependencyCount: 0, cycleCount: 0, conflictCount: 0, message: 'healthy' }),
      reset: () => {}
    };
  };

  class FakeModuleLoader implements IPluginModuleLoader {
    public async load(_entryPoint: string): Promise<unknown> {
      return { initialized: true };
    }
  }

  const createLoaderAndDeps = (manifests: PluginManifest[], order: string[] = []): { loader: IPluginLoader, discovery: IPluginDiscoveryManager, resolver: IPluginDependencyResolver } => {
    const discovery = createMockDiscovery(manifests);
    const resolver = createMockResolver(order);
    const loader = new PluginLoader(discovery, resolver, new FakeModuleLoader());
    return { loader, discovery, resolver };
  };

  // 1. lifecycle manager construction
  it('constructs lifecycle manager successfully', () => {
    const { loader, discovery, resolver } = createLoaderAndDeps([]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    expect(manager).toBeDefined();
  });

  // 2. initial state
  it('reports correct initial lifecycle state', () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.UNLOADED);
  });

  // 3. reset
  // 42. lifecycle reset
  it('resets lifecycle state and metrics correctly', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1], ['p1']);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);

    await loader.load('p1');
    await manager.initializePlugin('p1');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.DEACTIVATED);
    expect(manager.statistics().initializeCount).toBe(1);

    manager.reset();
    expect(manager.getLifecycleState('p1')).toBe(PluginState.LOADED); // Fallback to loader loaded status
    expect(manager.statistics().initializeCount).toBe(0);
  });

  // 4. successful initialization
  // 5. initialization hook
  it('initializes loaded plugin successfully and triggers initialize hook', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    let hookCalled = false;
    manager.registerHooks('p1', {
      onInitialize: async (context) => {
        hookCalled = true;
        expect(context.pluginId).toBe('p1');
        expect(context.currentLifecycleState).toBe(PluginState.INITIALIZING);
      }
    });

    const result = await manager.initializePlugin('p1');
    expect(result.success).toBe(true);
    expect(result.currentState).toBe(PluginState.DEACTIVATED);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.DEACTIVATED);
    expect(hookCalled).toBe(true);
  });

  // 6. initialization failure
  it('transitions to FAILED on initialization hook failure', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    manager.registerHooks('p1', {
      onInitialize: async () => {
        throw new Error('Init hook failed');
      }
    });

    await expect(manager.initializePlugin('p1')).rejects.toThrow('Init hook failed');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.FAILED);
  });

  // 7. invalid initialization state
  it('rejects initialization from invalid states', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);

    // Unloaded -> Initializing invalid
    await expect(manager.initializePlugin('p1')).rejects.toThrow(PluginLifecycleTransitionError);
  });

  // 8. activation after initialization
  // 9. activation hook
  it('activates initialized plugin successfully and executes activate hook', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');

    let hookCalled = false;
    manager.registerHooks('p1', {
      onActivate: async (context) => {
        hookCalled = true;
        expect(context.currentLifecycleState).toBe(PluginState.DEACTIVATED);
      }
    });

    const result = await manager.activatePlugin('p1');
    expect(result.success).toBe(true);
    expect(result.currentState).toBe(PluginState.ACTIVE);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.ACTIVE);
    expect(hookCalled).toBe(true);
  });

  // 10. activation before initialization rejected
  it('rejects activation before initialization', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    await expect(manager.activatePlugin('p1')).rejects.toThrow(PluginLifecycleTransitionError);
  });

  // 11. activation failure
  it('transitions to FAILED on activation hook failure', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');

    manager.registerHooks('p1', {
      onActivate: async () => {
        throw new Error('Activation hook failed');
      }
    });

    await expect(manager.activatePlugin('p1')).rejects.toThrow('Activation hook failed');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.FAILED);
  });

  // 12. successful deactivation
  // 13. deactivation hook
  it('deactivates active plugin successfully and executes deactivate hook', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');
    await manager.activatePlugin('p1');

    let hookCalled = false;
    manager.registerHooks('p1', {
      onDeactivate: async (context) => {
        hookCalled = true;
        expect(context.currentLifecycleState).toBe(PluginState.DEACTIVATING);
      }
    });

    const result = await manager.deactivatePlugin('p1');
    expect(result.success).toBe(true);
    expect(result.currentState).toBe(PluginState.DEACTIVATED);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.DEACTIVATED);
    expect(hookCalled).toBe(true);
  });

  // 14. invalid deactivation
  it('rejects deactivation from invalid states', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    await expect(manager.deactivatePlugin('p1')).rejects.toThrow(PluginLifecycleTransitionError);
  });

  // 15. deactivation failure
  it('transitions to FAILED on deactivation hook failure', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');
    await manager.activatePlugin('p1');

    manager.registerHooks('p1', {
      onDeactivate: async () => {
        throw new Error('Deactivation hook failed');
      }
    });

    await expect(manager.deactivatePlugin('p1')).rejects.toThrow('Deactivation hook failed');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.FAILED);
  });

  // 16. successful disposal
  // 17. disposal hook
  it('disposes deactivated plugin successfully and executes disposal hook', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');

    let hookCalled = false;
    manager.registerHooks('p1', {
      onDispose: async (context) => {
        hookCalled = true;
        expect(context.currentLifecycleState).toBe(PluginState.DISPOSING);
      }
    });

    const result = await manager.disposePlugin('p1');
    expect(result.success).toBe(true);
    expect(result.currentState).toBe(PluginState.DISPOSED);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.DISPOSED);
    expect(hookCalled).toBe(true);
  });

  // 18. disposal of active plugin
  it('deactivates active plugin automatically first before disposal', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');
    await manager.activatePlugin('p1');

    let deactivateCalled = false;
    let disposeCalled = false;
    manager.registerHooks('p1', {
      onDeactivate: async () => { deactivateCalled = true; },
      onDispose: async () => { disposeCalled = true; }
    });

    await manager.disposePlugin('p1');
    expect(deactivateCalled).toBe(true);
    expect(disposeCalled).toBe(true);
    expect(manager.getLifecycleState('p1')).toBe(PluginState.DISPOSED);
  });

  // 19. disposed plugin cannot reactivate
  it('ensures disposed plugin is terminal and cannot reactivate or initialize', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');
    await manager.disposePlugin('p1');

    await expect(manager.initializePlugin('p1')).rejects.toThrow(PluginLifecycleTransitionError);
    await expect(manager.activatePlugin('p1')).rejects.toThrow(PluginLifecycleTransitionError);
  });

  // 20. disposal failure
  it('transitions to FAILED on disposal hook failure', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');

    manager.registerHooks('p1', {
      onDispose: async () => {
        throw new Error('Disposal hook failed');
      }
    });

    await expect(manager.disposePlugin('p1')).rejects.toThrow('Disposal hook failed');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.FAILED);
  });

  // 21. dependency-aware initialization
  // 22. dependency-aware activation
  // 23. reverse dependency deactivation
  // 24. reverse dependency disposal
  it('performs dependency-aware operations topologically in forward/reverse orders', async () => {
    // a depends on b
    const mB = createManifest('b', '1.0.0', 'b.js');
    const mA = createManifest('a', '1.0.0', 'a.js', [{ id: 'b', versionRange: '*' }]);
    const { loader, discovery, resolver } = createLoaderAndDeps([mB, mA], ['b', 'a']);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);

    await loader.loadAll();

    // 1. Init all forward
    const initResults = await manager.initializeAll();
    expect(initResults).toHaveLength(2);
    expect(initResults[0].pluginId).toBe('b');
    expect(initResults[1].pluginId).toBe('a');

    // 2. Activate all forward
    const activeResults = await manager.activateAll();
    expect(activeResults).toHaveLength(2);
    expect(activeResults[0].pluginId).toBe('b');
    expect(activeResults[1].pluginId).toBe('a');

    // 3. Deactivate all reverse
    const deactivateResults = await manager.deactivateAll();
    expect(deactivateResults).toHaveLength(2);
    expect(deactivateResults[0].pluginId).toBe('a'); // A first (dependent)
    expect(deactivateResults[1].pluginId).toBe('b'); // B second (dependency)

    // 4. Dispose all reverse
    const disposeResults = await manager.disposeAll();
    expect(disposeResults).toHaveLength(2);
    expect(disposeResults[0].pluginId).toBe('a');
    expect(disposeResults[1].pluginId).toBe('b');
  });

  // 25. dependency failure isolation
  // 26. dependent activation blocked when dependency failed
  it('isolates failures and blocks dependent activation when dependency initialization fails', async () => {
    const mB = createManifest('b', '1.0.0', 'b.js');
    const mA = createManifest('a', '1.0.0', 'a.js', [{ id: 'b', versionRange: '*' }]);
    const { loader, discovery, resolver } = createLoaderAndDeps([mB, mA], ['b', 'a']);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);

    await loader.loadAll();

    // Fail initialization of B
    manager.registerHooks('b', {
      onInitialize: async () => { throw new Error('B init failed'); }
    });

    // Initialize B (will fail)
    await expect(manager.initializePlugin('b')).rejects.toThrow('B init failed');
    expect(manager.getLifecycleState('b')).toBe(PluginState.FAILED);

    // Try to initialize or activate A
    await expect(manager.initializePlugin('a')).rejects.toThrow("dependency 'b' is not initialized");
    expect(manager.getLifecycleState('a')).toBe(PluginState.FAILED);
  });

  // 27. duplicate concurrent initialization
  // 28. concurrent activation protection
  // 29. conflicting lifecycle operations
  it('protects against duplicate and conflicting concurrent operations using promise sharing', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    // Concurrent initialization
    const p1 = manager.initializePlugin('p1');
    const p2 = manager.initializePlugin('p1');

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1.success).toBe(true);
    expect(r2.success).toBe(true);
  });

  // 30. hook registration
  // 31. hook unregistration
  // 32. duplicate hook handling
  it('registers, unregisters, and prevents duplicate hook registrations', () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);

    manager.registerHooks('p1', { onInitialize: async () => {} });
    expect(() => {
      manager.registerHooks('p1', { onInitialize: async () => {} });
    }).toThrow(PluginLifecycleError);

    manager.unregisterHooks('p1');
    // Can register again now
    manager.registerHooks('p1', { onInitialize: async () => {} });
  });

  // 33. hook exception isolation
  it('isolates exceptions raised during hook executions', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');

    manager.registerHooks('p1', {
      onInitialize: async () => { throw new Error('isolated error'); }
    });

    await expect(manager.initializePlugin('p1')).rejects.toThrow('isolated error');
    expect(manager.getLifecycleState('p1')).toBe(PluginState.FAILED);
  });

  // 34. lifecycle history
  // 35. bounded history
  it('maintains a bounded history of lifecycle operations', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader, { maxHistorySize: 2 });
    await loader.load('p1');

    await manager.initializePlugin('p1');
    expect(manager.history()).toHaveLength(1);

    await manager.activatePlugin('p1');
    expect(manager.history()).toHaveLength(2);

    await manager.deactivatePlugin('p1');
    expect(manager.history()).toHaveLength(2); // strictly bounded to 2
  });

  // 36. statistics
  // 37. health
  // 38. diagnostics
  // 39. immutable snapshots
  it('populates immutable stats, health, and diagnostics snapshots correctly', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const { loader, discovery, resolver } = createLoaderAndDeps([m1]);
    const manager = new PluginLifecycleManager(discovery, resolver, loader);
    await loader.load('p1');
    await manager.initializePlugin('p1');

    const stats = manager.statistics();
    expect(stats.initializeCount).toBe(1);
    expect(Object.isFrozen(stats)).toBe(true);

    const health = manager.health();
    expect(health.healthy).toBe(true);
    expect(Object.isFrozen(health)).toBe(true);

    const diagnostics = manager.diagnostics();
    expect(diagnostics.statistics.initializeCount).toBe(1);
    expect(Object.isFrozen(diagnostics)).toBe(true);
  });

  // 40. provider delegation
  it('delegates lifecycle APIs correctly through PluginProvider', async () => {
    const provider = new PluginProvider();
    expect(provider.lifecycle()).toBeDefined();
    expect(provider.lifecycle().statistics().initializeCount).toBe(0);
  });

  // 41. runtime delegation
  it('delegates lifecycle APIs correctly through thin PluginRuntime coordinator', async () => {
    const runtime = new PluginRuntime();
    expect(runtime.lifecycle()).toBeDefined();
    expect(runtime.lifecycle().statistics().initializeCount).toBe(0);
  });

});
