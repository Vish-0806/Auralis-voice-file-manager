import { describe, it, expect } from 'vitest';
import { DiagnosticsProvider } from '../../../src/observability/diagnostics/provider/DiagnosticsProvider';
import {
  createDiagnosticSourceDescriptor,
  createDiagnosticResult
} from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('Diagnostics Immutability Tests', () => {
  it('should freeze source descriptors and checks returned by factories', () => {
    const desc = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'D1',
      metadata: { test: 'value' }
    });

    expect(Object.isFrozen(desc)).toBe(true);
    expect(Object.isFrozen(desc.metadata)).toBe(true);
    expect(() => {
      (desc as any).name = 'New Name';
    }).toThrow();
    expect(() => {
      (desc.metadata as any).test = 'mutated';
    }).toThrow();
  });

  it('should freeze diagnostic results returned by factories', () => {
    const res = createDiagnosticResult({
      checkId: 'c1',
      sourceId: 'src1',
      status: DiagnosticStatus.HEALTHY,
      severity: DiagnosticSeverity.INFO,
      message: 'success',
      duration: 10,
      timestamp: Date.now(),
      metadata: { key: 'val' },
      error: { name: 'Error', message: 'err' }
    });

    expect(Object.isFrozen(res)).toBe(true);
    expect(Object.isFrozen(res.metadata)).toBe(true);
    expect(Object.isFrozen(res.error)).toBe(true);
    expect(() => {
      (res as any).status = DiagnosticStatus.UNHEALTHY;
    }).toThrow();
  });

  it('should freeze diagnostic reports returned by provider runs', async () => {
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

    const report = await provider.run();
    expect(Object.isFrozen(report)).toBe(true);
    expect(Object.isFrozen(report.results)).toBe(true);
    expect(Object.isFrozen(report.results[0])).toBe(true);
    expect(Object.isFrozen(report.statistics)).toBe(true);

    expect(() => {
      (report as any).overallStatus = DiagnosticStatus.UNHEALTHY;
    }).toThrow();
  });

  it('should freeze report history list and items returned by provider', async () => {
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

    await provider.run();

    const history = provider.getHistory();
    expect(Object.isFrozen(history)).toBe(true);
    expect(Object.isFrozen(history[0])).toBe(true);

    expect(() => {
      (history as any)[0] = null;
    }).toThrow();
  });

  it('should freeze statistics snapshots returned by provider', async () => {
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

    await provider.run();

    const stats = provider.getStatistics();
    expect(Object.isFrozen(stats)).toBe(true);
    expect(() => {
      (stats as any).totalRuns = 999;
    }).toThrow();
  });

  it('should freeze operational snapshot returned by getDiagnostics()', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    provider.registerSource({
      descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' })
    });

    const snap = provider.getDiagnostics();
    expect(Object.isFrozen(snap)).toBe(true);
    expect(Object.isFrozen(snap.statistics)).toBe(true);
    expect(() => {
      (snap as any).historySize = -1;
    }).toThrow();
  });
});
