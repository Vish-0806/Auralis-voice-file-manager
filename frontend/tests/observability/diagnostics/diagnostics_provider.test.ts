import { describe, it, expect } from 'vitest';
import { DiagnosticsProvider } from '../../../src/observability/diagnostics/provider/DiagnosticsProvider';
import { createDiagnosticSourceDescriptor } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory, DiagnosticsRuntimeState } from '../../../src/observability/diagnostics/models/diagnostic';
import { DiagnosticsStateError, DiagnosticSourceNotFoundError, DiagnosticCheckNotFoundError } from '../../../src/observability/diagnostics/errors/DiagnosticsErrors';

describe('DiagnosticsProvider Tests', () => {
  it('should initialize and shutdown correctly validating lifecycle transitions', async () => {
    const provider = new DiagnosticsProvider();
    expect(provider.getState()).toBe(DiagnosticsRuntimeState.UNINITIALIZED);

    await provider.initialize();
    expect(provider.getState()).toBe(DiagnosticsRuntimeState.READY);

    // Idempotent initialize
    await provider.initialize();
    expect(provider.getState()).toBe(DiagnosticsRuntimeState.READY);

    await provider.shutdown();
    expect(provider.getState()).toBe(DiagnosticsRuntimeState.STOPPED);

    // Idempotent shutdown
    await provider.shutdown();
    expect(provider.getState()).toBe(DiagnosticsRuntimeState.STOPPED);

    // Invalid transition: initializing from stopped should throw
    await expect(provider.initialize()).rejects.toThrow(DiagnosticsStateError);
  });

  it('should throw DiagnosticsStateError if executing action when uninitialized or stopped', async () => {
    const provider = new DiagnosticsProvider();
    const source = { descriptor: createDiagnosticSourceDescriptor({ id: 's1', name: 'S1', description: 'D1' }) };

    expect(() => provider.registerSource(source)).toThrow(DiagnosticsStateError);
    await expect(provider.run()).rejects.toThrow(DiagnosticsStateError);

    await provider.initialize();
    provider.registerSource(source);
    await provider.shutdown();

    expect(() => provider.registerSource(source)).toThrow(DiagnosticsStateError);
    await expect(provider.run()).rejects.toThrow(DiagnosticsStateError);
  });

  it('should run all enabled checks and aggregate findings', async () => {
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
      category: DiagnosticCategory.PERFORMANCE,
      severity: DiagnosticSeverity.WARNING,
      execute: () => DiagnosticStatus.DEGRADED
    });

    const report = await provider.run();
    expect(report.overallStatus).toBe(DiagnosticStatus.DEGRADED);
    expect(report.results.length).toBe(2);
    expect(report.passedCount).toBe(1);
    expect(report.degradedCount).toBe(1);

    // Check history and statistics
    expect(provider.getHistory().length).toBe(1);
    const stats = provider.getStatistics();
    expect(stats.totalRuns).toBe(1);
    expect(stats.degradedRuns).toBe(1);
    expect(stats.executedChecks).toBe(2);
  });

  it('should run checks associated with a single source using runSource()', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });
    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src2', name: 'S2', description: 'D2' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    provider.registerCheck({
      id: 'c2',
      sourceId: 'src2',
      name: 'C2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.CRITICAL,
      execute: () => DiagnosticStatus.UNHEALTHY
    });

    const report = await provider.runSource('src1');
    expect(report.overallStatus).toBe(DiagnosticStatus.HEALTHY);
    expect(report.results.length).toBe(1);
    expect(report.results[0].checkId).toBe('c1');
  });

  it('should throw DiagnosticSourceNotFoundError in runSource for non-existent source', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();
    await expect(provider.runSource('non-existent')).rejects.toThrow(DiagnosticSourceNotFoundError);
  });

  it('should run a single check using runCheck()', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    const result = await provider.runCheck('c1');
    expect(result.checkId).toBe('c1');
    expect(result.status).toBe(DiagnosticStatus.HEALTHY);
  });

  it('should throw DiagnosticCheckNotFoundError in runCheck for non-existent check', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();
    await expect(provider.runCheck('non-existent')).rejects.toThrow(DiagnosticCheckNotFoundError);
  });

  it('should maintain bounded history size and support clearing history', async () => {
    const provider = new DiagnosticsProvider({ historyCapacity: 2 });
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });

    await provider.run();
    await provider.run();
    await provider.run(); // 3rd run triggers eviction

    expect(provider.getHistory().length).toBe(2);

    provider.clearHistory();
    expect(provider.getHistory().length).toBe(0);
  });

  it('should safely coordinate concurrent runs without state corruption', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    let runCount = 0;
    provider.registerCheck({
      id: 'c1',
      sourceId: 'src1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: async () => {
        runCount++;
        await new Promise((resolve) => setTimeout(resolve, 20));
      }
    });

    // Trigger multiple concurrent runs
    const p1 = provider.run();
    const p2 = provider.run();
    const p3 = provider.run();

    const [r1, r2, r3] = await Promise.all([p1, p2, p3]);

    expect(runCount).toBe(1); // Execute callback called exactly once
    expect(r1).toBe(r2);
    expect(r2).toBe(r3); // Shared the same report

    expect(provider.getStatistics().totalRuns).toBe(1);
    expect(provider.getHistory().length).toBe(1);
  });
});
