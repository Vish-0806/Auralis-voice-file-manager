import { beforeEach, describe, expect, it } from 'vitest';
import {
  PluginRegistry,
  PluginValidator,
  PluginLoader,
  PluginDiagnosticsManager,
  SandboxManager,
  PluginCertifier,
  createPluginManifest,
  createPluginSandbox,
} from '../../src/runtime/plugins';

describe('Phase 16.7 — Production Certification Engine Tests', () => {
  let registry: PluginRegistry;
  let validator: PluginValidator;
  let loader: PluginLoader;
  let diagnostics: PluginDiagnosticsManager;
  let sandboxManager: SandboxManager;
  let certifier: PluginCertifier;

  beforeEach(() => {
    registry = new PluginRegistry();
    validator = new PluginValidator();
    loader = new PluginLoader();
    diagnostics = new PluginDiagnosticsManager(registry, loader);
    sandboxManager = new SandboxManager();
    certifier = new PluginCertifier(registry, validator, diagnostics, sandboxManager);
  });

  describe('1. Certification Scoring & Audits', () => {
    it('should certify a perfectly healthy plugin with a score of 100', async () => {
      const manifest = createPluginManifest({
        id: 'perfect-plugin',
        name: 'Perfect Plugin',
        version: '1.0.0',
        main: 'index.js',
      });
      registry.registerPlugin(manifest);
      sandboxManager.applySandbox('perfect-plugin', createPluginSandbox({ capabilityRestrictions: ['clipboard'] }));

      const report = await certifier.certifyPlugin('perfect-plugin');
      expect(report.certification.certified).toBe(true);
      expect(report.certification.score).toBe(100);
      expect(report.certification.issues.length).toBe(0);
      expect(report.signature).toBeDefined();
    });

    it('should throw an error when certifying a non-existing plugin', async () => {
      await expect(certifier.certifyPlugin('ghost')).rejects.toThrow();
    });

    it('should deduct points and fail certification on validation failures', async () => {
      const manifest = createPluginManifest({
        id: 'faulty-plugin',
        name: 'Faulty',
        version: 'invalid_semver',
        main: '',
      });
      registry.registerPlugin(manifest);

      const report = await certifier.certifyPlugin('faulty-plugin');
      expect(report.certification.certified).toBe(false);
      expect(report.certification.score).toBeLessThan(70);
      expect(report.certification.issues.some(i => i.type === 'validation_error')).toBe(true);
    });

    it('should deduct points if sandboxing is completely missing', async () => {
      const manifest = createPluginManifest({
        id: 'unsafe-plugin',
        name: 'Unsafe Plugin',
        version: '1.0.0',
        main: 'index.js',
      });
      registry.registerPlugin(manifest);

      const report = await certifier.certifyPlugin('unsafe-plugin');
      expect(report.certification.score).toBe(85); // 100 - 15 (no sandbox)
      expect(report.certification.issues.some(i => i.type === 'sandbox_warning')).toBe(true);
    });

    it('should deduct points if telemetry shows high execution failure rates', async () => {
      const manifest = createPluginManifest({
        id: 'buggy-plugin',
        name: 'Buggy Plugin',
        version: '1.0.0',
        main: 'index.js',
      });
      registry.registerPlugin(manifest);
      sandboxManager.applySandbox('buggy-plugin', createPluginSandbox());

      // Simulate executions, low success rate: 1 success, 4 failures (20% success rate)
      diagnostics.recordTelemetry('buggy-plugin', 10, true);
      diagnostics.recordTelemetry('buggy-plugin', 10, false);
      diagnostics.recordTelemetry('buggy-plugin', 10, false);
      diagnostics.recordTelemetry('buggy-plugin', 10, false);
      diagnostics.recordTelemetry('buggy-plugin', 10, false);

      const report = await certifier.certifyPlugin('buggy-plugin');
      expect(report.certification.score).toBe(80); // 100 - 20 (telemetry failure)
      expect(report.certification.issues.some(i => i.type === 'telemetry_warning')).toBe(true);
    });

    it('should aggregate certification statistics and engine health', async () => {
      // Register one good, one bad
      const perfect = createPluginManifest({ id: 'p1', name: 'Perfect', version: '1.0.0', main: 'index.js' });
      const bad = createPluginManifest({ id: 'p2', name: 'Bad', version: 'invalid', main: '' });
      registry.registerPlugin(perfect);
      registry.registerPlugin(bad);
      sandboxManager.applySandbox('p1', createPluginSandbox());

      await certifier.certifyPlugin('p1');
      await certifier.certifyPlugin('p2');

      const stats = certifier.statistics();
      expect(stats.totalRuns).toBe(2);
      expect(stats.passCount).toBe(1);
      expect(stats.failCount).toBe(1);
      expect(stats.averageScore).toBe(77.5); // (100 + 55) / 2 = 77.5

      const health = certifier.health();
      expect(health.healthy).toBe(false); // failure rate is 50% (> 25%)
      expect(health.failureRate).toBe(0.5);
    });
  });
});
