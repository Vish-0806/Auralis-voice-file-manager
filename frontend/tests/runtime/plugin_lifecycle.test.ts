import { beforeEach, describe, expect, it } from 'vitest';
import { PluginLifecycleManager, PluginLifecycleState, createPluginState } from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Lifecycle Engine Tests', () => {
  let manager: PluginLifecycleManager;

  beforeEach(() => {
    manager = new PluginLifecycleManager();
  });

  describe('1. Plugin Lifecycle States Transitions', () => {
    it('should initialize a plugin successfully', async () => {
      const state = await manager.initializePlugin('my-plugin', {});
      expect(state.initialized).toBe(true);
      expect(state.lifecycleState).toBe(PluginLifecycleState.INITIALIZED);
    });

    it('should activate an initialized plugin successfully', async () => {
      await manager.initializePlugin('my-plugin', {});
      const act = await manager.activatePlugin('my-plugin');

      expect(act.success).toBe(true);
      expect(act.durationMs).toBeGreaterThanOrEqual(0);
    });

    it('should throw error when activating uninitialized plugin', async () => {
      await expect(manager.activatePlugin('ghost')).rejects.toThrow();
    });

    it('should deactivate an active plugin successfully', async () => {
      await manager.initializePlugin('my-plugin', {});
      await manager.activatePlugin('my-plugin');
      const deact = await manager.deactivatePlugin('my-plugin');

      expect(deact.success).toBe(true);
    });

    it('should deactivate safely if plugin is already inactive', async () => {
      await manager.initializePlugin('my-plugin', {});
      const deact = await manager.deactivatePlugin('my-plugin');
      expect(deact.success).toBe(true);
    });

    it('should dispose a plugin and set state to UNLOADED', async () => {
      await manager.initializePlugin('my-plugin', {});
      await manager.activatePlugin('my-plugin');

      const state = await manager.disposePlugin('my-plugin');
      expect(state.initialized).toBe(false);
      expect(state.activated).toBe(false);
      expect(state.lifecycleState).toBe(PluginLifecycleState.UNLOADED);
    });
  });

  describe('2. Lifecycle Event History Logging', () => {
    it('should keep track of lifecycle state history', async () => {
      await manager.initializePlugin('p1', {});
      await manager.activatePlugin('p1');
      await manager.deactivatePlugin('p1');

      const history = manager.getHistory('p1');
      expect(history.length).toBe(3);
      expect(history[0].state).toBe(PluginLifecycleState.INITIALIZED);
      expect(history[1].state).toBe(PluginLifecycleState.ACTIVATED);
      expect(history[2].state).toBe(PluginLifecycleState.DEACTIVATED);
    });

    it('should retrieve history logs across all plugins', async () => {
      await manager.initializePlugin('p1', {});
      await manager.initializePlugin('p2', {});

      const history = manager.getHistory();
      expect(history.length).toBe(2);
    });

    it('should record manual state transitions using recordState', () => {
      const state = createPluginState({ pluginId: 'p1', lifecycleState: PluginLifecycleState.RESOLVED });
      manager.recordState('p1', state, 'Manually resolved');

      const history = manager.getHistory('p1');
      expect(history.length).toBe(1);
      expect(history[0].state).toBe(PluginLifecycleState.RESOLVED);
      expect(history[0].description).toBe('Manually resolved');
    });

    it('should throw error when disposing non-existent plugin', async () => {
      await expect(manager.disposePlugin('ghost')).rejects.toThrow();
    });

    it('should support restarting/reactivating plugin cleanly', async () => {
      await manager.initializePlugin('p1', {});
      await manager.activatePlugin('p1');
      await manager.deactivatePlugin('p1');
      const actAgain = await manager.activatePlugin('p1');
      expect(actAgain.success).toBe(true);

      const history = manager.getHistory('p1');
      expect(history.length).toBe(4); // init, active, deactive, active
    });
  });
});
