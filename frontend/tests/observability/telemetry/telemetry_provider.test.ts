import { describe, it, expect } from 'vitest';
import {
  TelemetryProvider,
  TelemetryValidationError,
  InMemoryTelemetryExporter
} from '../../../src/observability';

describe('TelemetryProvider Ingestion Tests', () => {
  it('1. should ingest and record valid telemetry records', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    provider.record({
      id: 'rec-1',
      timestamp: Date.now(),
      type: 'LOG',
      source: 'test-source',
      name: 'test.log',
      severity: 'INFO',
      attributes: { k: 'v' }
    });

    const stats = provider.getStatistics();
    expect(stats.recordsAccepted).toBe(1);
    expect(stats.recordsBuffered).toBe(1);
  });

  it('2. should reject invalid record fields', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    expect(() => {
      provider.record({
        id: '',
        timestamp: Date.now(),
        type: 'LOG',
        source: 'test',
        name: 'test',
        severity: 'INFO'
      });
    }).toThrow(TelemetryValidationError);

    expect(() => {
      provider.record({
        id: 'rec-id',
        timestamp: -1,
        type: 'LOG',
        source: 'test',
        name: 'test',
        severity: 'INFO'
      });
    }).toThrow(TelemetryValidationError);
  });

  it('3. should support convenience recording methods', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    provider.recordEvent('click.button', { id: 'btn' });
    provider.recordLog('something happened', 'WARN');
    provider.recordMetric('mem.used', 1024);
    provider.recordTrace('fetch.users', 120);

    const stats = provider.getStatistics();
    expect(stats.recordsAccepted).toBe(4);
  });

  it('4. should clean and redact unsafe credential keys in attributes', async () => {
    const provider = new TelemetryProvider();
    await provider.initialize();

    const exporter = new InMemoryTelemetryExporter();
    provider.registerExporter(exporter);

    provider.recordEvent('login', { password: 'my-password', auth_token: 'secret123', safe_field: 'ok' });
    
    await provider.flush();
    
    const records = exporter.getExportedRecords();
    expect(records.length).toBe(1);
    expect(records[0].attributes?.password).toBe('[REDACTED]');
    expect(records[0].attributes?.auth_token).toBe('[REDACTED]');
    expect(records[0].attributes?.safe_field).toBe('ok');
  });
});
