import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  InMemoryDiscoverySource,
  PluginDependencyGraphBuilder,
  PluginDependencyResolver,
  DependencyResolutionStatus,
  DependencyResolutionIssueCode,
  type PluginManifest,
  type IPluginDiscoveryManager,
  type IPluginProvider
} from '../../src/plugins';

describe('Plugin Dependency Resolution Runtime (Phase 17.3)', () => {

  const createManifest = (id: string, version: string, dependencies: any[] = []): PluginManifest => {
    return PluginManifestValidator.parse({
      id,
      name: `${id} Plugin`,
      version,
      description: `Description of ${id}`,
      author: 'Test Author',
      schemaVersion: '1.0.0',
      entryPoint: `src/${id}.js`,
      dependencies,
      capabilities: [],
      metadata: {}
    });
  };

  // Helper mock Discovery Manager
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

  // 1. Dependency model creation
  it('creates dependency models cleanly', () => {
    const manifest = createManifest('plugin-a', '1.0.0', [
      { id: 'plugin-b', versionRange: '^2.0.0', optional: true }
    ]);
    expect(manifest.dependencies).toHaveLength(1);
    expect(manifest.dependencies[0].id).toBe('plugin-b');
    expect(manifest.dependencies[0].versionRange).toBe('^2.0.0');
    expect(manifest.dependencies[0].optional).toBe(true);
  });

  // 2. Dependency model immutability
  it('enforces immutability on dependency models', () => {
    const manifest = createManifest('plugin-a', '1.0.0', [
      { id: 'plugin-b', versionRange: '^2.0.0', optional: true }
    ]);
    expect(Object.isFrozen(manifest.dependencies)).toBe(true);
    expect(Object.isFrozen(manifest.dependencies[0])).toBe(true);
    expect(() => {
      (manifest.dependencies as any)[0] = {};
    }).toThrow(TypeError);
  });

  // 3. Graph construction
  it('builds a deterministic graph structure from manifests', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0' }]);
    const m2 = createManifest('b', '1.2.0');
    const graph = PluginDependencyGraphBuilder.build([m1, m2]);

    expect(graph.nodes.size).toBe(2);
    expect(graph.edges).toHaveLength(1);
    expect(graph.edges[0].from).toBe('a');
    expect(graph.edges[0].to).toBe('b');
    expect(graph.edges[0].required).toBe(true);
    expect(graph.edges[0].versionRange).toBe('^1.0.0');
    expect(Object.isFrozen(graph)).toBe(true);
  });

  // 4. Single dependency
  it('resolves a single dependency relation', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0' }]);
    const m2 = createManifest('b', '1.2.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['b', 'a']);
    expect(result.issues).toHaveLength(0);
  });

  // 5. Multiple dependencies
  it('resolves multiple direct dependencies', () => {
    const m1 = createManifest('a', '1.0.0', [
      { id: 'b', versionRange: '^1.0.0' },
      { id: 'c', versionRange: '^2.0.0' }
    ]);
    const m2 = createManifest('b', '1.2.0');
    const m3 = createManifest('c', '2.0.5');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    // alphabetical tie-breaking on independent roots / leaves
    expect(result.plan?.order).toEqual(['b', 'c', 'a']);
  });

  // 6. Branching dependency graph
  it('resolves branching dependency trees', () => {
    // a -> b -> d
    // a -> c -> d
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }, { id: 'c', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'd', versionRange: '*' }]);
    const m3 = createManifest('c', '1.0.0', [{ id: 'd', versionRange: '*' }]);
    const m4 = createManifest('d', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3, m4]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['d', 'b', 'c', 'a']);
  });

  // 7. Deep dependency graph
  it('resolves deep chains of dependencies', () => {
    // a -> b -> c -> d -> e
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'c', versionRange: '*' }]);
    const m3 = createManifest('c', '1.0.0', [{ id: 'd', versionRange: '*' }]);
    const m4 = createManifest('d', '1.0.0', [{ id: 'e', versionRange: '*' }]);
    const m5 = createManifest('e', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3, m4, m5]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['e', 'd', 'c', 'b', 'a']);
  });

  // 8. Independent plugins
  it('resolves independent plugins deterministically', () => {
    const m1 = createManifest('z', '1.0.0');
    const m2 = createManifest('m', '1.0.0');
    const m3 = createManifest('a', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['a', 'm', 'z']);
  });

  // 9. Required dependency success
  it('successfully satisfies required dependencies', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0', optional: false }]);
    const m2 = createManifest('b', '1.1.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.resolvedIds).toContain('a');
    expect(result.resolvedIds).toContain('b');
  });

  // 10. Missing required dependency
  it('fails resolution on missing required dependencies', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0', optional: false }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    expect(result.plan).toBeNull();
    expect(result.issues).toHaveLength(1);
    expect(result.issues[0].code).toBe(DependencyResolutionIssueCode.MISSING_DEPENDENCY);
    expect(result.issues[0].severity).toBe('error');
    expect(result.unresolvedIds).toContain('a');
  });

  // 11. Missing optional dependency
  it('proceeds with resolution but warns on missing optional dependencies', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0', optional: true }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['a']);
    expect(result.issues).toHaveLength(1);
    expect(result.issues[0].code).toBe(DependencyResolutionIssueCode.MISSING_DEPENDENCY);
    expect(result.issues[0].severity).toBe('warning');
  });

  // 12. Compatible version
  it('satisfies constraints with compatible versions', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '~1.2.0' }]);
    const m2 = createManifest('b', '1.2.5');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.issues).toHaveLength(0);
  });

  // 13. Incompatible required version
  it('fails resolution when required dependency version is incompatible', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^2.0.0', optional: false }]);
    const m2 = createManifest('b', '1.9.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    expect(result.plan).toBeNull();
    expect(result.issues).toHaveLength(1);
    expect(result.issues[0].code).toBe(DependencyResolutionIssueCode.VERSION_CONFLICT);
    expect(result.issues[0].severity).toBe('error');
  });

  // 14. Incompatible optional version
  it('proceeds with resolution but warns when optional dependency version is incompatible', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^2.0.0', optional: true }]);
    const m2 = createManifest('b', '1.9.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    // Since B is present (but incompatible), it participates in graph ordering!
    expect(result.plan?.order).toEqual(['b', 'a']);
    expect(result.issues).toHaveLength(1);
    expect(result.issues[0].code).toBe(DependencyResolutionIssueCode.VERSION_CONFLICT);
    expect(result.issues[0].severity).toBe('warning');
  });

  // 15. Multiple version constraints
  it('handles multiple AND version constraints', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '>=1.0.0 <2.0.0' }]);
    const m2 = createManifest('b', '1.5.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    let result = resolver.resolveAll();
    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);

    // Incompatible check
    const m3 = createManifest('b2', '2.0.0');
    const resolver2 = new PluginDependencyResolver(createMockDiscovery([m1, m3]));
    result = resolver2.resolveAll();
    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
  });

  // 16. Version conflict detection
  it('detects version conflicts in independent branches on same target', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '^1.0.0' }]);
    const m2 = createManifest('c', '1.0.0', [{ id: 'b', versionRange: '^2.0.0' }]);
    const m3 = createManifest('b', '1.5.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    expect(result.issues.some(i => i.code === DependencyResolutionIssueCode.VERSION_CONFLICT)).toBe(true);
  });

  // 17. Two-node circular dependency
  it('detects cycle between two nodes', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'a', versionRange: '*' }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    expect(result.issues.some(i => i.code === DependencyResolutionIssueCode.CIRCULAR_DEPENDENCY)).toBe(true);
  });

  // 18. Three-node circular dependency
  it('detects cycle between three nodes', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'c', versionRange: '*' }]);
    const m3 = createManifest('c', '1.0.0', [{ id: 'a', versionRange: '*' }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    const circularIssue = result.issues.find(i => i.code === DependencyResolutionIssueCode.CIRCULAR_DEPENDENCY);
    expect(circularIssue).toBeDefined();
    expect(circularIssue?.path).toBeDefined();
  });

  // 19. Longer circular dependency
  it('detects cycle along a five-node chain', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'c', versionRange: '*' }]);
    const m3 = createManifest('c', '1.0.0', [{ id: 'd', versionRange: '*' }]);
    const m4 = createManifest('d', '1.0.0', [{ id: 'e', versionRange: '*' }]);
    const m5 = createManifest('e', '1.0.0', [{ id: 'a', versionRange: '*' }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3, m4, m5]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
  });

  // 20. Topological ordering
  it('produces valid topological ordering', () => {
    const m1 = createManifest('x', '1.0.0', [{ id: 'y', versionRange: '*' }]);
    const m2 = createManifest('y', '1.0.0', [{ id: 'z', versionRange: '*' }]);
    const m3 = createManifest('z', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    const order = result.plan!.order;
    expect(order.indexOf('z')).toBeLessThan(order.indexOf('y'));
    expect(order.indexOf('y')).toBeLessThan(order.indexOf('x'));
  });

  // 21. Deterministic ordering
  // 22. Independent-node tie breaking
  it('breaks ties deterministically on independent nodes', () => {
    const m1 = createManifest('c', '1.0.0');
    const m2 = createManifest('b', '1.0.0');
    const m3 = createManifest('a', '1.0.0');

    // Alphabetical order: a, b, c
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const r1 = resolver.resolveAll();
    const r2 = resolver.resolveAll();

    expect(r1.plan?.order).toEqual(['a', 'b', 'c']);
    expect(r2.plan?.order).toEqual(['a', 'b', 'c']);
  });

  // 23. Partial resolution
  it('correctly reports resolved and unresolved plugin partitions', () => {
    // a depends on bad required dependency b
    // c is healthy and independent
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('c', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.FAILED);
    expect(result.unresolvedIds).toEqual(['a']); // a is unresolved because b is missing
    expect(result.resolvedIds).toEqual(['c']);   // c resolved successfully
  });

  // 24. Empty plugin set
  it('handles empty manifest lists safely', () => {
    const resolver = new PluginDependencyResolver(createMockDiscovery([]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toHaveLength(0);
  });

  // 25. Single plugin with no dependencies
  it('resolves a single plugin with no dependencies', () => {
    const m1 = createManifest('a', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['a']);
  });

  // 26. Multiple roots
  it('resolves multiple root nodes correctly', () => {
    // a -> c
    // b -> c
    const m1 = createManifest('a', '1.0.0', [{ id: 'c', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0', [{ id: 'c', versionRange: '*' }]);
    const m3 = createManifest('c', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2, m3]));
    const result = resolver.resolveAll();

    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
    expect(result.plan?.order).toEqual(['c', 'a', 'b']);
  });

  // 27. Dependency lookup
  // 28. Dependent lookup
  it('performs direct dependency and dependent lookups', async () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const m2 = createManifest('b', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1, m2]));
    
    // Resolve first to populate currentGraph
    resolver.resolveAll();

    expect(resolver.dependenciesOf('a')).toEqual(['b']);
    expect(resolver.dependentsOf('b')).toEqual(['a']);
    expect(resolver.dependenciesOf('b')).toEqual([]);
    expect(resolver.dependentsOf('a')).toEqual([]);
  });

  // 29. Resolution statistics
  it('tracks statistics correctly', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    resolver.resolveAll();

    const stats = resolver.statistics();
    expect(stats.resolutionAttempts).toBe(1);
    expect(stats.missingDependencies).toBe(1);
    expect(stats.resolutionFailures).toBe(1);
  });

  // 30. Health reporting
  it('reports health snapshots correctly', () => {
    const m1 = createManifest('a', '1.0.0', [{ id: 'b', versionRange: '*' }]);
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    resolver.resolveAll();

    const health = resolver.health();
    expect(health.healthy).toBe(false);
    expect(health.unresolvedDependencyCount).toBe(1);
  });

  // 31. Provider delegation
  it('delegates dependency resolver through PluginProvider', () => {
    const provider = new PluginProvider();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [
        {
          id: 'a',
          name: 'A',
          version: '1.0.0',
          schemaVersion: '1.0.0',
          entryPoint: 'a.js',
          dependencies: []
        }
      ]
    );
    provider.discovery().registerSource(source);
    
    // Fake discover to populate
    provider.discovery().discover();

    const result = provider.resolver().resolveAll();
    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
  });

  // 32. Runtime delegation
  it('delegates dependency resolver through PluginRuntime', () => {
    const runtime = new PluginRuntime();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [
        {
          id: 'a',
          name: 'A',
          version: '1.0.0',
          schemaVersion: '1.0.0',
          entryPoint: 'a.js',
          dependencies: []
        }
      ]
    );
    runtime.discovery().registerSource(source);
    runtime.discovery().discover();

    const result = runtime.resolver().resolveAll();
    expect(result.status).toBe(DependencyResolutionStatus.RESOLVED);
  });

  // 33. Dependency injection/custom resolver
  it('supports dependency injection of custom resolver', () => {
    const customProvider: IPluginProvider = {
      initialize: () => ({ state: 'READY', healthy: true, message: 'Custom' }),
      shutdown: () => ({ state: 'STOPPED', healthy: true, message: 'Custom' }),
      state: () => 'READY',
      status: () => ({ state: 'READY', healthy: true, message: 'Custom' }),
      statistics: () => ({ registeredPlugins: 0, enabledPlugins: 0, disabledPlugins: 0, initializationCount: 0, shutdownCount: 0, errors: 0, uptime: 0 }),
      health: () => ({ healthy: true, state: 'READY', registeredPluginCount: 0, enabledPluginCount: 0, errorCount: 0, message: 'Custom' }),
      registerPlugin: () => { throw new Error('Not implemented'); },
      unregisterPlugin: () => { throw new Error('Not implemented'); },
      hasPlugin: () => false,
      getPlugin: () => null,
      listPlugins: () => [],
      diagnostics: () => ({} as any),
      discovery: () => ({} as any),
      resolver: () => {
        return {
          resolve: () => ({ status: DependencyResolutionStatus.RESOLVED, plan: { order: ['injected'] }, issues: [], resolvedIds: ['injected'], unresolvedIds: [] }),
          resolveAll: () => ({ status: DependencyResolutionStatus.RESOLVED, plan: { order: ['injected'] }, issues: [], resolvedIds: ['injected'], unresolvedIds: [] }),
          resolvePlugin: () => ({ status: DependencyResolutionStatus.RESOLVED, plan: { order: ['injected'] }, issues: [], resolvedIds: ['injected'], unresolvedIds: [] }),
          graph: () => ({ nodes: new Map(), edges: [] }),
          dependenciesOf: () => [],
          dependentsOf: () => [],
          statistics: () => ({} as any),
          health: () => ({ healthy: true, unresolvedDependencyCount: 0, cycleCount: 0, conflictCount: 0, message: 'injected' }),
          reset: () => {}
        };
      },
      loader: () => ({} as any),
      lifecycle: () => ({} as any),
      capabilities: () => ({} as any),
      extensions: () => ({} as any),
      security: () => ({} as any),
      policies: () => ({} as any),
      sandbox: () => ({} as any),
      configuration: () => ({} as any)
    };

    const runtime = new PluginRuntime(customProvider);
    expect(runtime.resolver().resolveAll().plan?.order).toEqual(['injected']);
  });

  // 34. Reset/lifecycle behavior
  it('resets resolver statistics and current graph correctly', () => {
    const m1 = createManifest('a', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    resolver.resolveAll();

    expect(resolver.statistics().resolutionAttempts).toBe(1);
    expect(resolver.graph().nodes.size).toBe(1);

    resolver.reset();
    expect(resolver.statistics().resolutionAttempts).toBe(0);
    expect(resolver.graph().nodes.size).toBe(0);
  });

  // 35. Immutable returned snapshots
  it('returns deeply frozen resolution results and snapshots', () => {
    const m1 = createManifest('a', '1.0.0');
    const resolver = new PluginDependencyResolver(createMockDiscovery([m1]));
    const result = resolver.resolveAll();

    expect(Object.isFrozen(result)).toBe(true);
    expect(Object.isFrozen(result.resolvedIds)).toBe(true);
    expect(Object.isFrozen(result.issues)).toBe(true);
    expect(() => {
      (result as any).status = 'CHANGED';
    }).toThrow(TypeError);
  });

  // 36. Regression tests for Phase 17.1
  it('does not break Phase 17.1 foundations', () => {
    const provider = new PluginProvider();
    const result = provider.initialize();
    expect(result.healthy).toBe(true);
    expect(provider.state()).toBe('READY');
  });

  // 37. Regression tests for Phase 17.2
  it('does not break Phase 17.2 manifest validation and discovery behavior', () => {
    const manifest = PluginManifestValidator.parse({
      id: 'p-17-2',
      name: 'P 17.2',
      version: '1.2.3-alpha+build.1',
      schemaVersion: '1.0.0',
      entryPoint: 'index.js',
      author: 'Tester',
      dependencies: []
    });
    expect(manifest.id).toBe('p-17-2');
    expect(manifest.version).toBe('1.2.3-alpha+build.1');
  });

});
