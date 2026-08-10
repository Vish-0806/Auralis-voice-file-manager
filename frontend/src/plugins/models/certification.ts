import { freezeDeepSafe } from './dependency';

export const CertificationSeverity = {
  INFO: 'INFO',
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL'
} as const;
export type CertificationSeverityValue = typeof CertificationSeverity[keyof typeof CertificationSeverity];

export const CertificationStatus = {
  PASSED: 'PASSED',
  PASSED_WITH_WARNINGS: 'PASSED_WITH_WARNINGS',
  FAILED: 'FAILED'
} as const;
export type CertificationStatusValue = typeof CertificationStatus[keyof typeof CertificationStatus];

export interface PluginCertificationIssue {
  readonly id: string;
  readonly stage: string;
  readonly severity: CertificationSeverityValue;
  readonly message: string;
  readonly details?: string;
  readonly timestamp: number;
}

export interface PluginCertificationCheck {
  readonly id: string;
  readonly name: string;
  readonly stage: string;
  readonly passed: boolean;
  readonly duration: number; // In milliseconds
  readonly error?: string;
}

export interface PluginCertificationStage {
  readonly id: string;
  readonly name: string;
  readonly checks: ReadonlyArray<PluginCertificationCheck>;
  readonly score: number;
  readonly maxScore: number;
  readonly passed: boolean;
}

export interface PluginCertificationScore {
  readonly rawScore: number;
  readonly maxScore: number;
  readonly percentage: number;
}

export interface PluginCertificationResult {
  readonly targetId: string;
  readonly success: boolean;
  readonly score: number;
  readonly issues: ReadonlyArray<PluginCertificationIssue>;
  readonly checksRun: number;
  readonly duration: number;
}

export interface PluginCertificationSummary {
  readonly status: CertificationStatusValue;
  readonly score: number;
  readonly issueCount: {
    readonly INFO: number;
    readonly LOW: number;
    readonly MEDIUM: number;
    readonly HIGH: number;
    readonly CRITICAL: number;
  };
  readonly stageResults: ReadonlyArray<PluginCertificationStage>;
}

export interface PluginCertificationReport {
  readonly summary: PluginCertificationSummary;
  readonly issues: ReadonlyArray<PluginCertificationIssue>;
  readonly timestamp: number;
  readonly duration: number;
}

export interface PluginCertificationStatistics {
  readonly totalRuns: number;
  readonly passedRuns: number;
  readonly failedRuns: number;
  readonly totalIssuesFound: number;
  readonly averageScore: number;
}

export interface PluginCertificationHealth {
  readonly healthy: boolean;
  readonly score: number;
  readonly criticalIssueCount: number;
  readonly highIssueCount: number;
  readonly totalIssueCount: number;
  readonly warningCount: number;
  readonly lastCertificationTime?: number;
  readonly totalCertificationRuns: number;
  readonly message: string;
}

export interface PluginCertificationDiagnostics {
  readonly statistics: PluginCertificationStatistics;
  readonly health: PluginCertificationHealth;
  readonly lastReport?: PluginCertificationReport;
}

export interface PluginCertificationSnapshot {
  readonly report: PluginCertificationReport;
  readonly statistics: PluginCertificationStatistics;
  readonly health: PluginCertificationHealth;
}

// Helper functions for immutable creation
export function createCertificationResult(input: Omit<PluginCertificationResult, typeof Symbol.toStringTag>): PluginCertificationResult {
  return freezeDeepSafe(input);
}

export function createCertificationReport(input: Omit<PluginCertificationReport, typeof Symbol.toStringTag>): PluginCertificationReport {
  return freezeDeepSafe(input);
}

export function createCertificationStatistics(input: Omit<PluginCertificationStatistics, typeof Symbol.toStringTag>): PluginCertificationStatistics {
  return freezeDeepSafe(input);
}

export function createCertificationHealth(input: Omit<PluginCertificationHealth, typeof Symbol.toStringTag>): PluginCertificationHealth {
  return freezeDeepSafe(input);
}

export function createCertificationDiagnostics(input: Omit<PluginCertificationDiagnostics, typeof Symbol.toStringTag>): PluginCertificationDiagnostics {
  return freezeDeepSafe(input);
}
