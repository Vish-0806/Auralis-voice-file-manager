import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationProvider,
  ConfigurationProviderException,
  ConfigurationRuntime,
  ConfigurationSourcePriority,
  createConfigurationEntry,
  createConfigurationSnapshot,
  createConfigurationSourceHealth,
  createConfigurationSourceRegistration,
  createConfigurationSourceStatistics,
  getConfigurationProvider,
  getConfigurationRuntime,
  MemoryConfigurationSource,
  resetConfigurationProvider,
  resetConfigurationRuntime,
  SourceRegistry,
} from '../../src/runtime/config';

describe('Phase 16.3.2 — Frontend Configuration Sources & Resolution Foundation', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. ConfigurationSourcePriority Enum & Source Models', () => {
    it('should verify MEMORY priority value', () => {
      expect(ConfigurationSourcePriority.MEMORY).toBe(500);
    });

    it('should verify RUNTIME priority value', () => {
      expect(ConfigurationSourcePriority.RUNTIME).toBe(400);
    });

    it('should verify ENVIRONMENT priority value', () => {
      expect(ConfigurationSourcePriority.ENVIRONMENT).toBe(300);
    });

    it('should verify LOCAL priority value', () => {
      expect(ConfigurationSourcePriority.LOCAL).toBe(200);
    });

    it('should verify SESSION priority value', () => {
      expect(ConfigurationSourcePriority.SESSION).toBe(100);
    });

    it('should verify DEFAULT priority value', () => {
      expect(ConfigurationSourcePriority.DEFAULT).toBe(0);
    });

    it('should create immutable ConfigurationEntry model', () => {
      const entry = createConfigurationEntry({
        key: 'app.name',
        value: 'Auralis',
        sourceName: 'MemorySource',
        priority: ConfigurationSourcePriority.MEMORY,
      });

      expect(entry.key).toBe('app.name');
      expect(entry.value).toBe('Auralis');
      expect(entry.sourceName).toBe('MemorySource');
      expect(entry.priority).toBe(500);
      expect(Object.isFrozen(entry)).toBe(true);
    });

    it('should create immutable ConfigurationSnapshot model', () => {
      const entry = createConfigurationEntry({ key: 'k1', value: 'v1', sourceName: 'S1' });
      const snapshot = createConfigurationSnapshot({
        entries: { k1: entry },
        mergedValues: { k1: 'v1' },
        sourceCount: 1,
      });

      expect(snapshot.sourceCount).toBe(1);
      expect(snapshot.mergedValues.k1).toBe('v1');
      expect(Object.isFrozen(snapshot)).toBe(true);
      expect(Object.isFrozen(snapshot.entries)).toBe(true);
      expect(Object.isFrozen(snapshot.mergedValues)).toBe(true);
    });

    it('should create immutable ConfigurationSourceStatistics model', () => {
      const stats = createConfigurationSourceStatistics({ reads: 10, hits: 8, misses: 2 });
      expect(stats.reads).toBe(10);
      expect(stats.hits).toBe(8);
      expect(stats.misses).toBe(2);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable ConfigurationSourceHealth model', () => {
      const health = createConfigurationSourceHealth({ sourceName: 'MemorySource', healthy: true });
      expect(health.sourceName).toBe('MemorySource');
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable ConfigurationSourceRegistration model', () => {
      const reg = createConfigurationSourceRegistration({ sourceName: 'EnvSource', priority: 300 });
      expect(reg.sourceName).toBe('EnvSource');
      expect(reg.priority).toBe(300);
      expect(Object.isFrozen(reg)).toBe(true);
    });
  });

  describe('2. MemoryConfigurationSource Engine', () => {
    it('should set and get configuration values', () => {
      const source = new MemoryConfigurationSource();
      expect(source.set('api.url', 'https://api.auralis.com')).toBe(true);
      expect(source.get('api.url')).toBe('https://api.auralis.com');
      expect(source.contains('api.url')).toBe(true);
    });

    it('should initialize with initial key-value dictionary', () => {
      const source = new MemoryConfigurationSource('InitialMem', 500, {
        'theme.mode': 'dark',
        'theme.accent': 'blue',
      });

      expect(source.get('theme.mode')).toBe('dark');
      expect(source.get('theme.accent')).toBe('blue');
    });

    it('should remove configuration key and update delete telemetry', () => {
      const source = new MemoryConfigurationSource();
      source.set('temp.key', 'temp');
      expect(source.contains('temp.key')).toBe(true);

      expect(source.remove('temp.key')).toBe(true);
      expect(source.contains('temp.key')).toBe(false);
      expect(source.get('temp.key')).toBeUndefined();
      expect(source.statistics().deletes).toBe(1);
    });

    it('should clear all stored keys and update delete telemetry', () => {
      const source = new MemoryConfigurationSource();
      source.set('k1', 'v1');
      source.set('k2', 'v2');

      expect(source.keys().length).toBe(2);
      source.clear();
      expect(source.keys().length).toBe(0);
      expect(source.get('k1')).toBeUndefined();
      expect(source.statistics().deletes).toBe(1);
    });

    it('should list keys, values, and items dictionary', () => {
      const source = new MemoryConfigurationSource();
      source.set('k1', 'v1');
      source.set('k2', 'v2');

      expect(source.keys()).toEqual(['k1', 'k2']);
      expect(source.values()).toEqual(['v1', 'v2']);
      expect(source.items()).toEqual({ k1: 'v1', k2: 'v2' });
    });

    it('should record read/write telemetry statistics', () => {
      const source = new MemoryConfigurationSource();
      source.set('k1', 'v1');
      source.get('k1'); // hit
      source.get('k2'); // miss

      const stats = source.statistics();
      expect(stats.writes).toBe(1);
      expect(stats.reads).toBe(2);
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
      expect(stats.itemCount).toBe(1);
    });

    it('should return health evaluation snapshot when enabled and disabled', () => {
      const source = new MemoryConfigurationSource('MemHealth', 500);
      const health = source.health();

      expect(health.sourceName).toBe('MemHealth');
      expect(health.healthy).toBe(true);
      expect(health.enabled).toBe(true);
    });
  });

  describe('3. SourceRegistry Engine', () => {
    it('should register configuration source and retrieve by name', () => {
      const registry = new SourceRegistry();
      const memSource = new MemoryConfigurationSource('MemSource', 500);

      registry.register(memSource);
      expect(registry.get('MemSource')).toBe(memSource);
    });

    it('should reject registration of duplicate source name', () => {
      const registry = new SourceRegistry();
      const mem1 = new MemoryConfigurationSource('MemSource', 500);
      const mem2 = new MemoryConfigurationSource('MemSource', 500);

      registry.register(mem1);
      expect(() => registry.register(mem2)).toThrow(ConfigurationProviderException);
    });

    it('should reject registration of null source', () => {
      const registry = new SourceRegistry();
      expect(() => registry.register(null as any)).toThrow(ConfigurationProviderException);
    });

    it('should reject registration of empty source name', () => {
      const registry = new SourceRegistry();
      expect(() => registry.register(new MemoryConfigurationSource('   '))).toThrow(
        ConfigurationProviderException,
      );
    });

    it('should unregister existing configuration source', () => {
      const registry = new SourceRegistry();
      const memSource = new MemoryConfigurationSource('MemSource', 500);

      registry.register(memSource);
      expect(registry.unregister('MemSource')).toBe(true);
      expect(registry.get('MemSource')).toBeUndefined();
    });

    it('should return false when unregistering non-existent source', () => {
      const registry = new SourceRegistry();
      expect(registry.unregister('NonExistent')).toBe(false);
    });

    it('should sort sources by priority descending (highest priority first)', () => {
      const registry = new SourceRegistry();
      const defaultSrc = new MemoryConfigurationSource('DefaultSrc', ConfigurationSourcePriority.DEFAULT);
      const envSrc = new MemoryConfigurationSource('EnvSrc', ConfigurationSourcePriority.ENVIRONMENT);
      const memSrc = new MemoryConfigurationSource('MemSrc', ConfigurationSourcePriority.MEMORY);

      registry.register(defaultSrc);
      registry.register(envSrc);
      registry.register(memSrc);

      const sources = registry.listSources();
      expect(sources[0].name).toBe('MemSrc'); // 500
      expect(sources[1].name).toBe('EnvSrc'); // 300
      expect(sources[2].name).toBe('DefaultSrc'); // 0
    });

    it('should clear all registered sources', () => {
      const registry = new SourceRegistry();
      registry.register(new MemoryConfigurationSource('S1', 100));
      registry.register(new MemoryConfigurationSource('S2', 200));

      expect(registry.listSources().length).toBe(2);
      registry.clear();
      expect(registry.listSources().length).toBe(0);
    });
  });

  describe('4. Configuration Priority Resolution & Overrides', () => {
    it('should resolve key from highest priority source', () => {
      const registry = new SourceRegistry();
      const envSource = new MemoryConfigurationSource('EnvSource', ConfigurationSourcePriority.ENVIRONMENT, {
        'app.title': 'Env Title',
        'env.only': 'EnvValue',
      });
      const memSource = new MemoryConfigurationSource('MemSource', ConfigurationSourcePriority.MEMORY, {
        'app.title': 'Memory Title',
      });

      registry.register(envSource);
      registry.register(memSource);

      const provider = new ConfigurationProvider(undefined, undefined, undefined, registry);

      // MemorySource (500) overrides EnvSource (300) for 'app.title'
      expect(provider.get('app.title')).toBe('Memory Title');
      // EnvSource (300) resolves 'env.only'
      expect(provider.get('env.only')).toBe('EnvValue');
      // Default value fallback
      expect(provider.get('missing.key', 'Fallback')).toBe('Fallback');
    });

    it('should check key existence across all enabled sources via has()', () => {
      const registry = new SourceRegistry();
      const envSource = new MemoryConfigurationSource('EnvSource', ConfigurationSourcePriority.ENVIRONMENT, {
        'app.env': 'production',
      });
      registry.register(envSource);

      const provider = new ConfigurationProvider(undefined, undefined, undefined, registry);

      expect(provider.has('app.env')).toBe(true);
      expect(provider.has('nonexistent')).toBe(false);
    });

    it('should retrieve ConfigurationEntry metadata for resolved key', () => {
      const registry = new SourceRegistry();
      const envSource = new MemoryConfigurationSource('EnvSource', ConfigurationSourcePriority.ENVIRONMENT, {
        'db.host': 'localhost',
      });
      registry.register(envSource);

      const provider = new ConfigurationProvider(undefined, undefined, undefined, registry);
      const entry = provider.getEntry('db.host');

      expect(entry).toBeDefined();
      expect(entry?.key).toBe('db.host');
      expect(entry?.value).toBe('localhost');
      expect(entry?.sourceName).toBe('EnvSource');
      expect(entry?.priority).toBe(ConfigurationSourcePriority.ENVIRONMENT);
    });

    it('should return undefined for getEntry on missing key', () => {
      const provider = new ConfigurationProvider();
      expect(provider.getEntry('missing.key')).toBeUndefined();
    });

    it('should build merged configuration dictionary with priority override', () => {
      const registry = new SourceRegistry();
      const defaultSource = new MemoryConfigurationSource(
        'DefaultSource',
        ConfigurationSourcePriority.DEFAULT,
        { 'a': 1, 'b': 2, 'c': 3 },
      );
      const memSource = new MemoryConfigurationSource(
        'MemSource',
        ConfigurationSourcePriority.MEMORY,
        { 'b': 20, 'd': 40 },
      );

      registry.register(defaultSource);
      registry.register(memSource);

      const provider = new ConfigurationProvider(undefined, undefined, undefined, registry);
      const merged = provider.getAll();

      expect(merged).toMatchObject({ a: 1, b: 20, c: 3, d: 40 });
    });

    it('should generate complete ConfigurationSnapshot snapshot', () => {
      const registry = new SourceRegistry();
      const memSource = new MemoryConfigurationSource('MemSource', ConfigurationSourcePriority.MEMORY, {
        'feature.flag': true,
      });
      registry.register(memSource);

      const provider = new ConfigurationProvider(undefined, undefined, undefined, registry);
      const snapshot = provider.createSnapshot();

      expect(snapshot.sourceCount).toBe(2); // Default MemorySource + MemSource
      expect(snapshot.mergedValues['feature.flag']).toBe(true);
      expect(snapshot.entries['feature.flag'].sourceName).toBe('MemSource');
    });
  });

  describe('5. Provider & Runtime Delegation Integration', () => {
    it('should delegate registerSource to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R1', 100);
      runtime.registerSource(src);
      expect(runtime.listSources().some((s) => s.name === 'R1')).toBe(true);
    });

    it('should delegate unregisterSource to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R2', 100);
      runtime.registerSource(src);
      expect(runtime.unregisterSource('R2')).toBe(true);
    });

    it('should delegate get to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R3', 100, { k: 'v' });
      runtime.registerSource(src);
      expect(runtime.get('k')).toBe('v');
    });

    it('should delegate has to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R4', 100, { k: 'v' });
      runtime.registerSource(src);
      expect(runtime.has('k')).toBe(true);
    });

    it('should delegate getEntry to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R5', 100, { k: 'v' });
      runtime.registerSource(src);
      expect(runtime.getEntry('k')?.sourceName).toBe('R5');
    });

    it('should delegate getAll to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R6', 100, { k: 'v' });
      runtime.registerSource(src);
      expect(runtime.getAll()).toMatchObject({ k: 'v' });
    });

    it('should delegate createSnapshot to provider', () => {
      const runtime = new ConfigurationRuntime();
      const src = new MemoryConfigurationSource('R7', 100, { k: 'v' });
      runtime.registerSource(src);
      const snap = runtime.createSnapshot();
      expect(snap.mergedValues.k).toBe('v');
    });

    it('should include sources and snapshot in provider diagnostics()', () => {
      const provider = new ConfigurationProvider();
      provider.get<string>('test.key', 'val');

      const diag = provider.diagnostics();
      expect(diag.sources).toBeDefined();
      expect(diag.sources?.length).toBeGreaterThan(0);
      expect(diag.snapshot).toBeDefined();
    });

    it('should isolate registered sources between different provider instances', () => {
      const provider1 = new ConfigurationProvider();
      const provider2 = new ConfigurationProvider();

      provider1.registerSource(new MemoryConfigurationSource('P1Source', 100, { k: 1 }));
      provider2.registerSource(new MemoryConfigurationSource('P2Source', 200, { k: 2 }));

      expect(provider1.get('k')).toBe(1);
      expect(provider2.get('k')).toBe(2);
    });

    it('should interact cleanly with lazy singleton helpers', () => {
      const provider = getConfigurationProvider();
      const runtime = getConfigurationRuntime();

      provider.registerSource(new MemoryConfigurationSource('GlobalSrc', 300, { 'g.key': 'g.val' }));
      expect(runtime.get('g.key')).toBe('g.val');
    });
  });
});
