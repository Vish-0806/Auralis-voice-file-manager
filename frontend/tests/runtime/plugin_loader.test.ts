import { beforeEach, describe, expect, it } from 'vitest';
import { PluginLoader, createPluginDescriptor, createPluginManifest } from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Loader Engine Tests', () => {
  let loader: PluginLoader;

  beforeEach(() => {
    loader = new PluginLoader();
  });

  describe('1. Loading & Unloading Mechanics', () => {
    it('should load a plugin descriptor and record load state', async () => {
      const manifest = createPluginManifest({ id: 'my-plugin', name: 'My Plugin', main: 'main.js' });
      const desc = createPluginDescriptor({ id: 'my-plugin', manifest });

      const res = await loader.load(desc, {});
      expect(res.success).toBe(true);
      expect(res.pluginId).toBe('my-plugin');
      expect(res.durationMs).toBeGreaterThanOrEqual(0);
      expect(loader.isLoaded('my-plugin')).toBe(true);
    });

    it('should skip loading if plugin is already loaded', async () => {
      const manifest = createPluginManifest({ id: 'my-plugin', name: 'My Plugin' });
      const desc = createPluginDescriptor({ id: 'my-plugin', manifest });

      await loader.load(desc, {});
      const res = await loader.load(desc, {});

      expect(res.success).toBe(true);
      expect(res.durationMs).toBe(0);
    });

    it('should isolate errors when plugin main file is missing or loader fails', async () => {
      const manifest = createPluginManifest({ id: 'invalid-module', name: 'Faulty Plugin' });
      const desc = createPluginDescriptor({ id: 'invalid-module', manifest });

      const res = await loader.load(desc, {});
      expect(res.success).toBe(false);
      expect(res.error).toBeDefined();
    });

    it('should unload an active loaded plugin', async () => {
      const manifest = createPluginManifest({ id: 'my-plugin', name: 'My Plugin' });
      const desc = createPluginDescriptor({ id: 'my-plugin', manifest });

      await loader.load(desc, {});
      const res = await loader.unload('my-plugin');

      expect(res.success).toBe(true);
      expect(loader.isLoaded('my-plugin')).toBe(false);
    });

    it('should return error when unloading a non-loaded plugin', async () => {
      const res = await loader.unload('ghost');
      expect(res.success).toBe(false);
      expect(res.error).toBeDefined();
    });
  });

  describe('2. Reloading & Loader Analytics', () => {
    it('should reload a plugin successfully', async () => {
      const manifest = createPluginManifest({ id: 'my-plugin', name: 'My Plugin' });
      const desc = createPluginDescriptor({ id: 'my-plugin', manifest });

      await loader.load(desc, {});
      const res = await loader.reload(desc, {});

      expect(res.success).toBe(true);
      expect(loader.isLoaded('my-plugin')).toBe(true);
    });

    it('should collect loader statistics and load times', async () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      const desc = createPluginDescriptor({ id: 'p1', manifest });

      await loader.load(desc, {});
      const stats = loader.statistics();

      expect(stats.loadedPluginsCount).toBe(1);
      expect(stats.totalLoads).toBe(1);
      expect(stats.failedLoads).toBe(0);
      expect(stats.averageLoadTimeMs).toBeGreaterThanOrEqual(0);
    });
  });
});
