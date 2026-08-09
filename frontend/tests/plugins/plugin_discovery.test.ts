import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  SemVerValidator,
  InMemoryDiscoverySource,
  PluginDiscoveryManager,
  PluginManifestError,
  PluginDuplicateError,
  PluginDiscoveryError,
  type IPluginDiscoverySource,
  type IPluginProvider
} from '../../src/plugins';

describe('Plugin Discovery & Manifest Runtime (Phase 17.2)', () => {

  const createValidRawManifest = (overrides = {}) => ({
    id: 'demo-plugin',
    name: 'Demo Plugin',
    version: '1.0.0',
    description: 'An example plugin',
    author: 'Auralis Team',
    schemaVersion: '1.0.0',
    entryPoint: 'dist/index.js',
    dependencies: [],
    capabilities: [],
    metadata: { test: true },
    ...overrides
  });

  // 1. Manifest creation
  it('creates and parses a valid manifest', () => {
    const raw = createValidRawManifest();
    const manifest = PluginManifestValidator.parse(raw);

    expect(manifest.id).toBe('demo-plugin');
    expect(manifest.name).toBe('Demo Plugin');
    expect(manifest.version).toBe('1.0.0');
    expect(manifest.entryPoint).toBe('dist/index.js');
    expect(manifest.author).toBe('Auralis Team');
  });

  // 2. Manifest immutability
  it('enforces manifest immutability', () => {
    const raw = createValidRawManifest();
    const manifest = PluginManifestValidator.parse(raw);

    expect(Object.isFrozen(manifest)).toBe(true);
    expect(Object.isFrozen(manifest.dependencies)).toBe(true);
    expect(Object.isFrozen(manifest.capabilities)).toBe(true);
    expect(Object.isFrozen(manifest.metadata)).toBe(true);
    expect(() => {
      (manifest as any).name = 'New Name';
    }).toThrow(TypeError);
  });

  // 3. Valid manifest parsing
  it('parses valid manifest from a JSON string', () => {
    const rawStr = JSON.stringify(createValidRawManifest({ id: 'string-id' }));
    const manifest = PluginManifestValidator.parse(rawStr);
    expect(manifest.id).toBe('string-id');
  });

  // 4. Invalid manifest parsing
  it('throws PluginManifestError for malformed JSON string', () => {
    expect(() => {
      PluginManifestValidator.parse('{ invalid json ');
    }).toThrow(PluginManifestError);
  });

  // 5. Required field validation
  it('fails validation when required fields are missing', () => {
    const missingId = createValidRawManifest({ id: undefined });
    expect(() => PluginManifestValidator.parse(missingId)).toThrow(PluginManifestError);

    const missingName = createValidRawManifest({ name: undefined });
    expect(() => PluginManifestValidator.parse(missingName)).toThrow(PluginManifestError);

    const missingVersion = createValidRawManifest({ version: undefined });
    expect(() => PluginManifestValidator.parse(missingVersion)).toThrow(PluginManifestError);

    const missingEntryPoint = createValidRawManifest({ entryPoint: undefined });
    expect(() => PluginManifestValidator.parse(missingEntryPoint)).toThrow(PluginManifestError);
  });

  // 6. Invalid plugin IDs
  it('rejects invalid plugin IDs', () => {
    const spaceId = createValidRawManifest({ id: 'my plugin' });
    expect(() => PluginManifestValidator.parse(spaceId)).toThrow(PluginManifestError);

    const emptyId = createValidRawManifest({ id: '' });
    expect(() => PluginManifestValidator.parse(emptyId)).toThrow(PluginManifestError);

    const specialId = createValidRawManifest({ id: 'plugin@123' });
    expect(() => PluginManifestValidator.parse(specialId)).toThrow(PluginManifestError);
  });

  // 7. Invalid plugin versions
  it('rejects invalid plugin versions', () => {
    const invalidVer = createValidRawManifest({ version: '1.0' });
    expect(() => PluginManifestValidator.parse(invalidVer)).toThrow(PluginManifestError);

    const lettersVer = createValidRawManifest({ version: 'abc' });
    expect(() => PluginManifestValidator.parse(lettersVer)).toThrow(PluginManifestError);
  });

  // 8. Valid SemVer
  it('validates correct SemVer versions', () => {
    expect(SemVerValidator.isValid('1.0.0')).toBe(true);
    expect(SemVerValidator.isValid('0.3.7')).toBe(true);
    expect(SemVerValidator.isValid('10.25.300')).toBe(true);
  });

  // 9. Invalid SemVer
  it('rejects malformed SemVer strings', () => {
    expect(SemVerValidator.isValid('1.0')).toBe(false);
    expect(SemVerValidator.isValid('1')).toBe(false);
    expect(SemVerValidator.isValid('1.0.0.0')).toBe(false);
    expect(SemVerValidator.isValid('v1.0.0')).toBe(false);
  });

  // 10. Prerelease versions
  it('supports prerelease identifiers in SemVer', () => {
    expect(SemVerValidator.isValid('1.0.0-alpha')).toBe(true);
    expect(SemVerValidator.isValid('1.0.0-alpha.1')).toBe(true);
    expect(SemVerValidator.isValid('1.0.0-0.3.7')).toBe(true);
    expect(SemVerValidator.isValid('1.0.0-x.y.z--1')).toBe(true);

    const manifest = PluginManifestValidator.parse(createValidRawManifest({ version: '1.0.0-beta.2' }));
    expect(manifest.version).toBe('1.0.0-beta.2');
  });

  // 11. Build metadata
  it('supports build metadata in SemVer', () => {
    expect(SemVerValidator.isValid('1.0.0+build.1')).toBe(true);
    expect(SemVerValidator.isValid('1.0.0-alpha+001')).toBe(true);
    expect(SemVerValidator.isValid('1.0.0+20130313144700')).toBe(true);

    const manifest = PluginManifestValidator.parse(createValidRawManifest({ version: '1.0.0+2026.sha.1' }));
    expect(manifest.version).toBe('1.0.0+2026.sha.1');
  });

  // 12. Entry point validation
  it('rejects empty or non-string entry points', () => {
    const emptyEP = createValidRawManifest({ entryPoint: '' });
    expect(() => PluginManifestValidator.parse(emptyEP)).toThrow(PluginManifestError);

    const numberEP = createValidRawManifest({ entryPoint: 123 });
    expect(() => PluginManifestValidator.parse(numberEP)).toThrow(PluginManifestError);
  });

  // 13. Dependency declaration validation
  it('validates dependency syntax ranges', () => {
    // Valid ranges
    expect(SemVerValidator.isValidRange('^1.0.0')).toBe(true);
    expect(SemVerValidator.isValidRange('~1.2.3')).toBe(true);
    expect(SemVerValidator.isValidRange('>=1.0.0 <2.0.0')).toBe(true);
    expect(SemVerValidator.isValidRange('*')).toBe(true);
    expect(SemVerValidator.isValidRange('1.x')).toBe(true);

    // Invalid ranges
    expect(SemVerValidator.isValidRange('invalid-range')).toBe(false);
    expect(SemVerValidator.isValidRange('>=abc')).toBe(false);

    const raw = createValidRawManifest({
      dependencies: [
        { id: 'dep-a', versionRange: '^1.0.0' },
        { id: 'dep-b', versionRange: '*' }
      ]
    });
    const manifest = PluginManifestValidator.parse(raw);
    expect(manifest.dependencies).toHaveLength(2);
    expect(manifest.dependencies[0].id).toBe('dep-a');
  });

  // 14. Capability declaration validation
  it('validates capabilities', () => {
    const raw = createValidRawManifest({
      capabilities: [
        { type: 'ui', properties: { position: 'sidebar' } }
      ]
    });
    const manifest = PluginManifestValidator.parse(raw);
    expect(manifest.capabilities).toHaveLength(1);
    expect(manifest.capabilities[0].type).toBe('ui');
    expect(manifest.capabilities[0].properties.position).toBe('sidebar');

    const invalidCapType = createValidRawManifest({
      capabilities: [
        { type: '', properties: {} }
      ]
    });
    expect(() => PluginManifestValidator.parse(invalidCapType)).toThrow(PluginManifestError);
  });

  // 15. Duplicate declaration detection
  it('rejects duplicate declarations of dependencies or capabilities inside manifest', () => {
    const dupDeps = createValidRawManifest({
      dependencies: [
        { id: 'dep-a', versionRange: '^1.0.0' },
        { id: 'dep-a', versionRange: '^2.0.0' }
      ]
    });
    expect(() => PluginManifestValidator.parse(dupDeps)).toThrow(PluginManifestError);

    const dupCaps = createValidRawManifest({
      capabilities: [
        { type: 'ui', properties: { a: 1 } },
        { type: 'ui', properties: { b: 2 } }
      ]
    });
    expect(() => PluginManifestValidator.parse(dupCaps)).toThrow(PluginManifestError);
  });

  // 16. Discovery source registration
  it('registers and unregisters discovery sources', () => {
    const manager = new PluginDiscoveryManager();
    const source: IPluginDiscoverySource = new InMemoryDiscoverySource(
      { id: 'src-1', name: 'Source 1', type: 'in-memory' },
      []
    );

    manager.registerSource(source);
    expect(manager.getSources()).toHaveLength(1);
    expect(manager.getSources()[0].descriptor.id).toBe('src-1');

    manager.unregisterSource('src-1');
    expect(manager.getSources()).toHaveLength(0);

    expect(() => manager.unregisterSource('src-1')).toThrow(PluginDiscoveryError);
  });

  // 17. Discovery from in-memory source
  it('discovers manifests from in-memory source', async () => {
    const manager = new PluginDiscoveryManager();
    const raw = createValidRawManifest({ id: 'in-memory-plugin' });
    const source = new InMemoryDiscoverySource(
      { id: 'mem-src', name: 'Memory', type: 'in-memory' },
      [raw]
    );

    manager.registerSource(source);
    const result = await manager.discover();

    expect(result.success).toBe(true);
    expect(result.manifests).toHaveLength(1);
    expect(result.manifests[0].id).toBe('in-memory-plugin');
    expect(manager.find('in-memory-plugin')).not.toBeNull();
  });

  // 18. Multiple manifests
  it('discovers multiple manifests from multiple sources', async () => {
    const manager = new PluginDiscoveryManager();
    const src1 = new InMemoryDiscoverySource(
      { id: 'src-1', name: 'Src 1', type: 'in-memory' },
      [createValidRawManifest({ id: 'plugin-1' })]
    );
    const src2 = new InMemoryDiscoverySource(
      { id: 'src-2', name: 'Src 2', type: 'in-memory' },
      [createValidRawManifest({ id: 'plugin-2' })]
    );

    manager.registerSource(src1);
    manager.registerSource(src2);

    const result = await manager.discover();
    expect(result.success).toBe(true);
    expect(result.manifests).toHaveLength(2);
    expect(manager.findAll()).toHaveLength(2);
  });

  // 19. Duplicate plugin ID rejection
  it('rejects duplicate plugin IDs and throws PluginDuplicateError', async () => {
    const manager = new PluginDiscoveryManager();
    const src1 = new InMemoryDiscoverySource(
      { id: 'src-1', name: 'Src 1', type: 'in-memory' },
      [createValidRawManifest({ id: 'duplicate-plugin' })]
    );
    const src2 = new InMemoryDiscoverySource(
      { id: 'src-2', name: 'Src 2', type: 'in-memory' },
      [createValidRawManifest({ id: 'duplicate-plugin' })]
    );

    manager.registerSource(src1);
    manager.registerSource(src2);

    await expect(manager.discover()).rejects.toThrow(PluginDuplicateError);
    expect(manager.statistics().duplicateAttempts).toBe(1);
  });

  // 20. Invalid manifest rejection
  it('rejects invalid manifests during discovery but continues processing others', async () => {
    const manager = new PluginDiscoveryManager();
    const validRaw = createValidRawManifest({ id: 'valid-p' });
    const invalidRaw = createValidRawManifest({ id: 'invalid-p', version: 'not-semver' });
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [validRaw, invalidRaw]
    );

    manager.registerSource(source);
    const result = await manager.discover();

    expect(result.success).toBe(false);
    expect(result.manifests).toHaveLength(1);
    expect(result.manifests[0].id).toBe('valid-p');
    expect(result.invalid).toHaveLength(1);
    expect(result.invalid[0].issues).toBeDefined();
    expect(manager.statistics().invalidManifests).toBe(1);
  });

  // 21. Successful manifest registration
  it('verifies manifest exists in manager after successful discovery', async () => {
    const manager = new PluginDiscoveryManager();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'find-me' })]
    );
    manager.registerSource(source);
    await manager.discover();

    expect(manager.contains('find-me')).toBe(true);
  });

  // 22. find()
  // 23. findAll()
  // 24. contains()
  // 25. remove()
  // 26. clear()
  it('verifies crud lookup operations', async () => {
    const manager = new PluginDiscoveryManager();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [
        createValidRawManifest({ id: 'p1' }),
        createValidRawManifest({ id: 'p2' })
      ]
    );
    manager.registerSource(source);
    await manager.discover();

    // find()
    expect(manager.find('p1')?.id).toBe('p1');
    expect(manager.find('non-existent')).toBeNull();

    // findAll()
    expect(manager.findAll()).toHaveLength(2);

    // contains()
    expect(manager.contains('p2')).toBe(true);

    // remove()
    expect(manager.remove('p2')).toBe(true);
    expect(manager.contains('p2')).toBe(false);

    // clear()
    manager.clear();
    expect(manager.findAll()).toHaveLength(0);
  });

  // 27. Discovery statistics
  it('tracks discovery statistics correctly', async () => {
    const manager = new PluginDiscoveryManager();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'p1' })]
    );
    manager.registerSource(source);

    expect(manager.statistics().discoveryAttempts).toBe(0);
    
    await manager.discover();
    expect(manager.statistics().discoveryAttempts).toBe(1);
    expect(manager.statistics().discoveredPlugins).toBe(1);
    expect(manager.statistics().validManifests).toBe(1);
  });

  // 28. Discovery health
  it('determines health based on failures and source existence', async () => {
    const manager = new PluginDiscoveryManager();
    // No source registered
    expect(manager.health().healthy).toBe(false);
    expect(manager.health().issues).toContain('No discovery sources registered');

    // Register source
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      []
    );
    manager.registerSource(source);
    expect(manager.health().healthy).toBe(true);
  });

  // 29. Provider delegation
  it('delegates discovery through PluginProvider', async () => {
    const provider = new PluginProvider();
    const source = new InMemoryDiscoverySource(
      { id: 'p-src', name: 'P Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'provider-p' })]
    );

    provider.discovery().registerSource(source);
    const result = await provider.discovery().discover();

    expect(result.success).toBe(true);
    expect(provider.discovery().contains('provider-p')).toBe(true);
  });

  // 30. Runtime delegation
  it('delegates discovery through PluginRuntime', async () => {
    const runtime = new PluginRuntime();
    const source = new InMemoryDiscoverySource(
      { id: 'r-src', name: 'R Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'runtime-p' })]
    );

    runtime.discovery().registerSource(source);
    const result = await runtime.discovery().discover();

    expect(result.success).toBe(true);
    expect(runtime.discovery().contains('runtime-p')).toBe(true);
  });

  // 31. Dependency injection with a custom discovery/provider implementation
  it('supports DI with custom discovery implementation', () => {
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
      discovery: () => {
        return {
          registerSource: () => {},
          unregisterSource: () => {},
          getSources: () => [],
          discover: async () => ({ success: true, manifests: [], invalid: [], duplicates: [], failures: [] }),
          discoverFromSource: async () => ({ success: true, manifests: [], invalid: [], duplicates: [], failures: [] }),
          find: () => null,
          findAll: () => [],
          contains: () => false,
          remove: () => false,
          clear: () => {},
          statistics: () => ({ discoveryAttempts: 42 } as any),
          health: () => ({ healthy: true, message: 'Mocked', issues: [] }),
          reset: () => {}
        };
      }
    };

    const runtime = new PluginRuntime(customProvider);
    expect(runtime.discovery().statistics().discoveryAttempts).toBe(42);
  });

  // 32. Reset/lifecycle behavior
  it('resets discovery manager correctly', async () => {
    const manager = new PluginDiscoveryManager();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'p1' })]
    );
    manager.registerSource(source);
    await manager.discover();

    expect(manager.findAll()).toHaveLength(1);
    expect(manager.getSources()).toHaveLength(1);

    manager.reset();
    expect(manager.findAll()).toHaveLength(0);
    expect(manager.getSources()).toHaveLength(0);
    expect(manager.statistics().discoveryAttempts).toBe(0);
  });

  // 33. Internal state cannot be mutated through returned snapshots
  it('prevents internal state mutation through snapshots', async () => {
    const manager = new PluginDiscoveryManager();
    const source = new InMemoryDiscoverySource(
      { id: 'src', name: 'Src', type: 'in-memory' },
      [createValidRawManifest({ id: 'p1' })]
    );
    manager.registerSource(source);
    await manager.discover();

    const sources = manager.getSources();
    expect(Object.isFrozen(sources)).toBe(true);
    expect(() => {
      (sources as any).push({});
    }).toThrow(TypeError);

    const manifests = manager.findAll();
    expect(Object.isFrozen(manifests)).toBe(true);
    expect(() => {
      (manifests as any).push({});
    }).toThrow(TypeError);

    const manifest = manager.find('p1')!;
    expect(Object.isFrozen(manifest)).toBe(true);
    expect(() => {
      (manifest as any).id = 'mutated';
    }).toThrow(TypeError);
  });

});
