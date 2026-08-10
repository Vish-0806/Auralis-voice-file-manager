import type { TelemetryRecord } from '../models/telemetry';
import type { TelemetryStatistics, TelemetryDiagnostics } from '../models/statistics';
import type { ITelemetryExporter } from './telemetry-exporter';

export interface ITelemetryProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;

  record(record: TelemetryRecord): void;
  recordEvent(name: string, attributes?: Record<string, unknown>, metadata?: Record<string, unknown>): void;
  recordLog(message: string, severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL', attributes?: Record<string, unknown>): void;
  recordMetric(name: string, value: number, attributes?: Record<string, unknown>): void;
  recordTrace(name: string, durationMs: number, attributes?: Record<string, unknown>): void;

  registerExporter(exporter: ITelemetryExporter): void;
  getExporter(name: string): ITelemetryExporter;
  removeExporter(name: string): void;
  listExporters(): ReadonlyArray<ITelemetryExporter>;

  getBufferCapacity(): number;
  setBufferCapacity(capacity: number): void;
  getBufferSize(): number;
  clearBuffer(): void;

  getSamplingRate(): number;
  setSamplingRate(rate: number): void;

  flush(): Promise<void>;
  getStatistics(): TelemetryStatistics;
  getDiagnostics(): TelemetryDiagnostics;
}
