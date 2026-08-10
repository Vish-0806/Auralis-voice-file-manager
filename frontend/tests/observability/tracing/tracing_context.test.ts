import { describe, it, expect } from 'vitest';
import {
  TracingProvider,
  TraceContext
} from '../../../src/observability';

describe('Tracing Context Propagation Tests', () => {
  it('1. should create context from span', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    const ctx = provider.createContext(rootSpan);

    expect(ctx.traceId).toBe(rootSpan.traceId);
    expect(ctx.spanId).toBe(rootSpan.spanId);
    expect(ctx.parentSpanId).toBeUndefined();

    rootSpan.end();
  });

  it('2. should inject and extract context cleanly', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const ctx: TraceContext = {
      traceId: 'trace-id-12345',
      spanId: 'span-id-56789',
      parentSpanId: 'parent-id'
    };

    const injected = provider.injectContext(ctx);
    const extracted = provider.extractContext(injected);

    expect(extracted.traceId).toBe('trace-id-12345');
    expect(extracted.spanId).toBe('span-id-56789');
    expect(extracted.parentSpanId).toBe('parent-id');
  });

  it('3. should support using parentSpanId and traceId to link child contexts', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    const parentCtx = provider.createContext(rootSpan);

    const childSpan = provider.startSpan('child', {
      traceId: parentCtx.traceId,
      parentSpanId: parentCtx.spanId
    });

    const childCtx = provider.createContext(childSpan);
    expect(childCtx.traceId).toBe(rootSpan.traceId);
    expect(childCtx.parentSpanId).toBe(rootSpan.spanId);

    childSpan.end();
    rootSpan.end();
  });
});
