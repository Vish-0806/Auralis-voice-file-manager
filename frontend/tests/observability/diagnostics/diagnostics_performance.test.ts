import { describe, it, expect } from 'vitest';
import { DiagnosticsProvider } from '../../../src/observability/diagnostics/provider/DiagnosticsProvider';
import { createDiagnosticSourceDescriptor } from '../../../src/observability/diagnostics/factories/diagnosticsFactories';
import { DiagnosticStatus, DiagnosticSeverity, DiagnosticCategory } from '../../../src/observability/diagnostics/models/diagnostic';

describe('Diagnostics Performance Benchmarks', () => {
  it('measures core runtime operations performance', async () => {
    const provider = new DiagnosticsProvider();
    await provider.initialize();

    // Register 10 sources and 50 checks
    for (let i = 0; i < 10; i++) {
      provider.registerSource({
        descriptor: createDiagnosticSourceDescriptor({
          id: `src-${i}`,
          name: `Source ${i}`,
          description: `Description ${i}`
        })
      });

      for (let j = 0; j < 5; j++) {
        provider.registerCheck({
          id: `check-${i}-${j}`,
          sourceId: `src-${i}`,
          name: `Check ${i} ${j}`,
          description: `Desc ${i} ${j}`,
          category: DiagnosticCategory.RUNTIME,
          severity: DiagnosticSeverity.INFO,
          execute: () => DiagnosticStatus.HEALTHY
        });
      }
    }

    // 1. Source lookup benchmark (10,000 runs)
    const t0 = performance.now();
    for (let k = 0; k < 10000; k++) {
      provider.getSource('src-5');
    }
    const t1 = performance.now();
    const sourceLookupTime = (t1 - t0) / 10000;
    console.log(`[PERF] Source Lookup Time: ${sourceLookupTime.toFixed(6)} ms / lookup`);

    // 2. Check lookup benchmark (10,000 runs)
    const t2 = performance.now();
    for (let k = 0; k < 10000; k++) {
      provider.getCheck('check-5-2');
    }
    const t3 = performance.now();
    const checkLookupTime = (t3 - t2) / 10000;
    console.log(`[PERF] Check Lookup Time: ${checkLookupTime.toFixed(6)} ms / lookup`);

    // 3. Report aggregation benchmark (100 runs)
    const t4 = performance.now();
    for (let k = 0; k < 100; k++) {
      await provider.run();
    }
    const t5 = performance.now();
    const reportAggregationTime = (t5 - t4) / 100;
    console.log(`[PERF] Full Run & Report Aggregation Time: ${reportAggregationTime.toFixed(4)} ms / run`);

    // 4. Diagnostics snapshot generation benchmark (1,000 runs)
    const t6 = performance.now();
    for (let k = 0; k < 1000; k++) {
      provider.getDiagnostics();
    }
    const t7 = performance.now();
    const snapshotGenerationTime = (t7 - t6) / 1000;
    console.log(`[PERF] Snapshot Generation Time: ${snapshotGenerationTime.toFixed(6)} ms / snapshot`);

    // Sanity assertions
    expect(sourceLookupTime).toBeLessThan(0.1); // should be sub-microsecond/very fast
    expect(checkLookupTime).toBeLessThan(0.1);
    expect(reportAggregationTime).toBeLessThan(50); // running 50 sync checks should take well under 50ms
    expect(snapshotGenerationTime).toBeLessThan(0.5);
  });
});
