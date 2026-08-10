import type { ITelemetryRuntime } from '../interfaces/telemetry-runtime';
import type { ITelemetryProvider } from '../interfaces/telemetry-provider';
import type { TelemetryRecord } from '../models/telemetry';
import type { TelemetryStatistics, TelemetryDiagnostics } from '../models/statistics';
import type { ITelemetryExporter } from '../interfaces/telemetry-exporter';
import { TelemetryProvider } from '../provider/TelemetryProvider';

export class TelemetryRuntime implements ITelemetryRuntime {
  private readonly _provider: ITelemetryProvider;

  constructor(provider?: ITelemetryProvider) {
    this._provider = provider || new TelemetryProvider();
  }

  public provider(): ITelemetryProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public record(record: TelemetryRecord): void {
    this._provider.record(record);
  }

  public recordEvent(name: string, attributes?: Record<string, unknown>, metadata?: Record<string, unknown>): void {
    this._provider.recordEvent(name, attributes, metadata);
  }

  public recordLog(message: string, severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL', attributes?: Record<string, unknown>): void {
    this._provider.recordLog(message, severity, attributes);
  }

  public recordMetric(name: string, value: number, attributes?: Record<string, unknown>): void {
    this._provider.recordMetric(name, value, attributes);
  }

  public recordTrace(name: string, durationMs: number, attributes?: Record<string, unknown>): void {
    this._provider.recordTrace(name, durationMs, attributes);
  }

  public registerExporter(exporter: ITelemetryExporter): void {
    this._provider.registerExporter(exporter);
  }

  public getExporter(name: string): ITelemetryExporter {
    return this._provider.getExporter(name);
  }

  public removeExporter(name: string): void {
    this._provider.removeExporter(name);
  }

  public listExporters(): ReadonlyArray<ITelemetryExporter> {
    return this._provider.listExporters();
  }

  public getBufferCapacity(): number {
    return this._provider.getBufferCapacity();
  }

  public setBufferCapacity(capacity: number): void {
    this._provider.setBufferCapacity(capacity);
  }

  public getBufferSize(): number {
    return this._provider.getBufferSize();
  }

  public clearBuffer(): void {
    this._provider.clearBuffer();
  }

  public getSamplingRate(): number {
    return this._provider.getSamplingRate();
  }

  public setSamplingRate(rate: number): void {
    this._provider.setSamplingRate(rate);
  }

  public flush(): Promise<void> {
    return this._provider.flush();
  }

  public getStatistics(): TelemetryStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): TelemetryDiagnostics {
    return this._provider.getDiagnostics();
  }
}
