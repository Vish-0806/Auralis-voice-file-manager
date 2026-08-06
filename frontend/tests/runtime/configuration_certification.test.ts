import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationCertifier,
  ConfigurationProvider,
  ConfigurationRuntime,
  createCertificationHealth,
  createCertificationIssue,
  createCertificationReport,
  createCertificationStatistics,
  createConfigurationCertification,
  createConfigurationCertificationSummary,
  createConfigurationDefinition,
  createConfigurationSchema,
  getConfigurationProvider,
  getConfigurationRuntime,
  MemoryConfigurationSource,
  resetConfigurationProvider,
  resetConfigurationRuntime,
} from '../../src/runtime/config';

describe('Phase 16.3.6 — Frontend Configuration Runtime Production Certification', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable CertificationIssue model', () => {
      const issue = createCertificationIssue({
        severity: 'WARNING',
        component: 'Sources',
        message: 'Duplicate source priorities detected.',
        remediation: 'Assign unique priority numbers.',
      });

      expect(issue.severity).toBe('WARNING');
      expect(issue.component).toBe('Sources');
      expect(issue.message).toContain('Duplicate');
      expect(Object.isFrozen(issue)).toBe(true);
    });

    it('should create immutable ConfigurationCertification model', () => {
      const cert = createConfigurationCertification({
        certified: true,
        score: 100,
        environment: 'production',
      });

      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
      expect(cert.environment).toBe('production');
      expect(Object.isFrozen(cert)).toBe(true);
      expect(Object.isFrozen(cert.issues)).toBe(true);
    });

    it('should create immutable ConfigurationCertificationSummary model', () => {
      const summary = createConfigurationCertificationSummary({
        certified: true,
        score: 100,
        totalChecks: 8,
        passedChecks: 8,
      });

      expect(summary.totalChecks).toBe(8);
      expect(summary.passedChecks).toBe(8);
      expect(Object.isFrozen(summary)).toBe(true);
    });

    it('should create immutable CertificationStatistics and CertificationHealth models', () => {
      const stats = createCertificationStatistics({ certificationsRun: 5, passedCertifications: 5, averageScore: 100 });
      expect(stats.certificationsRun).toBe(5);
      expect(stats.averageScore).toBe(100);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createCertificationHealth({ healthy: true, lastCertificationScore: 100 });
      expect(health.healthy).toBe(true);
      expect(health.lastCertificationScore).toBe(100);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable CertificationReport model', () => {
      const cert = createConfigurationCertification();
      const summary = createConfigurationCertificationSummary();
      const provider = new ConfigurationProvider();
      provider.initialize();
      const diag = provider.diagnostics();

      const report = createCertificationReport({
        certification: cert,
        summary,
        diagnostics: diag,
        benchmarkMs: 2.5,
      });

      expect(report.certification).toBe(cert);
      expect(report.summary).toBe(summary);
      expect(report.benchmarkMs).toBe(2.5);
      expect(Object.isFrozen(report)).toBe(true);
    });
  });

  describe('2. ConfigurationCertifier Engine & Verification Checks', () => {
    it('should run certification and return certified status with score 100 when provider is initialized', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();

      const certifier = new ConfigurationCertifier(provider);
      const report = certifier.runCertification();

      expect(report.certification.certified).toBe(true);
      expect(report.certification.score).toBe(100);
      expect(report.summary.passedChecks).toBeGreaterThan(0);
      expect(report.benchmarkMs).toBeGreaterThanOrEqual(0);
    });

    it('should detect uninitialized state as CRITICAL issue and decrease score', () => {
      const provider = new ConfigurationProvider();
      // Uninitialized provider

      const certifier = new ConfigurationCertifier(provider);
      const report = certifier.runCertification();

      expect(report.certification.certified).toBe(false);
      expect(report.certification.score).toBeLessThanOrEqual(50);
      expect(report.certification.issues.some((i) => i.severity === 'CRITICAL')).toBe(true);
    });

    it('should detect duplicate source priorities as WARNING issue', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      provider.registerSource(new MemoryConfigurationSource('S1', 500));
      provider.registerSource(new MemoryConfigurationSource('S2', 500)); // Duplicate priority 500

      const certifier = new ConfigurationCertifier(provider);
      const report = certifier.runCertification();

      expect(report.certification.issues.some((i) => i.component === 'Sources' && i.severity === 'WARNING')).toBe(true);
    });

    it('should detect schema validation failures as ERROR issue', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();

      const schema = createConfigurationSchema({
        schemaName: 'ErrSchema',
        definitions: {
          'req.field': createConfigurationDefinition({ key: 'req.field', expectedType: 'string', required: true }),
        },
      });

      provider.registerSchema(schema);
      // Missing required field 'req.field'

      const certifier = new ConfigurationCertifier(provider);
      const report = certifier.runCertification();

      expect(report.certification.certified).toBe(false);
      expect(report.certification.issues.some((i) => i.component === 'Validator' && i.severity === 'ERROR')).toBe(true);
    });

    it('should track statistics and health telemetry in ConfigurationCertifier', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();

      const certifier = new ConfigurationCertifier(provider);
      certifier.runCertification();

      const stats = certifier.statistics();
      expect(stats.certificationsRun).toBe(1);
      expect(stats.passedCertifications).toBe(1);
      expect(stats.averageScore).toBe(100);

      const health = certifier.health();
      expect(health.healthy).toBe(true);
      expect(health.lastCertificationScore).toBe(100);
    });

    it('should update statistics and health telemetry when certification fails', () => {
      const provider = new ConfigurationProvider();
      // Uninitialized -> fails certification

      const certifier = new ConfigurationCertifier(provider);
      certifier.runCertification();

      const stats = certifier.statistics();
      expect(stats.certificationsRun).toBe(1);
      expect(stats.failedCertifications).toBe(1);

      const health = certifier.health();
      expect(health.healthy).toBe(false);
    });

    it('should return last generated certification report via certificationReport()', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();

      const certifier = new ConfigurationCertifier(provider);
      expect(certifier.certificationReport()).toBeUndefined();

      const report = certifier.runCertification();
      expect(certifier.certificationReport()).toBe(report);
    });
  });

  describe('3. Provider Integration & Runtime Delegation', () => {
    it('should delegate certify(), runCertification(), and certificationReport() through ConfigurationProvider', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();

      const cert = provider.certify();
      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);

      const report = provider.runCertification();
      expect(report).toBeDefined();
      expect(report.summary.certified).toBe(true);

      const lastReport = provider.certificationReport();
      expect(lastReport).toBe(report);
    });

    it('should delegate certification APIs through ConfigurationRuntime coordinator', () => {
      const runtime = new ConfigurationRuntime();
      runtime.initialize();

      const cert = runtime.certify();
      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);

      const report = runtime.runCertification();
      expect(report).toBeDefined();

      const lastReport = runtime.certificationReport();
      expect(lastReport).toBe(report);
    });

    it('should include certification and certificationSummary in provider diagnostics()', () => {
      const provider = new ConfigurationProvider();
      provider.initialize();
      provider.runCertification();

      const diag = provider.diagnostics();
      expect(diag.certification).toBeDefined();
      expect(diag.certification?.certified).toBe(true);
      expect(diag.certificationSummary).toBeDefined();
      expect(diag.certificationSummary?.score).toBe(100);
    });

    it('should certify global singleton runtime helpers cleanly', () => {
      const provider = getConfigurationProvider();
      const runtime = getConfigurationRuntime();

      provider.initialize();

      const cert = runtime.certify();
      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
    });
  });
});
