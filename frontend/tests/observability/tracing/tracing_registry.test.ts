import { describe, it, expect } from 'vitest';
import {
  TracingRegistry,
  Trace,
  Span
} from '../../../src/observability';

describe('TracingRegistry Tests', () => {
  it('1. should register traces and spans correctly', () => {
    const registry = new TracingRegistry();
    const trace: Trace = {
      traceId: 'trace-id-1',
      name: 't.operation',
      startTime: 1000,
      rootSpanId: 'span-id-1',
      status: 'UNSET',
      spansCount: 1
    };
    const span: Span = {
      spanId: 'span-id-1',
      traceId: 'trace-id-1',
      name: 's.operation',
      kind: 'INTERNAL',
      startTime: 1000,
      status: 'UNSET'
    };

    registry.registerTrace(trace);
    registry.registerSpan(span);

    expect(registry.getTrace('trace-id-1')).not.toBeNull();
    expect(registry.getSpan('span-id-1')).not.toBeNull();
    expect(registry.getTraceCount()).toBe(1);
    expect(registry.getSpanCount()).toBe(1);
  });

  it('2. should cascade delete spans when trace is removed', () => {
    const registry = new TracingRegistry();
    const trace: Trace = {
      traceId: 't1',
      name: 't',
      startTime: 1000,
      rootSpanId: 's1',
      status: 'UNSET',
      spansCount: 1
    };
    const span: Span = {
      spanId: 's1',
      traceId: 't1',
      name: 's',
      kind: 'INTERNAL',
      startTime: 1000,
      status: 'UNSET'
    };

    registry.registerTrace(trace);
    registry.registerSpan(span);

    registry.removeTrace('t1');
    expect(registry.getTrace('t1')).toBeNull();
    expect(registry.getSpan('s1')).toBeNull();
  });

  it('3. should support child querying', () => {
    const registry = new TracingRegistry();
    const trace: Trace = {
      traceId: 't1',
      name: 't',
      startTime: 1000,
      rootSpanId: 'root',
      status: 'UNSET',
      spansCount: 2
    };
    const rootSpan: Span = {
      spanId: 'root',
      traceId: 't1',
      name: 'root',
      kind: 'INTERNAL',
      startTime: 1000,
      status: 'UNSET'
    };
    const childSpan: Span = {
      spanId: 'child',
      traceId: 't1',
      parentSpanId: 'root',
      name: 'child',
      kind: 'INTERNAL',
      startTime: 1010,
      status: 'UNSET'
    };

    registry.registerTrace(trace);
    registry.registerSpan(rootSpan);
    registry.registerSpan(childSpan);

    const children = registry.getChildSpans('root');
    expect(children.length).toBe(1);
    expect(children[0].spanId).toBe('child');
  });
});
