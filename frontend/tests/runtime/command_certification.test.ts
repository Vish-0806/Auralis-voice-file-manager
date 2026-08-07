import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  CommandCertifier,
  CommandProvider,
  CommandRuntime,
  createCertificationIssue,
  createCommandCertification,
  createCommandCertificationSummary,
  createCertificationStatistics,
  createCertificationHealth,
  createCertificationReport,
  createCertificationStage,
  createCertificationCheck,
  createCertificationScore,
  createCertificationDiagnostics,
  resetCommandRuntime,
  resetCommandProvider,
  getCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.7 — Frontend Command Runtime Production Certification & End-to-End Verification', () => {
  let provider: CommandProvider;
  let certifier: CommandCertifier;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();
    provider = new CommandProvider();
    provider.initialize();
    certifier = new CommandCertifier();
  });

  describe('1. Immutable Certification Models & Factories', () => {
    it('should create immutable CertificationIssue model', () => {
      const issue = createCertificationIssue({ category: 'LIFECYCLE', message: 'Test issue' });
      expect(issue.category).toBe('LIFECYCLE');
      expect(issue.message).toBe('Test issue');
      expect(Object.isFrozen(issue)).toBe(true);
    });

    it('should create immutable CommandCertification model', () => {
      const cert = createCommandCertification({ score: 95, passedChecks: 10, failedChecks: 1 });
      expect(cert.score).toBe(95);
      expect(cert.passedChecks).toBe(10);
      expect(cert.failedChecks).toBe(1);
      expect(Object.isFrozen(cert)).toBe(true);
    });

    it('should create immutable CommandCertificationSummary model', () => {
      const summary = createCommandCertificationSummary({ status: 'PASSED', score: 100 });
      expect(summary.status).toBe('PASSED');
      expect(summary.score).toBe(100);
      expect(Object.isFrozen(summary)).toBe(true);
    });

    it('should create immutable CertificationStatistics model', () => {
      const stats = createCertificationStatistics({ totalCertifications: 5 });
      expect(stats.totalCertifications).toBe(5);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable CertificationHealth model', () => {
      const health = createCertificationHealth({ healthy: true });
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable CertificationReport model', () => {
      const diag = provider.diagnostics();
      const report = createCertificationReport({ diagnostics: diag });
      expect(report.certification).toBeDefined();
      expect(report.summary).toBeDefined();
      expect(Object.isFrozen(report)).toBe(true);
      expect(Object.isFrozen(report.issues)).toBe(true);
    });

    it('should create immutable CertificationStage model', () => {
      const check = createCertificationCheck({ name: 'Check 1' });
      const stage = createCertificationStage({ name: 'Stage 1', checks: [check] });
      expect(stage.name).toBe('Stage 1');
      expect(Object.isFrozen(stage)).toBe(true);
      expect(Object.isFrozen(stage.checks)).toBe(true);
    });

    it('should create immutable CertificationCheck model', () => {
      const check = createCertificationCheck({ name: 'Check 1', status: 'PASSED' });
      expect(check.name).toBe('Check 1');
      expect(check.status).toBe('PASSED');
      expect(Object.isFrozen(check)).toBe(true);
    });

    it('should create immutable CertificationScore model', () => {
      const score = createCertificationScore({ value: 90 });
      expect(score.value).toBe(90);
      expect(Object.isFrozen(score)).toBe(true);
    });

    it('should create immutable CertificationDiagnostics model', () => {
      const stats = createCertificationStatistics();
      const health = createCertificationHealth();
      const diag = createCertificationDiagnostics({ statistics: stats, health });
      expect(diag.statistics).toBeDefined();
      expect(diag.health).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
      expect(Object.isFrozen(diag.stageResults)).toBe(true);
    });
  });

  describe('2. Subsystem Certification Engine', () => {
    it('should run certification and generate a report with 100/100 score', async () => {
      const report = await certifier.runCertification(provider);
      expect(report.certification.certified).toBe(true);
      expect(report.certification.score).toBe(100);
      expect(report.summary.status).toBe('PASSED');
      expect(report.issues.length).toBe(0);
    });

    it('should verify Stage 1: Runtime Lifecycle check succeeds', async () => {
      const report = await certifier.runCertification(provider);
      const stage = report.diagnostics.certificationSummary ? certifier.diagnostics().stageResults[0] : null;
      expect(stage).toBeDefined();
      expect(stage?.status).toBe('PASSED');
      expect(stage?.checks[0].name).toContain('lifecycle');
    });

    it('should verify Stage 2: Registry checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[1];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 3: Execution checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[2];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 4: Pipeline checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[3];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 5: Validator checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[4];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 6: Permission checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[5];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 7: Policy checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[6];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 8: Scheduler checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[7];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 9: Queue checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[8];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 10: Background checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[9];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 11: Diagnostics checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[10];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
    });

    it('should verify Stage 12: Performance Benchmarks checks succeed', async () => {
      await certifier.runCertification(provider);
      const stage = certifier.diagnostics().stageResults[11];
      expect(stage).toBeDefined();
      expect(stage.status).toBe('PASSED');
      expect(stage.checks.length).toBe(3); // Lookup, Validation, Pipeline
    });

    it('should record statistics and health for multiple certification runs', async () => {
      await certifier.runCertification(provider);
      await certifier.runCertification(provider);

      const stats = certifier.certificationStatistics();
      expect(stats.totalCertifications).toBe(2);
      expect(stats.passedCertifications).toBe(2);
      expect(stats.failedCertifications).toBe(0);
      expect(stats.averageScore).toBe(100);

      const health = certifier.certificationHealth();
      expect(health.healthy).toBe(true);
      expect(health.certified).toBe(true);
    });

    it('should generate warning issues and lower score if provider state is uninitialized', async () => {
      vi.spyOn(provider, 'state').mockReturnValue({
        initialized: false,
        runtimeState: 'UNINITIALIZED' as any,
        startedAt: new Date().toISOString(),
      });

      const report = await certifier.runCertification(provider);
      expect(report.certification.certified).toBe(false);
      expect(report.certification.score).toBeLessThan(100);
      expect(report.issues.length).toBeGreaterThan(0);
      expect(report.issues[0].severity).toBe('CRITICAL');
    });
  });

  describe('3. Provider & Runtime Coordinator Integration', () => {
    it('should delegate certify, runCertification, statistics, and health from CommandProvider and CommandRuntime', async () => {
      const runtime = new CommandRuntime(provider);

      const cert = await runtime.certify();
      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);

      const report = await runtime.runCertification();
      expect(report.summary.status).toBe('PASSED');
      
      const rep2 = await runtime.certificationReport();
      expect(rep2.summary.status).toBe('PASSED');

      const stats = runtime.certificationStatistics();
      expect(stats.totalCertifications).toBe(2); // From certify() + runCertification()

      const health = runtime.certificationHealth();
      expect(health.healthy).toBe(true);
    });

    it('should include certification details in diagnostics payload', async () => {
      const runtime = getCommandRuntime();
      runtime.initialize();

      // Diagnostics before running cert
      let diag = runtime.diagnostics();
      expect(diag.certificationStatistics?.totalCertifications).toBe(0);

      // Trigger certification
      await runtime.certify();

      // Diagnostics after running cert
      diag = runtime.diagnostics();
      expect(diag.certification).toBeDefined();
      expect(diag.certification?.score).toBe(100);
      expect(diag.certificationSummary?.status).toBe('PASSED');
      expect(diag.certificationStatistics?.totalCertifications).toBe(1);
      expect(diag.certificationHealth?.certified).toBe(true);
    });
  });
});
