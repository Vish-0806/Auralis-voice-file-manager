import { beforeEach, describe, expect, it } from 'vitest';
import { PluginRegistry, createPluginManifest, PluginLifecycleState } from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Registry Engine Tests', () => {
  let registry: PluginRegistry;

  beforeEach(() => {
    registry = new PluginRegistry();
  });

  describe('1. Plugin Registration & Removal', () => {
    it('should register a valid plugin manifest', () => {
      const manifest = createPluginManifest({ id: 'test-plugin', name: 'Test Plugin' });
      const reg = registry.registerPlugin(manifest);

      expect(reg.success).toBe(true);
      expect(reg.pluginId).toBe('test-plugin');
      expect(registry.containsPlugin('test-plugin')).toBe(true);
    });

    it('should throw an error when registering a duplicate plugin ID', () => {
      const manifest = createPluginManifest({ id: 'test-plugin', name: 'Test Plugin' });
      registry.registerPlugin(manifest);

      expect(() => registry.registerPlugin(manifest)).toThrow();
    });

    it('should throw an error when manifest lacks ID', () => {
      const manifest = createPluginManifest({ id: '', name: 'Test' });
      expect(() => registry.registerPlugin(manifest)).toThrow();
    });

    it('should remove an existing plugin', () => {
      const manifest = createPluginManifest({ id: 'test-plugin', name: 'Test Plugin' });
      registry.registerPlugin(manifest);

      const removed = registry.removePlugin('test-plugin');
      expect(removed.success).toBe(true);
      expect(registry.containsPlugin('test-plugin')).toBe(false);
    });

    it('should return success = false when removing a non-existing plugin', () => {
      const removed = registry.removePlugin('ghost');
      expect(removed.success).toBe(false);
    });

    it('should support registering multiple distinct plugins', () => {
      registry.registerPlugin(createPluginManifest({ id: 'p1', name: 'P1' }));
      registry.registerPlugin(createPluginManifest({ id: 'p2', name: 'P2' }));
      registry.registerPlugin(createPluginManifest({ id: 'p3', name: 'P3' }));

      expect(registry.listPlugins().length).toBe(3);
    });
  });

  describe('2. Plugin Lookup & Search', () => {
    it('should find a registered plugin descriptor', () => {
      const manifest = createPluginManifest({ id: 'my-plugin', name: 'My Plugin' });
      registry.registerPlugin(manifest);

      const found = registry.findPlugin('my-plugin');
      expect(found).toBeDefined();
      expect(found?.manifest.name).toBe('My Plugin');
    });

    it('should return undefined when looking up unregistered plugin', () => {
      expect(registry.findPlugin('ghost')).toBeUndefined();
    });

    it('should search plugins by name or description (case-insensitive)', () => {
      const plugin1 = createPluginManifest({ id: 'p1', name: 'Voice Manager', description: 'Manages files' });
      const plugin2 = createPluginManifest({ id: 'p2', name: 'Audio Player', description: 'Plays voice recordings' });
      registry.registerPlugin(plugin1);
      registry.registerPlugin(plugin2);

      const results = registry.search('VOICE');
      expect(results.length).toBe(2);

      const results2 = registry.search('PlAyEr');
      expect(results2.length).toBe(1);
      expect(results2[0].id).toBe('p2');
    });

    it('should search plugins by tag/keyword', () => {
      const manifest = createPluginManifest({
        id: 'p1',
        name: 'P1',
        metadata: { keywords: ['audio', 'utility'] },
      });
      registry.registerPlugin(manifest);

      const found = registry.findPluginsByTag('audio');
      expect(found.length).toBe(1);
      expect(found[0].id).toBe('p1');

      expect(registry.findPluginsByTag('other').length).toBe(0);
    });

    it('should search plugins by category capability', () => {
      const manifest = createPluginManifest({
        id: 'p1',
        name: 'P1',
        capabilities: [{ type: 'category', name: 'Editor', details: {} }],
      });
      registry.registerPlugin(manifest);

      const found = registry.findPluginsByCategory('Editor');
      expect(found.length).toBe(1);
      expect(found[0].id).toBe('p1');
    });

    it('should return empty array when searching for keyword not present', () => {
      const results = registry.search('nonexistent');
      expect(results.length).toBe(0);
    });

    it('should filter by tag correctly with multiple keywords', () => {
      const manifest = createPluginManifest({
        id: 'p1',
        name: 'P1',
        metadata: { keywords: ['vocal', 'effects', 'dsp'] },
      });
      registry.registerPlugin(manifest);

      expect(registry.findPluginsByTag('effects').length).toBe(1);
      expect(registry.findPluginsByTag('dsp').length).toBe(1);
      expect(registry.findPluginsByTag('vocal').length).toBe(1);
    });
  });

  describe('3. Plugin State Updates & Registry Telemetry', () => {
    it('should update plugin lifecycle state', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);

      const state = registry.updatePluginState('p1', {
        lifecycleState: PluginLifecycleState.INITIALIZED,
        initialized: true,
      });

      expect(state.lifecycleState).toBe(PluginLifecycleState.INITIALIZED);
      expect(state.initialized).toBe(true);
    });

    it('should throw an error when updating state of unregistered plugin', () => {
      expect(() => registry.updatePluginState('ghost', { initialized: true })).toThrow();
    });

    it('should aggregate registry statistics', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);
      registry.findPlugin('p1');

      const stats = registry.statistics();
      expect(stats.registeredPlugins).toBe(1);
      expect(stats.lookupsCount).toBe(1);
    });

    it('should report registry health evaluation snapshot', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);

      const h1 = registry.health();
      expect(h1.healthy).toBe(true);

      // Fail a plugin and verify registry health drops
      registry.updatePluginState('p1', { lifecycleState: PluginLifecycleState.FAILED, error: 'Initialization panic' });
      const h2 = registry.health();
      expect(h2.healthy).toBe(false);
      expect(h2.issues.length).toBe(1);
    });

    it('should clear registry content', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);
      registry.clear();

      expect(registry.listPlugins().length).toBe(0);
      expect(registry.statistics().registeredPlugins).toBe(0);
    });

    it('should record failed registration attempts in stats', () => {
      const p1 = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(p1);

      // Duplicate attempt
      expect(() => registry.registerPlugin(p1)).toThrow();

      const stats = registry.statistics();
      expect(stats.registrationAttempts).toBe(2);
      expect(stats.failedRegistrations).toBe(1);
    });

    it('should track multiple registry search attempts in stats', () => {
      registry.search('term1');
      registry.search('term2');
      const stats = registry.statistics();
      expect(stats.searchCount).toBe(2);
    });
  });
});
