import { beforeEach, describe, expect, it } from 'vitest';
import { PluginValidator, createPluginManifest, createPluginCapability, createPluginPermission } from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Validator Engine Tests', () => {
  let validator: PluginValidator;

  beforeEach(() => {
    validator = new PluginValidator();
  });

  describe('1. Schema Validation Checks', () => {
    it('should validate a correct manifest successfully', () => {
      const manifest = createPluginManifest({
        id: 'valid-plugin',
        name: 'Valid Plugin',
        version: '1.0.0',
        main: 'index.js',
      });

      const res = validator.validateManifest(manifest);
      expect(res.valid).toBe(true);
      expect(res.issues.length).toBe(0);
    });

    it('should return errors for invalid manifests', () => {
      const manifest = createPluginManifest({
        id: '',
        name: '',
        version: 'bad_version',
        main: '',
      });

      const res = validator.validateManifest(manifest);
      expect(res.valid).toBe(false);
      expect(res.issues.length).toBeGreaterThan(0);
      expect(res.issues.some(i => i.severity === 'error')).toBe(true);
    });

    it('should validate capabilities and flag invalid properties', () => {
      const c1 = createPluginCapability({ type: 'command', name: 'my.cmd' });
      const c2 = { type: '', name: '' } as any; // Invalid capability

      const res = validator.validateCapabilities('my-plugin', [c1, c2]);
      expect(res.valid).toBe(false);
      expect(res.issues.length).toBe(2);
    });

    it('should validate permissions list and catch empty scope', () => {
      const p1 = createPluginPermission({ scope: 'filesystem' });
      const p2 = { scope: '' } as any; // Invalid permission

      const res = validator.validatePermissions('my-plugin', [p1, p2]);
      expect(res.valid).toBe(false);
      expect(res.issues.length).toBe(1);
    });
  });

  describe('2. Detailed Subsystem Validator Cases', () => {
    it('should catch invalid type in capabilities validation', () => {
      const cap = { type: 123, name: 'invalid-type-name' } as any;
      const res = validator.validateCapabilities('my-plugin', [cap]);
      expect(res.valid).toBe(false);
      expect(res.issues[0].message).toContain('Capability type');
    });

    it('should catch invalid name in capabilities validation', () => {
      const cap = { type: 'command', name: 123 } as any;
      const res = validator.validateCapabilities('my-plugin', [cap]);
      expect(res.valid).toBe(false);
      expect(res.issues[0].message).toContain('Capability name');
    });

    it('should catch invalid scope type in permissions validation', () => {
      const perm = { scope: 123 } as any;
      const res = validator.validatePermissions('my-plugin', [perm]);
      expect(res.valid).toBe(false);
      expect(res.issues[0].message).toContain('Permission scope');
    });

    it('should validate empty capabilities array as valid', () => {
      const res = validator.validateCapabilities('my-plugin', []);
      expect(res.valid).toBe(true);
      expect(res.issues.length).toBe(0);
    });

    it('should validate empty permissions array as valid', () => {
      const res = validator.validatePermissions('my-plugin', []);
      expect(res.valid).toBe(true);
      expect(res.issues.length).toBe(0);
    });

    it('should fail manifest validation if dependencies have invalid structure', () => {
      const manifest = createPluginManifest({
        id: 'p1',
        name: 'P1',
        dependencies: [{ id: '', versionRange: 123 } as any],
      });
      const res = validator.validateManifest(manifest);
      expect(res.valid).toBe(false);
      expect(res.issues.some(i => i.path.includes('dependencies'))).toBe(true);
    });

    it('should pass manifest validation if optional dependencies are fully configured', () => {
      const manifest = createPluginManifest({
        id: 'p1',
        name: 'P1',
        dependencies: [{ id: 'other', versionRange: '^1.0.0', optional: true }],
      });
      const res = validator.validateManifest(manifest);
      expect(res.valid).toBe(true);
    });
  });
});
