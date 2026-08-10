import { describe, it, expect } from 'vitest';
import { TelemetryBuffer, TelemetryRecord } from '../../../src/observability';

describe('TelemetryBuffer FIFO Tests', () => {
  it('1. should enqueue and dequeue records', () => {
    const buffer = new TelemetryBuffer(5);
    const rec: TelemetryRecord = {
      id: 'r1',
      timestamp: Date.now(),
      type: 'LOG',
      source: 'test',
      name: 'log',
      severity: 'INFO'
    };

    buffer.enqueue(rec);
    expect(buffer.size()).toBe(1);

    const items = buffer.dequeue(1);
    expect(items.length).toBe(1);
    expect(items[0].id).toBe('r1');
    expect(buffer.size()).toBe(0);
  });

  it('2. should evict oldest records on overflow capacity', () => {
    const buffer = new TelemetryBuffer(3);
    for (let i = 0; i < 4; i++) {
      buffer.enqueue({
        id: `r${i}`,
        timestamp: Date.now(),
        type: 'LOG',
        source: 'test',
        name: 'log',
        severity: 'INFO'
      });
    }

    expect(buffer.size()).toBe(3);
    const peeked = buffer.peek();
    expect(peeked[0].id).toBe('r1'); // r0 got evicted
  });

  it('3. should support resizing capacity dynamically with immediate evictions', () => {
    const buffer = new TelemetryBuffer(5);
    for (let i = 0; i < 5; i++) {
      buffer.enqueue({
        id: `r${i}`,
        timestamp: Date.now(),
        type: 'LOG',
        source: 'test',
        name: 'log',
        severity: 'INFO'
      });
    }

    expect(buffer.size()).toBe(5);
    const { evicted } = buffer.setCapacity(3);
    expect(evicted.length).toBe(2);
    expect(buffer.size()).toBe(3);
    expect(buffer.peek()[0].id).toBe('r2');
  });
});
