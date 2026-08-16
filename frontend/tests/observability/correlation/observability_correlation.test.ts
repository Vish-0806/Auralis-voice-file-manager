import { describe, it, expect } from 'vitest';
import {
  CorrelationRuntime,
  CorrelationProvider,
  CorrelationStateError,
  CorrelationValidationError,
  CorrelationEventError,
  CorrelationLinkError
} from '../../../src/observability';

describe('Cross-Runtime Event Correlation Tests', () => {
  it('1. Default runtime construction & DI', () => {
    const runtime = new CorrelationRuntime();
    expect(runtime.provider()).toBeDefined();

    const provider = new CorrelationProvider({ maxEvents: 50 });
    const runtimeCustom = new CorrelationRuntime(provider);
    expect(runtimeCustom.provider()).toBe(provider);
  });

  it('2. Initial lifecycle state & transitions', async () => {
    const runtime = new CorrelationRuntime();
    expect(runtime.getState()).toBe('UNINITIALIZED');

    await runtime.initialize();
    expect(runtime.getState()).toBe('READY');

    await runtime.shutdown();
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('3. Idempotent initialize & shutdown & promise caching', async () => {
    const runtime = new CorrelationRuntime();

    const p1 = runtime.initialize();
    const p2 = runtime.initialize();
    expect(p1).toBe(p2);
    await p1;

    await runtime.initialize(); // Idempotent
    expect(runtime.getState()).toBe('READY');

    const p3 = runtime.shutdown();
    const p4 = runtime.shutdown();
    expect(p3).toBe(p4);
    await p3;

    await runtime.shutdown(); // Idempotent
    expect(runtime.getState()).toBe('STOPPED');
  });

  it('4. Context creation, validation & propagation', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const ctx = runtime.createContext({
      traceId: 'trace-123',
      requestId: 'req-456',
      source: 'test-suite'
    });

    expect(ctx.correlationId).toBeDefined();
    expect(ctx.traceId).toBe('trace-123');
    expect(ctx.requestId).toBe('req-456');
    expect(ctx.source).toBe('test-suite');
    expect(ctx.timestamp).toBeGreaterThan(0);

    // Validate Context
    expect(() => runtime.validateContext(ctx)).not.toThrow();

    // Child Context Inheritance
    const child = runtime.childContext(ctx, {
      spanId: 'span-999',
      source: 'child-module'
    });

    expect(child.correlationId).toBe(ctx.correlationId); // Preserve parent correlation ID
    expect(child.parentCorrelationId).toBe(ctx.correlationId);
    expect(child.traceId).toBe('trace-123');
    expect(child.requestId).toBe('req-456');
    expect(child.spanId).toBe('span-999');
    expect(child.source).toBe('child-module');
  });

  it('5. Event registration & validation', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const ctx = runtime.createContext({ traceId: 't1' });

    // Invalid Event validations
    expect(() =>
      runtime.recordEvent({
        eventType: '',
        context: ctx,
        sourceSubsystem: 'Logging'
      })
    ).toThrow(CorrelationEventError);

    expect(() =>
      runtime.recordEvent({
        eventType: 'API_CALL',
        context: null as any,
        sourceSubsystem: 'Logging'
      })
    ).toThrow(CorrelationValidationError);

    // Successful registration
    const ev = runtime.recordEvent({
      eventType: 'API_CALL',
      context: ctx,
      sourceSubsystem: 'Logging',
      metadata: { path: '/users' },
      payload: { userId: 'u1' }
    });

    expect(ev.eventId).toBeDefined();
    expect(ev.eventType).toBe('API_CALL');
    expect(ev.sourceSubsystem).toBe('Logging');
    expect(ev.metadata?.path).toBe('/users');
    expect(ev.payload?.userId).toBe('u1');

    // Get Event
    const fetched = runtime.getEvent(ev.eventId);
    expect(fetched).toEqual(ev);
  });

  it('6. Data hygiene: Redacting sensitive fields & normalizing unsafe structures', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const ctx = runtime.createContext();

    const mockReactElement = {
      $$typeof: Symbol.for('react.element'),
      type: 'div',
      props: {}
    };

    const mockDOMNode = {
      nodeType: 1,
      nodeName: 'SPAN',
      innerHTML: 'hello'
    };

    const rawError = new Error('Database connection failed');

    // Circular references setup
    const circularObj: any = { name: 'circular' };
    circularObj.self = circularObj;

    const ev = runtime.recordEvent({
      eventType: 'SENSITIVE_OP',
      context: ctx,
      sourceSubsystem: 'Authentication',
      metadata: {
        password: 'supersecretpassword123',
        api_key: 'key-abc',
        token: 'jwt-token-xyz'
      },
      payload: {
        reactUI: mockReactElement,
        domRef: mockDOMNode,
        error: rawError,
        loop: circularObj
      }
    });

    // Verify metadata redaction
    expect(ev.metadata?.password).toBe('[REDACTED]');
    expect(ev.metadata?.api_key).toBe('[REDACTED]');
    expect(ev.metadata?.token).toBe('[REDACTED]');

    // Verify payload normalization
    expect(ev.payload?.reactUI).toBe('[REACT_ELEMENT]');
    expect(ev.payload?.domRef).toBe('[DOM_NODE_SPAN]');
    expect(ev.payload?.error).toEqual({
      name: 'Error',
      message: 'Database connection failed',
      stack: rawError.stack
    });
    expect((ev.payload?.loop as any).loop).toBeUndefined(); // Circular self reference resolved
    expect((ev.payload?.loop as any).self).toBe('[CIRCULAR]');
  });

  it('7. Queries by correlationId, traceId, requestId, operationId', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const ctx1 = runtime.createContext({ traceId: 'trace-A', requestId: 'req-A' });
    const ctx2 = runtime.createContext({ traceId: 'trace-B', operationId: 'op-B' });

    runtime.recordEvent({ eventType: 'LOG', context: ctx1, sourceSubsystem: 'Logging' });
    runtime.recordEvent({ eventType: 'METRIC', context: ctx1, sourceSubsystem: 'Metrics' });
    runtime.recordEvent({ eventType: 'SPAN', context: ctx2, sourceSubsystem: 'Tracing' });

    // Query by correlationId
    const resCorr = runtime.query({ correlationId: ctx1.correlationId });
    expect(resCorr.length).toBe(2);

    // Query by traceId
    const resTrace = runtime.query({ traceId: 'trace-B' });
    expect(resTrace.length).toBe(1);
    expect(resTrace[0].eventType).toBe('SPAN');

    // Query by requestId
    const resReq = runtime.query({ requestId: 'req-A' });
    expect(resReq.length).toBe(2);

    // Query by operationId
    const resOp = runtime.query({ operationId: 'op-B' });
    expect(resOp.length).toBe(1);

    // Filtering by type/source
    const resFilter = runtime.query({ correlationId: ctx1.correlationId, eventType: 'METRIC' });
    expect(resFilter.length).toBe(1);
    expect(resFilter[0].sourceSubsystem).toBe('Metrics');
  });

  it('8. Time-range filtering', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const ctx = runtime.createContext();

    const ev1 = runtime.recordEvent({ eventType: 'E1', context: ctx, sourceSubsystem: 'S' });
    
    // Simulate time passing (manual query overrides / timestamp checks)
    const startTime = ev1.timestamp - 1000;
    const midTime = ev1.timestamp + 10;
    
    const res1 = runtime.query({ startTime, endTime: midTime });
    expect(res1.length).toBe(1);

    const res2 = runtime.query({ startTime: midTime });
    expect(res2.length).toBe(0);
  });

  it('9. Link creation & lookup', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const link = runtime.addLink({
      sourceId: 'event-01',
      targetId: 'trace-99',
      kind: 'EVENT_TO_TRACE',
      metadata: { token: 'sensitive' } // should be redacted
    });

    expect(link.sourceId).toBe('event-01');
    expect(link.targetId).toBe('trace-99');
    expect(link.kind).toBe('EVENT_TO_TRACE');
    expect(link.metadata?.token).toBe('[REDACTED]');

    // Lookup
    const srcLinks = runtime.getLinksForSource('event-01');
    expect(srcLinks.length).toBe(1);
    expect(srcLinks[0]).toEqual(link);

    const tgtLinks = runtime.getLinksForTarget('trace-99');
    expect(tgtLinks.length).toBe(1);
    expect(tgtLinks[0]).toEqual(link);
  });

  it('10. Bounded FIFO eviction', async () => {
    // Construct provider with max capacity of 3 events and 2 links
    const provider = new CorrelationProvider({ maxEvents: 3, maxLinks: 2 });
    const runtime = new CorrelationRuntime(provider);
    await runtime.initialize();

    const ctx = runtime.createContext();

    runtime.recordEvent({ eventId: 'ev-1', eventType: 'A', context: ctx, sourceSubsystem: 'S' });
    runtime.recordEvent({ eventId: 'ev-2', eventType: 'B', context: ctx, sourceSubsystem: 'S' });
    runtime.recordEvent({ eventId: 'ev-3', eventType: 'C', context: ctx, sourceSubsystem: 'S' });

    // Checking if ev1 exists before we overflow
    expect(runtime.getEvent('ev-1')).not.toBeNull();

    // Trigger FIFO overflow eviction of ev1
    runtime.recordEvent({ eventId: 'ev-4', eventType: 'D', context: ctx, sourceSubsystem: 'S' });

    expect(runtime.getEvent('ev-1')).toBeNull(); // Evicted!
    expect(runtime.getEvent('ev-2')).not.toBeNull();
    expect(runtime.getEvent('ev-4')).not.toBeNull();

    // Check stats evicted counter
    const stats = runtime.getStatistics();
    expect(stats.evictedEvents).toBe(1);

    // Trigger link eviction
    runtime.addLink({ sourceId: 's1', targetId: 't1', kind: 'EVENT_TO_EVENT' });
    runtime.addLink({ sourceId: 's2', targetId: 't2', kind: 'EVENT_TO_EVENT' });
    runtime.addLink({ sourceId: 's3', targetId: 't3', kind: 'EVENT_TO_EVENT' }); // Evicts s1-t1

    expect(runtime.getLinksForSource('s1').length).toBe(0);
    expect(runtime.getLinksForSource('s2').length).toBe(1);
    expect(runtime.getLinksForSource('s3').length).toBe(1);
    expect(runtime.getStatistics().evictedLinks).toBe(1);
  });

  it('11. Diagnostics & deep immutability', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    const diags = runtime.getDiagnostics();
    expect(diags.runtimeState).toBe('READY');
    expect(diags.healthStatus).toBe('HEALTHY');
    expect(Object.isFrozen(diags)).toBe(true);
    expect(Object.isFrozen(diags.statistics)).toBe(true);
  });

  it('12. Invalid lifecycle transitions', async () => {
    const runtime = new CorrelationRuntime();
    (runtime.provider() as any)._state = 'STOPPING';

    await expect(runtime.initialize()).rejects.toThrow(CorrelationStateError);
  });

  it('13. Failure isolation in link validation', async () => {
    const runtime = new CorrelationRuntime();
    await runtime.initialize();

    // Missing sourceId throws CorrelationLinkError
    expect(() =>
      runtime.addLink({
        sourceId: '',
        targetId: 't',
        kind: 'EVENT_TO_EVENT'
      })
    ).toThrow(CorrelationLinkError);

    // Runtime state remains intact
    expect(runtime.getState()).toBe('READY');
  });
});
