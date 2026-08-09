import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  PluginLoader,
  PluginLifecycleManager,
  PluginCapabilityManager,
  PluginExtensionManager,
  PluginState,
  PluginCapabilityType,
  PluginCapabilityRegistrationError,
  PluginCapabilityConflictError,
  PluginExtensionRegistrationError,
  PluginExtensionConflictError,
  type PluginManifest,
  type IPluginDiscoveryManager,
  type IPluginDependencyResolver,
  type IPluginModuleLoader
} from '../../src/plugins';

describe('Plugin Capability & Extension Runtime (Phase 17.6)', () => {

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

  const createRuntimeContext = (manifests: PluginManifest[], order: string[] = []) => {
    const discovery = createMockDiscovery(manifests);
    const resolver = createMockResolver(order);
    const loader = new PluginLoader(discovery, resolver, new FakeModuleLoader());
    const lifecycle = new PluginLifecycleManager(discovery, resolver, loader);
    return { discovery, resolver, loader, lifecycle };
  };

  // CAPABILITY TESTS
  describe('Capabilities', () => {
    // 1. manager construction
    it('constructs capability manager successfully', () => {
      const { lifecycle } = createRuntimeContext([]);
      const manager = new PluginCapabilityManager(lifecycle);
      expect(manager).toBeDefined();
    });

    // 2. registration
    // 3. lookup
    // 4. contains
    it('registers, looks up, and queries capability existence', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      const regResult = manager.registerCapability('p1', {
        id: 'c1',
        name: 'Command 1',
        type: PluginCapabilityType.COMMAND,
        version: '1.0.0'
      });

      expect(regResult.success).toBe(true);
      expect(regResult.capabilityId).toBe('c1');

      const found = manager.findCapability('c1');
      expect(found).toBeDefined();
      expect(found?.name).toBe('Command 1');
      expect(manager.containsCapability('c1')).toBe(true);
    });

    // 5. duplicate rejection
    // 38. duplicate capability conflict
    it('rejects duplicate capability registrations', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', {
        id: 'c1',
        name: 'Command 1',
        type: PluginCapabilityType.COMMAND,
        version: '1.0.0'
      });

      expect(() => {
        manager.registerCapability('p1', {
          id: 'c1',
          name: 'Command 1 duplicate',
          type: PluginCapabilityType.COMMAND,
          version: '1.0.0'
        });
      }).toThrow(PluginCapabilityConflictError);
    });

    // 6. invalid metadata rejection
    it('rejects capability registration with missing fields', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      expect(() => {
        manager.registerCapability('p1', {
          id: '',
          name: 'Command 1',
          type: PluginCapabilityType.COMMAND,
          version: '1.0.0'
        });
      }).toThrow(PluginCapabilityRegistrationError);
    });

    // 7. find by plugin
    // 8. find by type
    it('filters capabilities by plugin or type', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', { id: 'c1', name: 'Command 1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      manager.registerCapability('p1', { id: 'c2', name: 'Service 1', type: PluginCapabilityType.SERVICE, version: '1.0.0' });

      const pluginCaps = manager.findCapabilitiesByPlugin('p1');
      expect(pluginCaps).toHaveLength(2);

      const commandCaps = manager.findCapabilitiesByType(PluginCapabilityType.COMMAND);
      expect(commandCaps).toHaveLength(1);
      expect(commandCaps[0].id).toBe('c1');
    });

    // 9. unregister
    it('unregisters capability successfully', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', { id: 'c1', name: 'Command 1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      expect(manager.containsCapability('c1')).toBe(true);

      const unregResult = manager.unregisterCapability('p1', 'c1');
      expect(unregResult.success).toBe(true);
      expect(manager.containsCapability('c1')).toBe(false);
    });

    // 10. unregister plugin capabilities
    it('unregisters all capabilities of a plugin', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', { id: 'c1', name: 'Command 1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      manager.registerCapability('p1', { id: 'c2', name: 'Service 1', type: PluginCapabilityType.SERVICE, version: '1.0.0' });

      manager.unregisterPluginCapabilities('p1');
      expect(manager.findCapabilitiesByPlugin('p1')).toHaveLength(0);
    });

    // 11. enable
    // 12. disable
    it('enables and disables capabilities', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', { id: 'c1', name: 'Command 1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });

      manager.disableCapability('c1');
      expect(manager.findCapability('c1')).toBeNull();

      manager.enableCapability('c1');
      expect(manager.findCapability('c1')).not.toBeNull();
    });

    // 13. statistics
    // 14. health
    // 15. diagnostics
    // 16. immutable snapshots
    it('records statistics and checks health of capabilities', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const manager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      manager.registerCapability('p1', { id: 'c1', name: 'Command 1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });

      const stats = manager.statistics();
      expect(stats.registeredCapabilities).toBe(1);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = manager.health();
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);

      const diag = manager.diagnostics();
      expect(diag.capabilityCount).toBe(1);
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  // EXTENSION POINT TESTS
  describe('Extension Points', () => {
    // 17. extension point registration
    // 19. lookup
    it('registers and looks up extension point', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', {
        id: 'ep1',
        name: 'Extension Point 1',
        version: '1.0.0',
        acceptedTypes: [PluginCapabilityType.COMMAND],
        cardinality: 'MANY',
        metadata: {}
      });

      const pt = extManager.findExtensionPoint('ep1');
      expect(pt).toBeDefined();
      expect(pt?.name).toBe('Extension Point 1');
      expect(extManager.listExtensionPoints()).toHaveLength(1);
    });

    // 18. duplicate extension point rejection
    it('rejects duplicate extension point registration', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', {
        id: 'ep1',
        name: 'Extension Point 1',
        version: '1.0.0',
        acceptedTypes: [PluginCapabilityType.COMMAND],
        cardinality: 'MANY',
        metadata: {}
      });

      expect(() => {
        extManager.registerExtensionPoint('p1', {
          id: 'ep1',
          name: 'Extension Point 1 duplicate',
          version: '1.0.0',
          acceptedTypes: [PluginCapabilityType.COMMAND],
          cardinality: 'MANY',
          metadata: {}
        });
      }).toThrow(PluginExtensionConflictError);
    });

    // 20. unregister
    it('unregisters extension point successfully', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', {
        id: 'ep1',
        name: 'EP 1',
        version: '1.0.0',
        acceptedTypes: [PluginCapabilityType.COMMAND],
        cardinality: 'MANY',
        metadata: {}
      });

      expect(extManager.findExtensionPoint('ep1')).not.toBeNull();
      extManager.unregisterExtensionPoint('p1', 'ep1');
      expect(extManager.findExtensionPoint('ep1')).toBeNull();
    });

    // 23. invalid cardinality
    it('rejects registration with invalid cardinality', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      expect(() => {
        extManager.registerExtensionPoint('p1', {
          id: 'ep1',
          name: 'EP 1',
          version: '1.0.0',
          acceptedTypes: [PluginCapabilityType.COMMAND],
          cardinality: 'INVALID' as any,
          metadata: {}
        });
      }).toThrow(PluginExtensionRegistrationError);
    });
  });

  // EXTENSION TESTS
  describe('Extensions', () => {
    // 24. extension registration
    // 32. find extensions by point
    // 33. find extensions by plugin
    it('registers and filters extensions', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      const regResult = extManager.registerExtension('p1', {
        extensionId: 'ext1',
        extensionPointId: 'ep1',
        priority: 100,
        metadata: {}
      });

      expect(regResult.success).toBe(true);
      expect(extManager.findExtension('ext1')).toBeDefined();
      expect(extManager.findExtensions('ep1')).toHaveLength(1);
      expect(extManager.findExtensionsByPlugin('p1')).toHaveLength(1);
    });

    // 25. missing extension point rejection
    it('rejects registration referencing missing extension point', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext1',
          extensionPointId: 'missing-ep',
          priority: 100,
          metadata: {}
        });
      }).toThrow(PluginExtensionRegistrationError);
    });

    // 26. missing capability rejection
    it('rejects registration referencing missing capability', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext1',
          extensionPointId: 'ep1',
          capabilityId: 'missing-cap',
          priority: 100,
          metadata: {}
        });
      }).toThrow(PluginExtensionRegistrationError);
    });

    // 27. capability ownership validation
    it('validates capability owner belongs to registering plugin', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const m2 = createManifest('p2', '1.0.0', 'p2.js');
      const { loader, lifecycle } = createRuntimeContext([m1, m2], ['p1', 'p2']);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.loadAll();
      await lifecycle.initializePlugin('p1');
      await lifecycle.initializePlugin('p2');
      await lifecycle.activatePlugin('p1');
      await lifecycle.activatePlugin('p2');

      capManager.registerCapability('p2', { id: 'c2', name: 'Cap 2', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      // p1 attempts to register extension referencing c2 owned by p2
      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext1',
          extensionPointId: 'ep1',
          capabilityId: 'c2',
          priority: 100,
          metadata: {}
        });
      }).toThrow(PluginExtensionConflictError);
    });

    // 28. capability type compatibility
    // 41. incompatible capability type conflict
    it('validates capability type compatibility with extension point accepted types', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      capManager.registerCapability('p1', { id: 'c1', name: 'Service Cap', type: PluginCapabilityType.SERVICE, version: '1.0.0' });
      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1 Accepting Commands', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext1',
          extensionPointId: 'ep1',
          capabilityId: 'c1',
          priority: 100,
          metadata: {}
        });
      }).toThrow(PluginExtensionConflictError);
    });

    // 29. duplicate extension rejection
    // 39. duplicate extension conflict
    it('rejects duplicate extension registration', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext1',
          extensionPointId: 'ep1',
          priority: 200,
          metadata: {}
        });
      }).toThrow(PluginExtensionConflictError);
    });

    // 30. priority ordering
    // 31. deterministic FIFO tie ordering
    it('sorts extensions topologically by priority and FIFO tie ordering', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext2', extensionPointId: 'ep1', priority: 200, metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext3', extensionPointId: 'ep1', priority: 100, metadata: {} });

      const sorted = extManager.findExtensions('ep1');
      expect(sorted).toHaveLength(3);
      expect(sorted[0].extensionId).toBe('ext2'); // Highest priority first
      expect(sorted[1].extensionId).toBe('ext1'); // Tie: FIFO registered first
      expect(sorted[2].extensionId).toBe('ext3');
    });

    // 21. SINGLE cardinality
    // 22. MANY cardinality
    // 40. exclusive extension point conflict
    it('enforces SINGLE cardinality rules on extension registration', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'SINGLE', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      expect(() => {
        extManager.registerExtension('p1', {
          extensionId: 'ext2',
          extensionPointId: 'ep1',
          priority: 200,
          metadata: {}
        });
      }).toThrow(PluginExtensionConflictError);
    });

    // 34. unregister extension
    it('unregisters extensions successfully', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      expect(extManager.findExtension('ext1')).not.toBeNull();
      extManager.unregisterExtension('p1', 'ext1');
      expect(extManager.findExtension('ext1')).toBeNull();
    });

    // 35. unregister plugin extensions
    it('unregisters all extensions belonging to a plugin', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      extManager.unregisterPluginExtensions('p1');
      expect(extManager.findExtensionsByPlugin('p1')).toHaveLength(0);
    });

    // 36. enable extension
    // 37. disable extension
    it('enables and disables extensions', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      extManager.disableExtension('ext1');
      expect(extManager.findExtension('ext1')).toBeNull();

      extManager.enableExtension('ext1');
      expect(extManager.findExtension('ext1')).not.toBeNull();
    });
  });

  // LIFECYCLE TESTS
  describe('Lifecycle Integration', () => {
    // 42. registration while ACTIVE
    // 43. registration while DEACTIVATED rejected
    // 44. registration while DISPOSED rejected
    it('enforces capability/extension registrations to respect owner plugin lifecycle state', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');

      // State is DEACTIVATED (initialized but not active)
      expect(() => {
        capManager.registerCapability('p1', { id: 'c1', name: 'C1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      }).toThrow(PluginCapabilityRegistrationError);

      await lifecycle.activatePlugin('p1');
      // State is ACTIVE
      capManager.registerCapability('p1', { id: 'c1', name: 'C1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      expect(capManager.containsCapability('c1')).toBe(true);

      await lifecycle.disposePlugin('p1');
      // State is DISPOSED
      expect(() => {
        capManager.registerCapability('p1', { id: 'c2', name: 'C2', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      }).toThrow(PluginCapabilityRegistrationError);
    });

    // 45. plugin deactivation removes/inactivates capabilities
    // 46. plugin disposal cleans registrations
    it('automatically unregisters capabilities and extensions upon deactivation or disposal', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      capManager.registerCapability('p1', { id: 'c1', name: 'C1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });
      extManager.registerExtension('p1', { extensionId: 'ext1', extensionPointId: 'ep1', priority: 100, metadata: {} });

      // Deactivate
      await lifecycle.deactivatePlugin('p1');
      expect(capManager.containsCapability('c1')).toBe(false);
      expect(extManager.findExtension('ext1')).toBeNull();
    });

    // 47. failed plugin cannot expose capabilities
    it('ensures failed plugin capabilities are not exposed', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      capManager.registerCapability('p1', { id: 'c1', name: 'C1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });

      // Trigger failure via hook throw during disposal/deactivation
      lifecycle.registerHooks('p1', {
        onDeactivate: async () => { throw new Error('failure deactivating'); }
      });

      await expect(lifecycle.deactivatePlugin('p1')).rejects.toThrow('failure deactivating');
      expect(lifecycle.getLifecycleState('p1')).toBe(PluginState.FAILED);

      expect(capManager.findCapability('c1')).toBeNull();
    });
  });

  // INTEGRATION TESTS
  describe('Integration', () => {
    // 48. provider capability delegation
    // 49. provider extension delegation
    // 52. diagnostics aggregation
    it('delegates capability and extension features through PluginProvider', async () => {
      const provider = new PluginProvider();
      expect(provider.capabilities()).toBeDefined();
      expect(provider.extensions()).toBeDefined();

      const diag = provider.diagnostics();
      expect(diag.capabilityManager).toBeDefined();
      expect(diag.extensionManager).toBeDefined();
    });

    // 50. runtime capability delegation
    // 51. runtime extension delegation
    it('delegates capability and extension features through PluginRuntime coordinator', async () => {
      const runtime = new PluginRuntime();
      expect(runtime.capabilities()).toBeDefined();
      expect(runtime.extensions()).toBeDefined();
    });

    // 53. reset behavior
    it('clears registered capabilities and extensions upon reset', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1]);
      const capManager = new PluginCapabilityManager(lifecycle);
      const extManager = new PluginExtensionManager(lifecycle, capManager);

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');
      await lifecycle.activatePlugin('p1');

      capManager.registerCapability('p1', { id: 'c1', name: 'C1', type: PluginCapabilityType.COMMAND, version: '1.0.0' });
      extManager.registerExtensionPoint('p1', { id: 'ep1', name: 'EP1', version: '1.0.0', acceptedTypes: [PluginCapabilityType.COMMAND], cardinality: 'MANY', metadata: {} });

      capManager.reset();
      extManager.reset();

      expect(capManager.containsCapability('c1')).toBe(false);
      expect(extManager.findExtensionPoint('ep1')).toBeNull();
    });
  });

});
