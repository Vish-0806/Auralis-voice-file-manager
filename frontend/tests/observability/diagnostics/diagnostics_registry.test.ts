import { describe, it, expect } from 'vitest';
import { DiagnosticsRegistry } from '../../../src/observability/diagnostics/registry/DiagnosticsRegistry';
import {
  DiagnosticSourceAlreadyExistsError,
  DiagnosticSourceNotFoundError,
  DiagnosticCheckAlreadyExistsError
} from '../../../src/observability/diagnostics/errors/DiagnosticsErrors';
import { createDiagnosticSourceDescriptor, createDiagnosticCheck } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('DiagnosticsRegistry Tests', () => {
  it('should register and retrieve a source successfully', () => {
    const registry = new DiagnosticsRegistry();
    const sourceDescriptor = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'Test Source 1'
    });
    const source = { descriptor: sourceDescriptor };

    registry.registerSource(source);
    expect(registry.hasSource('src1')).toBe(true);
    expect(registry.getSource('src1')).toBe(source);
    expect(registry.listSources()).toContain(source);
  });

  it('should reject duplicate source registrations', () => {
    const registry = new DiagnosticsRegistry();
    const sourceDescriptor = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'Test Source 1'
    });
    const source = { descriptor: sourceDescriptor };

    registry.registerSource(source);
    expect(() => registry.registerSource(source)).toThrow(DiagnosticSourceAlreadyExistsError);
  });

  it('should throw DiagnosticSourceNotFoundError when unregistering non-existent source', () => {
    const registry = new DiagnosticsRegistry();
    expect(() => registry.unregisterSource('non-existent')).toThrow(DiagnosticSourceNotFoundError);
  });

  it('should register and retrieve checks associated with a source', () => {
    const registry = new DiagnosticsRegistry();
    const sourceDescriptor = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'Test Source 1'
    });
    const source = { descriptor: sourceDescriptor };
    registry.registerSource(source);

    const check = createDiagnosticCheck({
      id: 'check1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'Test Check 1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });

    registry.registerCheck(check);
    expect(registry.getCheck('check1')).toBe(check);
    expect(registry.listChecks()).toContain(check);
    expect(registry.getChecksForSource('src1')).toContain(check);
  });

  it('should reject duplicate check registrations', () => {
    const registry = new DiagnosticsRegistry();
    const sourceDescriptor = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'Test Source 1'
    });
    const source = { descriptor: sourceDescriptor };
    registry.registerSource(source);

    const check = createDiagnosticCheck({
      id: 'check1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'Test Check 1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });

    registry.registerCheck(check);
    expect(() => registry.registerCheck(check)).toThrow(DiagnosticCheckAlreadyExistsError);
  });

  it('should reject check registration if associated source is not registered', () => {
    const registry = new DiagnosticsRegistry();
    const check = createDiagnosticCheck({
      id: 'check1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'Test Check 1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });

    expect(() => registry.registerCheck(check)).toThrow(DiagnosticSourceNotFoundError);
  });

  it('should perform cascade check removal when source is unregistered', () => {
    const registry = new DiagnosticsRegistry();
    const sourceDescriptor = createDiagnosticSourceDescriptor({
      id: 'src1',
      name: 'Source 1',
      description: 'Test Source 1'
    });
    const source = { descriptor: sourceDescriptor };
    registry.registerSource(source);

    const check = createDiagnosticCheck({
      id: 'check1',
      sourceId: 'src1',
      name: 'Check 1',
      description: 'Test Check 1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });

    registry.registerCheck(check);
    expect(registry.getCheck('check1')).toBe(check);

    registry.unregisterSource('src1');
    expect(registry.hasSource('src1')).toBe(false);
    expect(registry.getCheck('check1')).toBeNull();
    expect(registry.listChecks().length).toBe(0);
  });

  it('should preserve registration order in list methods', () => {
    const registry = new DiagnosticsRegistry();
    const src1 = { descriptor: createDiagnosticSourceDescriptor({ id: 'src1', name: 'S1', description: 'D1' }) };
    const src2 = { descriptor: createDiagnosticSourceDescriptor({ id: 'src2', name: 'S2', description: 'D2' }) };

    registry.registerSource(src1);
    registry.registerSource(src2);

    expect(registry.listSources()[0]).toBe(src1);
    expect(registry.listSources()[1]).toBe(src2);

    const check1 = createDiagnosticCheck({
      id: 'check1',
      sourceId: 'src1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });
    const check2 = createDiagnosticCheck({
      id: 'check2',
      sourceId: 'src1',
      name: 'C2',
      description: 'D2',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.ERROR,
      execute: () => DiagnosticStatus.HEALTHY
    });

    registry.registerCheck(check1);
    registry.registerCheck(check2);

    expect(registry.listChecks()[0]).toBe(check1);
    expect(registry.listChecks()[1]).toBe(check2);
  });
});
