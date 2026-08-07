import { beforeEach, describe, expect, it } from 'vitest';
import { CapabilityManager, createPluginCapability } from '../../src/runtime/plugins';

describe('Phase 16.7 — Capability Manager Engine Tests', () => {
  let manager: CapabilityManager;

  beforeEach(() => {
    manager = new CapabilityManager();
  });

  describe('1. Capability Registration & Querying', () => {
    it('should register a capability for a plugin', () => {
      const cap = createPluginCapability({ type: 'command', name: 'audio.convert', details: { format: 'wav' } });
      manager.registerCapability('my-plugin', cap);

      const resolved = manager.resolveCapability('audio.convert');
      expect(resolved).toBeDefined();
      expect(resolved?.type).toBe('command');
      expect(resolved?.details.format).toBe('wav');
    });

    it('should list capabilities registered by a specific plugin', () => {
      const cap1 = createPluginCapability({ type: 'command', name: 'c1' });
      const cap2 = createPluginCapability({ type: 'view', name: 'v1' });
      manager.registerCapability('p1', cap1);
      manager.registerCapability('p2', cap2);

      const p1Caps = manager.listCapabilities('p1');
      expect(p1Caps.length).toBe(1);
      expect(p1Caps[0].name).toBe('c1');

      const allCaps = manager.listCapabilities();
      expect(allCaps.length).toBe(2);
    });

    it('should return undefined when resolving non-existent capability', () => {
      expect(manager.resolveCapability('ghost')).toBeUndefined();
    });

    it('should remove a registered capability successfully', () => {
      const cap = createPluginCapability({ type: 'command', name: 'c1' });
      manager.registerCapability('p1', cap);

      const removed = manager.removeCapability('p1', 'c1');
      expect(removed).toBe(true);
      expect(manager.resolveCapability('c1')).toBeUndefined();
    });

    it('should return false when removing non-registered capability', () => {
      expect(manager.removeCapability('p1', 'ghost')).toBe(false);
    });

    it('should clear all capability registries', () => {
      const cap = createPluginCapability({ type: 'command', name: 'c1' });
      manager.registerCapability('p1', cap);
      manager.clear();

      expect(manager.listCapabilities().length).toBe(0);
    });

    it('should register multiple capabilities for a single plugin', () => {
      manager.registerCapability('p1', createPluginCapability({ type: 'view', name: 'v1' }));
      manager.registerCapability('p1', createPluginCapability({ type: 'panel', name: 'pn1' }));
      manager.registerCapability('p1', createPluginCapability({ type: 'menu', name: 'm1' }));

      const list = manager.listCapabilities('p1');
      expect(list.length).toBe(3);
    });

    it('should check if details objects of capability are frozen', () => {
      const cap = createPluginCapability({ type: 'command', name: 'c1', details: { value: 42 } });
      manager.registerCapability('p1', cap);
      const res = manager.resolveCapability('c1');

      expect(Object.isFrozen(res)).toBe(true);
      expect(Object.isFrozen(res?.details)).toBe(true);
    });
  });
});
