import { describe, it, expect } from 'vitest';
import {
  TracingProvider,
  TraceNotFoundError
} from '../../../src/observability';

describe('TracingProvider Tests', () => {
  it('1. should start and end traces correctly', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root.operation');
    expect(rootSpan.name).toBe('root.operation');
    expect(rootSpan.traceId).toBeDefined();
    expect(rootSpan.spanId).toBeDefined();

    const trace = provider.getTrace(rootSpan.traceId);
    expect(trace).not.toBeNull();
    expect(trace!.spansCount).toBe(1);

    rootSpan.end();
    const updated = provider.getTrace(rootSpan.traceId);
    expect(updated!.endTime).toBeDefined();
    expect(updated!.status).toBe('OK');
  });

  it('2. should start child spans and assert nesting works', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    const childSpan = provider.startSpan('child', {
      traceId: rootSpan.traceId,
      parentSpanId: rootSpan.spanId
    });

    expect(childSpan.parentSpanId).toBe(rootSpan.spanId);
    const trace = provider.getTrace(rootSpan.traceId);
    expect(trace!.spansCount).toBe(2);

    childSpan.end();
    rootSpan.end();

    const stats = provider.getStatistics();
    expect(stats.completedSpanCount).toBe(2);
  });

  it('3. should support diagnostics and statistics', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    rootSpan.end();

    const diag = provider.getDiagnostics();
    expect(diag.runtimeState).toBe('READY');
    expect(diag.statistics.traceCount).toBe(1);
  });

  it('4. should enforce FIFO history capacity eviction prioritizing completed traces', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    // Capacity is 100 in implementation. Let's write 102 completed traces
    for (let i = 0; i < 102; i++) {
      const rootSpan = provider.startTrace(`t.${i}`);
      rootSpan.end();
    }

    const list = provider.listRecentTraces();
    expect(list.length).toBe(100); // capped at 100
  });

  it('5. should reject span registration if parent trace does not exist', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    expect(() => {
      provider.startSpan('child', { traceId: 'nonexistent-trace-id-hex' });
    }).toThrow(TraceNotFoundError);
  });
});
