import type { ITelemetryProvider } from '../interfaces/telemetry-provider';
import type { ITelemetryExporter } from '../interfaces/telemetry-exporter';
import { type TelemetryRecord, TelemetryType, Severity } from '../models/telemetry';
import type { TelemetryBatch } from '../models/batch';
import type { TelemetryStatistics, TelemetryDiagnostics } from '../models/statistics';
import { TelemetryRegistry } from '../registry/TelemetryRegistry';
import { TelemetryBuffer } from '../buffer/TelemetryBuffer';
import {
  TelemetryStateError,
  TelemetryRuntimeError,
  TelemetryValidationError
} from '../errors/TelemetryErrors';
import {
  validateRecordId,
  validateTimestamp,
  validateTelemetryType,
  validateSeverity,
  cleanUnsafeAttributes,
  shouldSampleRecord
} from '../factories/telemetryFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class TelemetryProvider implements ITelemetryProvider {
  private lifecycleState = 'UNINITIALIZED';
  private readonly registry = new TelemetryRegistry();
  private readonly buffer = new TelemetryBuffer();
  
  private samplingRate = 1.0;
  private keepErrors = true;
  private maxBatchRecords = 50;
  private maxRetries = 3;

  private recordsAccepted = 0;
  private recordsRejected = 0;
  private recordsSampled = 0;
  private recordsEvicted = 0;
  private recordsExported = 0;
  private recordsFailed = 0;
  private batchesCreated = 0;
  private batchesExported = 0;
  private exportFailures = 0;
  private retryAttempts = 0;
  private totalExportDuration = 0;
  private completedExportCount = 0;

  private isFlushing = false;
  private currentFlushPromise: Promise<void> | null = null;
  private batchIdCounter = 0;
  private recordIdCounter = 0;

  private ensureReady(): void {
    if (this.lifecycleState !== 'READY' && this.lifecycleState !== 'FLUSHING') {
      throw new TelemetryStateError(`Telemetry provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (this.lifecycleState === 'READY') {
      return;
    }
    if (this.lifecycleState === 'INITIALIZING' || this.lifecycleState === 'STOPPING' || this.lifecycleState === 'STOPPED') {
      throw new TelemetryStateError(`Cannot initialize telemetry provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = 'INITIALIZING';
    try {
      this.lifecycleState = 'READY';
    } catch (err: any) {
      this.lifecycleState = 'ERROR';
      throw new TelemetryRuntimeError(`Failed to initialize telemetry provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === 'STOPPED') {
      return;
    }
    if (this.lifecycleState === 'UNINITIALIZED') {
      throw new TelemetryStateError('Cannot shutdown telemetry provider: it is not initialized.');
    }

    this.lifecycleState = 'STOPPING';
    try {
      await this.flush();
      const exporters = this.registry.list();
      for (const exporter of exporters) {
        try {
          await exporter.shutdown();
        } catch {
          // Isolate exporter shutdown failures
        }
      }
      this.buffer.clear();
    } finally {
      this.lifecycleState = 'STOPPED';
    }
  }

  public getState(): string {
    return this.lifecycleState;
  }

  public record(record: TelemetryRecord): void {
    this.ensureReady();
    if (!record) {
      throw new TelemetryValidationError('Record cannot be null or undefined.');
    }

    validateRecordId(record.id);
    validateTimestamp(record.timestamp);
    validateTelemetryType(record.type);
    validateSeverity(record.severity);

    let keep = true;
    if (this.samplingRate < 1.0) {
      const isError = record.severity === 'ERROR' || record.severity === 'FATAL';
      if (isError && this.keepErrors) {
        keep = true;
      } else {
        keep = shouldSampleRecord(record.id, this.samplingRate);
      }
    }

    if (!keep) {
      this.recordsSampled += 1;
      this.recordsRejected += 1;
      return;
    }

    const cleanedAttrs = cleanUnsafeAttributes(record.attributes);
    const normalized: TelemetryRecord = {
      ...record,
      attributes: cleanedAttrs
    };

    const { evicted } = this.buffer.enqueue(normalized);
    this.recordsAccepted += 1;
    this.recordsEvicted += evicted.length;

    if (this.buffer.size() >= this.maxBatchRecords) {
      this.flush().catch(() => {});
    }
  }

  private generateId(): string {
    this.recordIdCounter += 1;
    return `rec_${Date.now()}_${this.recordIdCounter}_${Math.random().toString(36).substring(2, 7)}`;
  }

  public recordEvent(name: string, attributes?: Record<string, unknown>, metadata?: Record<string, unknown>): void {
    const record: TelemetryRecord = {
      id: this.generateId(),
      timestamp: Date.now(),
      type: TelemetryType.EVENT,
      source: 'telemetry-provider',
      name,
      severity: Severity.INFO,
      attributes,
      metadata
    };
    this.record(record);
  }

  public recordLog(message: string, severity: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'FATAL', attributes?: Record<string, unknown>): void {
    const record: TelemetryRecord = {
      id: this.generateId(),
      timestamp: Date.now(),
      type: TelemetryType.LOG,
      source: 'telemetry-provider',
      name: 'log_message',
      severity,
      attributes: { ...attributes, message }
    };
    this.record(record);
  }

  public recordMetric(name: string, value: number, attributes?: Record<string, unknown>): void {
    const record: TelemetryRecord = {
      id: this.generateId(),
      timestamp: Date.now(),
      type: TelemetryType.METRIC,
      source: 'telemetry-provider',
      name,
      severity: Severity.INFO,
      attributes: { ...attributes, value }
    };
    this.record(record);
  }

  public recordTrace(name: string, durationMs: number, attributes?: Record<string, unknown>): void {
    const record: TelemetryRecord = {
      id: this.generateId(),
      timestamp: Date.now(),
      type: TelemetryType.TRACE,
      source: 'telemetry-provider',
      name,
      severity: Severity.INFO,
      attributes: { ...attributes, durationMs }
    };
    this.record(record);
  }

  public registerExporter(exporter: ITelemetryExporter): void {
    this.ensureReady();
    this.registry.register(exporter);
  }

  public getExporter(name: string): ITelemetryExporter {
    this.ensureReady();
    return this.registry.get(name);
  }

  public removeExporter(name: string): void {
    this.ensureReady();
    this.registry.remove(name);
  }

  public listExporters(): ReadonlyArray<ITelemetryExporter> {
    this.ensureReady();
    return this.registry.list();
  }

  public getBufferCapacity(): number {
    this.ensureReady();
    return this.buffer.getCapacity();
  }

  public setBufferCapacity(capacity: number): void {
    this.ensureReady();
    const { evicted } = this.buffer.setCapacity(capacity);
    this.recordsEvicted += evicted.length;
  }

  public getBufferSize(): number {
    this.ensureReady();
    return this.buffer.size();
  }

  public clearBuffer(): void {
    this.ensureReady();
    this.buffer.clear();
  }

  public getSamplingRate(): number {
    this.ensureReady();
    return this.samplingRate;
  }

  public setSamplingRate(rate: number): void {
    this.ensureReady();
    if (typeof rate !== 'number' || isNaN(rate) || rate < 0 || rate > 1) {
      throw new TelemetryValidationError('Sampling rate must be between 0.0 and 1.0.');
    }
    this.samplingRate = rate;
  }

  private createBatch(records: TelemetryRecord[]): TelemetryBatch {
    this.batchIdCounter += 1;
    return freezeDeepSafe({
      batchId: `batch_${Date.now()}_${this.batchIdCounter}`,
      records,
      createdAt: Date.now(),
      size: JSON.stringify(records).length,
      recordCount: records.length
    }) as TelemetryBatch;
  }

  public async flush(): Promise<void> {
    if (this.lifecycleState !== 'READY' && this.lifecycleState !== 'FLUSHING' && this.lifecycleState !== 'STOPPING') {
      throw new TelemetryStateError(`Cannot flush in state: ${this.lifecycleState}`);
    }
    if (this.isFlushing) {
      return this.currentFlushPromise || Promise.resolve();
    }

    this.isFlushing = true;
    this.currentFlushPromise = (async () => {
      const prevState = this.lifecycleState;
      this.lifecycleState = 'FLUSHING';
      try {
        while (this.buffer.size() > 0) {
          const records = this.buffer.dequeue(this.maxBatchRecords);
          if (records.length === 0) break;

          const batch = this.createBatch(records);
          this.batchesCreated += 1;

          const exporters = this.registry.list().filter(e => e.enabled);
          if (exporters.length === 0) {
            this.recordsFailed += records.length;
            continue;
          }

          const exportPromises = exporters.map(async exporter => {
            let attempt = 0;
            let result: any;
            while (attempt <= this.maxRetries) {
              if (attempt > 0) {
                this.retryAttempts += 1;
              }
              try {
                const start = Date.now();
                result = await exporter.export(batch);
                const duration = Date.now() - start;
                this.totalExportDuration += duration;
                this.completedExportCount += 1;

                if (result.success) {
                  return { success: true, count: batch.recordCount };
                }
              } catch {
                // Suppress exporter failures during batch sending
              }
              attempt += 1;
            }
            return { success: false, count: batch.recordCount };
          });

          const results = await Promise.all(exportPromises);
          
          let anyFailure = false;
          for (const res of results) {
            if (res.success) {
              this.recordsExported += res.count;
            } else {
              anyFailure = true;
              this.recordsFailed += res.count;
              this.exportFailures += 1;
            }
          }

          if (!anyFailure) {
            this.batchesExported += 1;
          }
        }
      } finally {
        this.lifecycleState = prevState;
        this.isFlushing = false;
        this.currentFlushPromise = null;
      }
    })();

    return this.currentFlushPromise;
  }

  public getStatistics(): TelemetryStatistics {
    this.ensureReady();
    const average = this.completedExportCount > 0 ? this.totalExportDuration / this.completedExportCount : 0;
    return freezeDeepSafe({
      recordsAccepted: this.recordsAccepted,
      recordsRejected: this.recordsRejected,
      recordsSampled: this.recordsSampled,
      recordsBuffered: this.buffer.size(),
      recordsEvicted: this.recordsEvicted,
      recordsExported: this.recordsExported,
      recordsFailed: this.recordsFailed,
      batchesCreated: this.batchesCreated,
      batchesExported: this.batchesExported,
      exportFailures: this.exportFailures,
      retryAttempts: this.retryAttempts,
      exporterCount: this.registry.getExporterCount(),
      averageExportDuration: average
    }) as TelemetryStatistics;
  }

  public getDiagnostics(): TelemetryDiagnostics {
    this.ensureReady();
    const enabledExporterCount = this.registry.list().filter(e => e.enabled).length;
    return freezeDeepSafe({
      runtimeState: this.lifecycleState,
      bufferSize: this.buffer.size(),
      bufferCapacity: this.buffer.getCapacity(),
      exporterCount: this.registry.getExporterCount(),
      enabledExporterCount,
      statistics: this.getStatistics(),
      generatedTimestamp: Date.now()
    }) as TelemetryDiagnostics;
  }
}
