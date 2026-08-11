import { describe, it, expect } from 'vitest';
import { DiagnosticsExecutor } from '../../../src/observability/diagnostics/executor/DiagnosticsExecutor';
import { createDiagnosticCheck } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('DiagnosticsExecutor Tests', () => {
  it('should successfully execute a synchronous check returning void', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'sync-void',
      sourceId: 'src1',
      name: 'Sync Void Check',
      description: 'Tests sync execution',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => {}
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.HEALTHY);
    expect(result.duration).toBeGreaterThanOrEqual(0);
    expect(result.error).toBeUndefined();
  });

  it('should successfully execute a synchronous check returning status', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'sync-status',
      sourceId: 'src1',
      name: 'Sync Status Check',
      description: 'Tests sync status return',
      category: DiagnosticCategory.PERFORMANCE,
      severity: DiagnosticSeverity.WARNING,
      execute: () => DiagnosticStatus.DEGRADED
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.DEGRADED);
    expect(result.error).toBeUndefined();
  });

  it('should successfully execute an asynchronous check', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'async-check',
      sourceId: 'src1',
      name: 'Async Check',
      description: 'Tests async execution',
      category: DiagnosticCategory.AVAILABILITY,
      severity: DiagnosticSeverity.ERROR,
      execute: async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return DiagnosticStatus.HEALTHY;
      }
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.HEALTHY);
    expect(result.duration).toBeGreaterThanOrEqual(10);
    expect(result.error).toBeUndefined();
  });

  it('should isolate thrown exceptions and normalize failures', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'failing-check',
      sourceId: 'src1',
      name: 'Failing Check',
      description: 'Throws error',
      category: DiagnosticCategory.SECURITY,
      severity: DiagnosticSeverity.CRITICAL,
      execute: () => {
        throw new Error('Database connection failed');
      }
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.UNHEALTHY);
    expect(result.error).toBeDefined();
    expect(result.error?.name).toBe('Error');
    expect(result.error?.message).toBe('Database connection failed');
    expect(result.error?.stack).toBeDefined();
  });

  it('should respect custom status set in thrown error', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'custom-error-status-check',
      sourceId: 'src1',
      name: 'Custom Status Check',
      description: 'Throws error with custom status',
      category: DiagnosticCategory.SECURITY,
      severity: DiagnosticSeverity.CRITICAL,
      execute: () => {
        const err = new Error('Service degraded') as any;
        err.status = DiagnosticStatus.DEGRADED;
        throw err;
      }
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.DEGRADED);
    expect(result.error?.message).toBe('Service degraded');
  });

  it('should handle timeout when execution takes longer than specified timeout', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'timeout-check',
      sourceId: 'src1',
      name: 'Timeout Check',
      description: 'Takes 100ms with 20ms timeout',
      category: DiagnosticCategory.AVAILABILITY,
      severity: DiagnosticSeverity.ERROR,
      timeout: 20,
      execute: async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return DiagnosticStatus.HEALTHY;
      }
    });

    const result = await executor.execute(check);
    expect(result.status).toBe(DiagnosticStatus.UNHEALTHY);
    expect(result.error).toBeDefined();
    expect(result.error?.name).toBe('DiagnosticTimeoutError');
    expect(result.error?.message).toContain('timed out');
  });

  it('should measure duration accurately', async () => {
    const executor = new DiagnosticsExecutor();
    const check = createDiagnosticCheck({
      id: 'measure-check',
      sourceId: 'src1',
      name: 'Measure Check',
      description: 'Takes 15ms',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: async () => {
        await new Promise((resolve) => setTimeout(resolve, 15));
      }
    });

    const result = await executor.execute(check);
    expect(result.duration).toBeGreaterThanOrEqual(14);
  });
});
