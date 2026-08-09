import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  PluginLoader,
  PluginLoadStatus,
  PluginStateError,
  type PluginManifest,
  type IPluginDiscoveryManager,
  type IPluginDependencyResolver,
  type IPluginModuleLoader
} from '../../src/plugins';

describe('Plugin Loading Runtime (Phase 17.4)', () => {

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

  // Mock Module Loader
  class FakeModuleLoader implements IPluginModuleLoader {
    public readonly loadedPaths: string[] = [];
    public failForPath: string | null = null;
    public returnedModule: unknown = { name: 'mock-module' };

    public async load(entryPoint: string): Promise<unknown> {
      this.loadedPaths.push(entryPoint);
      if (this.failForPath === entryPoint) {
        throw new Error(`Failed to load ${entryPoint}`);
      }
      return this.returnedModule;
    }
  }

  // A. Model immutability
  it('enforces immutability on returned loader models and diagnostics', async () => {
    const manifest = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([manifest]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    const result = await loader.load('p1');
    expect(Object.isFrozen(result)).toBe(true);
    expect(Object.isFrozen(result.warnings)).toBe(true);
    expect(() => {
      (result as any).success = false;
    }).toThrow(TypeError);

    const stats = loader.statistics();
    expect(Object.isFrozen(stats)).toBe(true);

    const health = loader.health();
    expect(Object.isFrozen(health)).toBe(true);

    const diag = loader.diagnostics();
    expect(Object.isFrozen(diag)).toBe(true);
  });

  // B. Module loader abstraction
  it('correctly uses the module loader abstraction to load and handle loader errors', async () => {
    const manifest = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([manifest]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    moduleLoader.failForPath = 'p1.js';
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    const result = await loader.load('p1');
    expect(result.success).toBe(false);
    expect(result.status).toBe(PluginLoadStatus.FAILED);
    expect(result.error?.message).toContain('Failed to load p1.js');
  });

  // C. Single plugin loading
  it('resolves valid loads, and rejects missing plugins or malformed modules', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([m1]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    // 1. Missing plugin
    const rMissing = await loader.load('missing');
    expect(rMissing.success).toBe(false);
    expect(rMissing.error?.message).toContain("not found in discovery scanner");

    // 2. Malformed module (primitive returned instead of object)
    moduleLoader.returnedModule = 'primitive-string';
    const rMalformed = await loader.load('p1');
    expect(rMalformed.success).toBe(false);
    expect(rMalformed.error?.message).toContain("did not return a valid module object");

    // 3. Valid load
    moduleLoader.returnedModule = { initialized: true };
    const rValid = await loader.load('p1');
    expect(rValid.success).toBe(true);
    expect(rValid.status).toBe(PluginLoadStatus.LOADED);
    expect(loader.isLoaded('p1')).toBe(true);
  });

  // D. Duplicate loading
  it('prevents duplicate loading and increments telemetry attempts', async () => {
    const manifest = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([manifest]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    const r1 = await loader.load('p1');
    expect(r1.success).toBe(true);
    expect(moduleLoader.loadedPaths).toHaveLength(1);

    const r2 = await loader.load('p1');
    expect(r2.success).toBe(false); // Duplicate load rejected
    expect(r2.status).toBe(PluginLoadStatus.LOADED); // but indicates it is loaded
    expect(moduleLoader.loadedPaths).toHaveLength(1); // underlying loader not called again
    expect(loader.statistics().duplicateLoadAttempts).toBe(1);
  });

  // E. Concurrent loading
  it('handles concurrent load requests by sharing in-flight loading promise', async () => {
    const manifest = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([manifest]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    // Trigger load concurrent requests
    const p1 = loader.load('p1');
    const p2 = loader.load('p1');

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1.success).toBe(true);
    expect(r2.success).toBe(true); // Share in-flight success
    expect(moduleLoader.loadedPaths).toHaveLength(1); // underlying load only called once
  });

  // F. Failure isolation
  it('isolates failures so one failing plugin does not block unrelated plugins', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const m2 = createManifest('p2', '1.0.0', 'p2.js');
    const discovery = createMockDiscovery([m1, m2]);
    const resolver = createMockResolver(['p1', 'p2']);
    const moduleLoader = new FakeModuleLoader();
    moduleLoader.failForPath = 'p1.js';
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    const r1 = await loader.load('p1'); // fails
    const r2 = await loader.load('p2'); // succeeds

    expect(r1.success).toBe(false);
    expect(r2.success).toBe(true);
    expect(loader.isLoaded('p1')).toBe(false);
    expect(loader.isLoaded('p2')).toBe(true);
  });

  // G. Dependency-aware loadAll
  it('performs topological loadAll and propagates required dependency failures', async () => {
    // a depends on b
    const mB = createManifest('b', '1.0.0', 'b.js');
    const mA = createManifest('a', '1.0.0', 'a.js', [{ id: 'b', versionRange: '*' }]);
    const discovery = createMockDiscovery([mB, mA]);
    const resolver = createMockResolver(['b', 'a']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    // 1. Success topological loadAll
    const results = await loader.loadAll();
    expect(results).toHaveLength(2);
    expect(results[0].pluginId).toBe('b'); // B loaded first
    expect(results[0].success).toBe(true);
    expect(results[1].pluginId).toBe('a'); // A loaded second
    expect(results[1].success).toBe(true);

    // Reset and fail the dependency
    loader.reset();
    moduleLoader.loadedPaths.length = 0;
    moduleLoader.failForPath = 'b.js';

    const failResults = await loader.loadAll();
    expect(failResults[0].pluginId).toBe('b');
    expect(failResults[0].success).toBe(false); // B fails
    expect(failResults[1].pluginId).toBe('a');
    expect(failResults[1].success).toBe(false); // A fails because B failed
    expect(failResults[1].error?.message).toContain("required dependency 'b' is not loaded");
  });

  // H. Unload
  it('handles unloading of loaded plugins, state transitions, and throws on missing', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([m1]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    // Try to unload not loaded plugin
    expect(() => {
      loader.unload('p1');
    }).toThrow(PluginStateError);

    // Load first
    await loader.load('p1');

    const result = loader.unload('p1');
    expect(result.success).toBe(true);
    expect(result.status).toBe(PluginLoadStatus.UNLOADED);
    expect(loader.isLoaded('p1')).toBe(false);
    expect(loader.statistics().successfulUnloads).toBe(1);
  });

  // I. History
  it('records bounded load history', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([m1]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader, { maxHistorySize: 2 });

    await loader.load('p1');
    expect(loader.loadHistory()).toHaveLength(1);

    await loader.unload('p1');
    expect(loader.loadHistory()).toHaveLength(2);

    // Evict oldest on next attempt
    await loader.load('p1');
    expect(loader.loadHistory()).toHaveLength(2); // strictly capped to 2
    expect(loader.loadHistory()[1].status).toBe(PluginLoadStatus.LOADED);

    loader.clearLoadHistory();
    expect(loader.loadHistory()).toHaveLength(0);
  });

  // J. Statistics
  // K. Health
  it('correctly populates stats, health, and diagnostics', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([m1]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    await loader.load('p1');
    const stats = loader.statistics();
    expect(stats.loadAttempts).toBe(1);
    expect(stats.successfulLoads).toBe(1);

    const health = loader.health();
    expect(health.healthy).toBe(true);
    expect(health.loadedPlugins).toBe(1);

    const diag = loader.diagnostics();
    expect(diag.statistics.loadAttempts).toBe(1);
    expect(diag.loadedPluginIds).toEqual(['p1']);
  });

  // L. Provider delegation
  it('registers and delegates through PluginProvider', () => {
    const provider = new PluginProvider();
    expect(provider.loader()).toBeDefined();
    expect(provider.loader().statistics().loadAttempts).toBe(0);
  });

  // M. Runtime delegation
  it('registers and delegates through PluginRuntime thin coordinator', () => {
    const runtime = new PluginRuntime();
    expect(runtime.loader()).toBeDefined();
    expect(runtime.loader().statistics().loadAttempts).toBe(0);
  });

  // N. Reset
  it('resets state and metrics back to default clean values', async () => {
    const m1 = createManifest('p1', '1.0.0', 'p1.js');
    const discovery = createMockDiscovery([m1]);
    const resolver = createMockResolver(['p1']);
    const moduleLoader = new FakeModuleLoader();
    const loader = new PluginLoader(discovery, resolver, moduleLoader);

    await loader.load('p1');
    expect(loader.isLoaded('p1')).toBe(true);
    expect(loader.statistics().loadAttempts).toBe(1);

    loader.reset();
    expect(loader.isLoaded('p1')).toBe(false);
    expect(loader.statistics().loadAttempts).toBe(0);
  });

});
