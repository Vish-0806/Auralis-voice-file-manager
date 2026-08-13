import { describe, it, expect } from 'vitest';
import { DiagnosticsProvider } from '../../../src/observability/diagnostics/provider/DiagnosticsProvider';
import { createDiagnosticSourceDescriptor } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('Diagnostics Aggregation Tests', () => {
  it('should aggregate all healthy checks to HEALTHY status and lowest severity', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    provider.registerCheck({
      id: 'c2',
      sourceId: 'src1',
      name: 'Check 2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.WARNING,
      execute: () => DiagnosticStatus.HEALTHY
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.HEALTHY);
    expect(report.overallSeverity).toBe(DiagnosticSeverity.WARNING);
    expect(report.passedCount).toBe(2);
    expect(report.failedCount).toBe(0);
    expect(report.degradedCount).toBe(0);
  });

  it('should aggregate to DEGRADED when at least one check is degraded and none is unhealthy', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    provider.registerCheck({
      id: 'c2',
      sourceId: 'src1',
      name: 'Check 2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.WARNING,
      execute: () => DiagnosticStatus.DEGRADED
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.DEGRADED);
    expect(report.overallSeverity).toBe(DiagnosticSeverity.WARNING);
    expect(report.passedCount).toBe(1);
    expect(report.degradedCount).toBe(1);
    expect(report.failedCount).toBe(0);
  });

  it('should aggregate to UNHEALTHY if any enabled check is unhealthy', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.DEGRADED
    });

    provider.registerCheck({
      id: 'c2',
      sourceId: 'src1',
      name: 'Check 2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.CRITICAL,
      execute: () => DiagnosticStatus.UNHEALTHY
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.UNHEALTHY);
    expect(report.overallSeverity).toBe(DiagnosticSeverity.CRITICAL);
    expect(report.degradedCount).toBe(1);
    expect(report.failedCount).toBe(1);
  });

  it('should ignore disabled checks when evaluating overall health and severity', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    provider.registerCheck({
      id: 'c2',
      sourceId: 'src1',
      name: 'Check 2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.CRITICAL,
      enabled: false,
      execute: () => DiagnosticStatus.UNHEALTHY
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.HEALTHY);
    expect(report.overallSeverity).toBe(DiagnosticSeverity.INFO);
    expect(report.passedCount).toBe(1);
    expect(report.skippedCount).toBe(1);
  });

  it('should return UNKNOWN overall status if there are no enabled checks', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.UNKNOWN);
    expect(report.overallSeverity).toBe(DiagnosticSeverity.INFO);
    expect(report.passedCount).toBe(0);
    expect(report.checkCount).toBe(0);
  });

  it('should dominate severity precedence logically (CRITICAL > ERROR > WARNING > INFO)', async () => {
    const precedence = [
      { id: 'c1', severity: DiagnosticSeverity.INFO },
      { id: 'c2', severity: DiagnosticSeverity.WARNING },
      { id: 'c3', severity: DiagnosticSeverity.ERROR },
      { id: 'c4', severity: DiagnosticSeverity.CRITICAL }
    ];

    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    for (const p of precedence) {
      provider.registerCheck({
        id: p.id,
        sourceId: 'src1',
        name: p.id,
        description: 'desc',
        category: DiagnosticCategory.RUNTIME,
        severity: p.severity,
        execute: () => DiagnosticStatus.HEALTHY
      });
    }

    const report = await provider.run();
    expect(report.overallSeverity).toBe(DiagnosticSeverity.CRITICAL);
  });
});
