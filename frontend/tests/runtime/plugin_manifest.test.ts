import { beforeEach, describe, expect, it } from 'vitest';
import { PluginManifestLoader, createPluginManifest } from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Manifest Engine Tests', () => {
  let loader: PluginManifestLoader;

  beforeEach(() => {
    loader = new PluginManifestLoader();
  });

  describe('1. Parsing & Basic Validation', () => {
    it('should parse a valid manifest json', () => {
      const raw = JSON.stringify({
        id: 'test-plugin',
        name: 'Test Plugin',
        version: '1.2.3',
        main: 'index.js',
      });
      const parsed = loader.parse(raw);
      expect(parsed.id).toBe('test-plugin');
      expect(parsed.version).toBe('1.2.3');
    });

    it('should throw an error on invalid json syntax', () => {
      expect(() => loader.parse('{invalid}')).toThrow();
    });

    it('should throw an error if manifest ID is missing', () => {
      expect(() => loader.parse(JSON.stringify({ name: 'name' }))).toThrow();
    });

    it('should check if version is valid SemVer format', () => {
      expect(loader.isValidSemVer('1.0.0')).toBe(true);
      expect(loader.isValidSemVer('1.2.3-alpha.1')).toBe(true);
      expect(loader.isValidSemVer('1.2.3+build.4')).toBe(true);
      expect(loader.isValidSemVer('1.2')).toBe(false);
      expect(loader.isValidSemVer('abc')).toBe(false);
    });

    it('should return errors when validation finds missing fields', () => {
      const manifest = createPluginManifest({
        id: '',
        name: '',
        version: 'invalid_ver',
        main: '',
        dependencies: [{ id: '', versionRange: '', optional: false }],
      });

      const result = loader.validate(manifest);
      expect(result.valid).toBe(false);
      expect(result.issues.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('2. SemVer Range Matching', () => {
    it('should match any version for range *', () => {
      expect(loader.satisfiesRange('1.2.3', '*')).toBe(true);
      expect(loader.satisfiesRange('0.1.0-beta', '*')).toBe(true);
    });

    it('should match caret (^) range requirements', () => {
      expect(loader.satisfiesRange('1.2.3', '^1.2.0')).toBe(true);
      expect(loader.satisfiesRange('1.5.0', '^1.2.0')).toBe(true);
      expect(loader.satisfiesRange('2.0.0', '^1.2.0')).toBe(false);
      expect(loader.satisfiesRange('1.1.0', '^1.2.0')).toBe(false);
    });

    it('should match tilde (~) range requirements', () => {
      expect(loader.satisfiesRange('1.2.3', '~1.2.0')).toBe(true);
      expect(loader.satisfiesRange('1.2.8', '~1.2.0')).toBe(true);
      expect(loader.satisfiesRange('1.3.0', '~1.2.0')).toBe(false);
      expect(loader.satisfiesRange('1.1.9', '~1.2.0')).toBe(false);
    });

    it('should match greater-than-or-equal (>=) range requirements', () => {
      expect(loader.satisfiesRange('1.5.0', '>=1.2.0')).toBe(true);
      expect(loader.satisfiesRange('2.0.0', '>=1.2.0')).toBe(true);
      expect(loader.satisfiesRange('1.1.0', '>=1.2.0')).toBe(false);
    });

    it('should match exact version match', () => {
      expect(loader.satisfiesRange('1.2.3', '1.2.3')).toBe(true);
      expect(loader.satisfiesRange('1.2.3', '=1.2.3')).toBe(true);
      expect(loader.satisfiesRange('1.2.4', '1.2.3')).toBe(false);
    });

    it('should match empty range as true', () => {
      expect(loader.satisfiesRange('1.0.0', '')).toBe(true);
    });

    it('should match carets with 0.x versions strictly', () => {
      // caret for 0.x means major is 0, minor can change if specified? No, in semver ^0.2.3 matches 0.2.x, but not 0.3.0
      expect(loader.satisfiesRange('0.2.5', '^0.2.3')).toBe(true);
      expect(loader.satisfiesRange('0.3.0', '^0.2.3')).toBe(false);
    });
  });

  describe('3. Engine Compatibility', () => {
    it('should verify engine version compatibility correctly', () => {
      const manifest = createPluginManifest({
        id: 'test',
        name: 'Test',
        engineVersion: '^1.0.0',
      });

      const res1 = loader.verifyCompatibility(manifest, '1.2.3');
      expect(res1.compatible).toBe(true);

      const res2 = loader.verifyCompatibility(manifest, '2.0.0');
      expect(res2.compatible).toBe(false);
    });

    it('should evaluate compatibility as true when no engine constraints exist', () => {
      const manifest = createPluginManifest({ id: 'test', name: 'Test' });
      const res = loader.verifyCompatibility(manifest, '1.0.0');
      expect(res.compatible).toBe(true);
    });
  });
});
