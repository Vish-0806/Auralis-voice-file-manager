import { beforeEach, describe, expect, it } from 'vitest';
import { PermissionManager, createPluginPermission } from '../../src/runtime/plugins';

describe('Phase 16.7 — Permission Engine Tests', () => {
  let manager: PermissionManager;

  beforeEach(() => {
    manager = new PermissionManager();
  });

  describe('1. Permission Enforcement', () => {
    it('should grant and evaluate a permission successfully', () => {
      const perm = createPluginPermission({ scope: 'filesystem', required: true });
      manager.grantPermission('my-plugin', perm);

      expect(manager.evaluatePermission('my-plugin', 'filesystem')).toBe(true);
    });

    it('should evaluate non-granted permissions as false', () => {
      expect(manager.evaluatePermission('my-plugin', 'clipboard')).toBe(false);
    });

    it('should revoke a granted permission scope', () => {
      const perm = createPluginPermission({ scope: 'filesystem', required: true });
      manager.grantPermission('my-plugin', perm);
      expect(manager.evaluatePermission('my-plugin', 'filesystem')).toBe(true);

      const revoked = manager.revokePermission('my-plugin', 'filesystem');
      expect(revoked).toBe(true);
      expect(manager.evaluatePermission('my-plugin', 'filesystem')).toBe(false);
    });

    it('should return false when revoking non-existent permission', () => {
      expect(manager.revokePermission('my-plugin', 'ghost')).toBe(false);
    });

    it('should list all permissions granted to a plugin', () => {
      const p1 = createPluginPermission({ scope: 'filesystem', required: true });
      const p2 = createPluginPermission({ scope: 'clipboard', required: true });
      manager.grantPermission('my-plugin', p1);
      manager.grantPermission('my-plugin', p2);

      const list = manager.listPermissions('my-plugin');
      expect(list.length).toBe(2);
      expect(list.some(p => p.scope === 'filesystem')).toBe(true);
      expect(list.some(p => p.scope === 'clipboard')).toBe(true);
    });

    it('should return empty list when listing permissions for unregistered plugin', () => {
      expect(manager.listPermissions('ghost').length).toBe(0);
    });

    it('should clear all permission maps', () => {
      const perm = createPluginPermission({ scope: 'filesystem', required: true });
      manager.grantPermission('my-plugin', perm);
      manager.clear();

      expect(manager.evaluatePermission('my-plugin', 'filesystem')).toBe(false);
    });
  });
});
