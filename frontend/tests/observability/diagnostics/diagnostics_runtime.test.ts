import { describe, it, expect, vi } from 'vitest';
import { DiagnosticsRuntime } from '../../../src/observability/diagnostics/runtime/DiagnosticsRuntime';
import { DiagnosticsProvider } from '../../../src/observability/diagnostics/provider/DiagnosticsProvider';
import { createDiagnosticSourceDescriptor } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('DiagnosticsRuntime Tests', () => {
  it('should instantiate with a default provider', () => {
    const runtime = new DiagnosticsRuntime();
    expect(runtime.provider()).toBeInstanceOf(DiagnosticsProvider);
  });

  it('should instantiate with an injected custom provider', () => {
    const provider = new DiagnosticsProvider();
    const runtime = new DiagnosticsRuntime(provider);
    expect(runtime.provider()).toBe(provider);
  });

  it('should delegate all IDiagnosticsProvider methods to the underlying provider', async () => {
    const provider = new DiagnosticsProvider();
    const runtime = new DiagnosticsRuntime(provider);

    // Spy on provider methods
    const initSpy = vi.spyOn(provider, 'initialize');
    const shutdownSpy = vi.spyOn(provider, 'shutdown');
    const getStateSpy = vi.spyOn(provider, 'getState');
    const regSourceSpy = vi.spyOn(provider, 'registerSource');
    const regCheckSpy = vi.spyOn(provider, 'registerCheck');
    const runSpy = vi.spyOn(provider, 'run');

    await runtime.initialize();
    expect(initSpy).toHaveBeenCalledTimes(1);

    runtime.getState();
    expect(getStateSpy).toHaveBeenCalledTimes(1);

    const source = { descriptor: createDiagnosticSourceDescriptor({ id: 's1', name: 'S1', description: 'D1' }) };
    runtime.registerSource(source);
    expect(regSourceSpy).toHaveBeenCalledWith(source);

    runtime.registerCheck({
      id: 'c1',
      sourceId: 's1',
      name: 'C1',
      description: 'D1',
      category: DiagnosticCategory.RUNTIME,
      severity: DiagnosticSeverity.INFO,
      execute: () => DiagnosticStatus.HEALTHY
    });
    expect(regCheckSpy).toHaveBeenCalledTimes(1);

    await runtime.run();
    expect(runSpy).toHaveBeenCalledTimes(1);

    await runtime.shutdown();
    expect(shutdownSpy).toHaveBeenCalledTimes(1);
  });
});
