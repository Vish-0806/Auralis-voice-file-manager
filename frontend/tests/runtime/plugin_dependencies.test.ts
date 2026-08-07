import { beforeEach, describe, expect, it } from 'vitest';
import { DependencyResolver, createPluginDescriptor, createPluginManifest } from '../../src/runtime/plugins';

describe('Phase 16.7 — Dependency Resolver Engine Tests', () => {
  let resolver: DependencyResolver;

  beforeEach(() => {
    resolver = new DependencyResolver();
  });

  describe('1. Dependency Resolution & Ordering', () => {
    it('should determine correct topological load order for linear dependency chain', () => {
      const pC = createPluginDescriptor({ id: 'C', manifest: createPluginManifest({ id: 'C', name: 'C' }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', dependencies: [{ id: 'C', versionRange: '*', optional: false }] }) });
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '*', optional: false }] }) });

      const res = resolver.resolveDependencies([pA, pB, pC]);
      expect(res.resolved).toBe(true);
      expect(res.loadOrder).toEqual(['C', 'B', 'A']);
    });

    it('should determine correct load order for branching dependency graph', () => {
      const pD = createPluginDescriptor({ id: 'D', manifest: createPluginManifest({ id: 'D', name: 'D' }) });
      const pC = createPluginDescriptor({ id: 'C', manifest: createPluginManifest({ id: 'C', name: 'C', dependencies: [{ id: 'D', versionRange: '*', optional: false }] }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', dependencies: [{ id: 'D', versionRange: '*', optional: false }] }) });
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '*', optional: false }, { id: 'C', versionRange: '*', optional: false }] }) });

      const res = resolver.resolveDependencies([pA, pB, pC, pD]);
      expect(res.resolved).toBe(true);
      expect(res.loadOrder.indexOf('D')).toBeLessThan(res.loadOrder.indexOf('B'));
      expect(res.loadOrder.indexOf('D')).toBeLessThan(res.loadOrder.indexOf('C'));
      expect(res.loadOrder.indexOf('B')).toBeLessThan(res.loadOrder.indexOf('A'));
      expect(res.loadOrder.indexOf('C')).toBeLessThan(res.loadOrder.indexOf('A'));
    });
  });

  describe('2. Circular & Missing Dependency Checks', () => {
    it('should throw an error when a circular dependency is detected', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '*', optional: false }] }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', dependencies: [{ id: 'A', versionRange: '*', optional: false }] }) });

      expect(() => resolver.resolveDependencies([pA, pB])).toThrow();
    });

    it('should fail resolution when a required dependency is missing', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'ghost', versionRange: '*', optional: false }] }) });

      const res = resolver.resolveDependencies([pA]);
      expect(res.resolved).toBe(false);
      expect(res.missingRequired.length).toBe(1);
    });

    it('should resolve successfully when an optional dependency is missing', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'ghost', versionRange: '*', optional: true }] }) });

      const res = resolver.resolveDependencies([pA]);
      expect(res.resolved).toBe(true);
      expect(res.missingOptional.length).toBe(1);
    });

    it('should fail resolution when dependency version constraint is violated', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '^2.0.0', optional: false }] }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', version: '1.5.0' }) });

      const res = resolver.resolveDependencies([pA, pB]);
      expect(res.resolved).toBe(false);
      expect(res.missingRequired.length).toBe(1);
    });

    it('should throw circular exception for a loop of length 3', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '*', optional: false }] }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', dependencies: [{ id: 'C', versionRange: '*', optional: false }] }) });
      const pC = createPluginDescriptor({ id: 'C', manifest: createPluginManifest({ id: 'C', name: 'C', dependencies: [{ id: 'A', versionRange: '*', optional: false }] }) });

      expect(() => resolver.resolveDependencies([pA, pB, pC])).toThrow();
    });

    it('should handle optional dependency version mismatch as warning in optional list', () => {
      const pA = createPluginDescriptor({ id: 'A', manifest: createPluginManifest({ id: 'A', name: 'A', dependencies: [{ id: 'B', versionRange: '^2.0.0', optional: true }] }) });
      const pB = createPluginDescriptor({ id: 'B', manifest: createPluginManifest({ id: 'B', name: 'B', version: '1.2.0' }) });

      const res = resolver.resolveDependencies([pA, pB]);
      expect(res.resolved).toBe(true);
      expect(res.missingOptional.length).toBe(1);
      expect(res.missingOptional[0]).toContain('requires B @ ^2.0.0, but found 1.2.0');
    });
  });
});
