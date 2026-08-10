import { describe, it, expect } from 'vitest';
import {
  TracingProvider,
  SpanStateError,
  SpanValidationError
} from '../../../src/observability';

describe('Span Instruments Tests', () => {
  it('1. should record attributes and reject invalid types', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    rootSpan.setAttribute('test.key', 'test.val');
    expect(rootSpan.attributes['test.key']).toBe('test.val');

    expect(() => {
      rootSpan.setAttribute('test.bad', () => {}); // function value
    }).toThrow(SpanValidationError);

    expect(() => {
      rootSpan.setAttribute('', 'val'); // empty key
    }).toThrow(SpanValidationError);

    rootSpan.end();
  });

  it('2. should append events and order them deterministically', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    rootSpan.addEvent('ev1', { k: 'v' });
    rootSpan.addEvent('ev2');

    expect(rootSpan.events.length).toBe(2);
    expect(rootSpan.events[0].name).toBe('ev1');
    expect(rootSpan.events[0].attributes?.k).toBe('v');
    expect(rootSpan.events[1].name).toBe('ev2');

    rootSpan.end();
  });

  it('3. should record errors, map structured details, and mark status as ERROR', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    const err = new Error('Database connection failed');
    rootSpan.recordError(err, { component: 'db' });

    expect(rootSpan.status).toBe('ERROR');
    expect(rootSpan.error).toBeDefined();
    expect(rootSpan.error!.message).toBe('Database connection failed');
    
    // Exception event should exist
    const excEvent = rootSpan.events.find(e => e.name === 'exception');
    expect(excEvent).toBeDefined();
    expect(excEvent!.attributes?.['exception.message']).toBe('Database connection failed');
    expect(excEvent!.attributes?.['component']).toBe('db');

    rootSpan.end();
  });

  it('4. should prevent double completion', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    rootSpan.end();

    expect(() => {
      rootSpan.end();
    }).toThrow(SpanStateError);
  });

  it('5. should freeze toModel output', async () => {
    const provider = new TracingProvider();
    await provider.initialize();

    const rootSpan = provider.startTrace('root');
    rootSpan.setAttribute('k', 'v');
    const model = rootSpan.toModel();
    expect(Object.isFrozen(model)).toBe(true);
    expect(Object.isFrozen(model.attributes)).toBe(true);
    rootSpan.end();
  });
});
