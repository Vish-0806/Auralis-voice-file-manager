/**
 * Configuration Certifier Engine (Phase 16.3.6).
 *
 * Implements end-to-end verification, dependency validation, source priority uniqueness audit,
 * performance benchmarking, score calculation, issue reporting, and production readiness certification
 * for the Frontend Configuration Runtime.
 */

import {
  CertificationHealth,
  CertificationIssue,
  CertificationReport,
  CertificationStatistics,
  ConfigurationCertification,
  ConfigurationRuntimeState,
  createCertificationHealth,
  createCertificationIssue,
  createCertificationReport,
  createCertificationStatistics,
  createConfigurationCertification,
  createConfigurationCertificationSummary,
} from './models';
import { IConfigurationProvider } from './interfaces';

export class ConfigurationCertifier {
  private readonly _provider: IConfigurationProvider;
  private _lastReport?: CertificationReport;

  private _certificationsRun = 0;
  private _passedCertifications = 0;
  private _failedCertifications = 0;
  private _totalScoreSum = 0;

  constructor(provider: IConfigurationProvider) {
    this._provider = provider;
  }

  public certify(): ConfigurationCertification {
    return this.runCertification().certification;
  }

  public runCertification(): CertificationReport {
    this._certificationsRun++;
    const issues: CertificationIssue[] = [];

    let totalChecks = 0;
    let passedChecks = 0;
    let failedChecks = 0;
    let warningChecks = 0;

    // 1. Runtime State Check
    totalChecks++;
    const state = this._provider.state();
    if (state.runtimeState === ConfigurationRuntimeState.READY) {
      passedChecks++;
    } else {
      failedChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          component: 'RuntimeState',
          message: `Runtime is in state ${state.runtimeState}, expected READY.`,
          remediation: 'Initialize configuration provider before certification.',
        }),
      );
    }

    // 2. Source Registration & Priority Check
    totalChecks++;
    const sources = this._provider.listSources();
    const activeSources = sources.filter((s) => s.enabled);
    if (activeSources.length > 0) {
      passedChecks++;
    } else {
      warningChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'WARNING',
          component: 'Sources',
          message: 'No active configuration sources registered.',
          remediation: 'Register at least one active configuration source.',
        }),
      );
    }

    // Source Priority Uniqueness Check
    totalChecks++;
    const priorities = new Set<number>();
    let duplicatePriority = false;
    for (const src of sources) {
      if (priorities.has(src.priority)) {
        duplicatePriority = true;
        break;
      }
      priorities.add(src.priority);
    }
    if (!duplicatePriority) {
      passedChecks++;
    } else {
      warningChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'WARNING',
          component: 'Sources',
          message: 'Multiple sources share identical priority values.',
          remediation: 'Assign unique priority values to avoid nondeterministic source overrides.',
        }),
      );
    }

    // 3. Schema & Validation Engine Check
    totalChecks++;
    const validationRes = this._provider.validate();
    if (validationRes.valid) {
      passedChecks++;
    } else {
      failedChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'ERROR',
          component: 'Validator',
          message: `Configuration validation failed with ${validationRes.errors.length} errors.`,
          remediation: 'Fix invalid configuration values to satisfy registered schema constraints.',
        }),
      );
    }

    // 4. Resolution Engine Performance Benchmark Check
    totalChecks++;
    const resolveStart = performance ? performance.now() : Date.now();
    for (let i = 0; i < 100; i++) {
      this._provider.getAll();
    }
    const resolveEnd = performance ? performance.now() : Date.now();
    const benchmarkMs = Math.round((resolveEnd - resolveStart) * 100) / 100;

    if (benchmarkMs < 50) {
      passedChecks++;
    } else {
      warningChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'WARNING',
          component: 'ResolutionEngine',
          message: `Resolution benchmark elapsed ${benchmarkMs}ms, exceeding target threshold 50ms.`,
          remediation: 'Optimize source lookup chains and reduce redundant object allocations.',
        }),
      );
    }

    // 5. Active Profile Check
    totalChecks++;
    const activeProf = this._provider.getActiveProfile();
    if (activeProf && activeProf.active) {
      passedChecks++;
    } else {
      failedChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'ERROR',
          component: 'ProfileManager',
          message: 'No active profile currently selected.',
          remediation: 'Activate a valid configuration profile.',
        }),
      );
    }

    // 6. Feature Flag Manager Check
    totalChecks++;
    const fHealth = this._provider.featureHealth();
    if (fHealth.healthy) {
      passedChecks++;
    } else {
      warningChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'WARNING',
          component: 'FeatureFlagManager',
          message: 'Feature flag evaluation reported unhealthy state.',
        }),
      );
    }

    // 7. Sensitive Configuration Redaction Protection Check
    totalChecks++;
    const sHealth = this._provider.sensitiveHealth();
    const diag = this._provider.diagnostics();
    const rawExposedInDiag = JSON.stringify(diag).includes('RAW_SECRET_LEAK_CHECK_FAIL');

    if (sHealth.healthy && !rawExposedInDiag) {
      passedChecks++;
    } else {
      failedChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          component: 'SecureConfigurationManager',
          message: 'Potential raw sensitive value exposure detected in diagnostics output.',
          remediation: 'Ensure all sensitive configuration properties are redacted before serialization.',
        }),
      );
    }

    // 8. Diagnostics Telemetry Aggregation Check
    totalChecks++;
    if (diag.health && diag.statistics && diag.capabilities) {
      passedChecks++;
    } else {
      failedChecks++;
      issues.push(
        createCertificationIssue({
          severity: 'ERROR',
          component: 'Diagnostics',
          message: 'Incomplete diagnostics telemetry reported.',
        }),
      );
    }

    // Compute score out of 100
    const rawScore = Math.max(0, Math.round((passedChecks / totalChecks) * 100));
    const criticals = issues.filter((i) => i.severity === 'CRITICAL').length;
    const errors = issues.filter((i) => i.severity === 'ERROR').length;
    const score = criticals > 0 ? Math.min(rawScore, 50) : errors > 0 ? Math.min(rawScore, 75) : rawScore;

    const certified = score >= 80 && criticals === 0 && errors === 0;

    if (certified) {
      this._passedCertifications++;
    } else {
      this._failedCertifications++;
    }
    this._totalScoreSum += score;

    const certification = createConfigurationCertification({
      certified,
      score,
      environment: this._provider.context().environment,
      issues: Object.freeze(issues),
      certifiedAt: new Date().toISOString(),
    });

    const summary = createConfigurationCertificationSummary({
      certified,
      score,
      totalChecks,
      passedChecks,
      failedChecks,
      warningChecks,
    });

    const report = createCertificationReport({
      certification,
      summary,
      diagnostics: diag,
      benchmarkMs,
      generatedAt: new Date().toISOString(),
    });

    this._lastReport = report;
    return report;
  }

  public certificationReport(): CertificationReport | undefined {
    return this._lastReport;
  }

  public statistics(): CertificationStatistics {
    const avg =
      this._certificationsRun > 0 ? Math.round(this._totalScoreSum / this._certificationsRun) : 100;

    return createCertificationStatistics({
      certificationsRun: this._certificationsRun,
      passedCertifications: this._passedCertifications,
      failedCertifications: this._failedCertifications,
      averageScore: avg,
    });
  }

  public health(): CertificationHealth {
    const lastScore = this._lastReport ? this._lastReport.certification.score : 100;
    const healthy = lastScore >= 80;
    return createCertificationHealth({
      healthy,
      lastCertificationScore: lastScore,
      statusMessage: healthy
        ? 'Configuration runtime is certified and operational.'
        : `Certification failed with score ${lastScore}/100.`,
    });
  }
}
