import type { ITelemetryExporter } from '../interfaces/telemetry-exporter';
import type { TelemetryBatch } from '../models/batch';
import type { TelemetryExportResult } from '../models/export';
import type { TelemetryRecord } from '../models/telemetry';
import { TelemetryExporterError } from '../errors/TelemetryErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class InMemoryTelemetryExporter implements ITelemetryExporter {
  public enabled = true;
  private readonly exportedBatches: TelemetryBatch[] = [];
  private shouldFail = false;
  private failErrorMsg = 'Failed to export batch (simulated error).';

  constructor(public readonly name: string = 'InMemoryTelemetryExporter') {}

  public setShouldFail(shouldFail: boolean, message?: string): void {
    this.shouldFail = shouldFail;
    if (message) {
      this.failErrorMsg = message;
    }
  }

  public async export(batch: TelemetryBatch): Promise<TelemetryExportResult> {
    if (!this.enabled) {
      throw new TelemetryExporterError(`Exporter '${this.name}' is disabled.`);
    }

    const start = Date.now();
    
    if (this.shouldFail) {
      return freezeDeepSafe({
        exporter: this.name,
        batchId: batch.batchId,
        attempted: batch.recordCount,
        exported: 0,
        failed: batch.recordCount,
        duration: Date.now() - start,
        success: false,
        error: {
          name: 'TelemetryExporterError',
          message: this.failErrorMsg
        }
      }) as TelemetryExportResult;
    }

    this.exportedBatches.push(batch);

    return freezeDeepSafe({
      exporter: this.name,
      batchId: batch.batchId,
      attempted: batch.recordCount,
      exported: batch.recordCount,
      failed: 0,
      duration: Date.now() - start,
      success: true
    }) as TelemetryExportResult;
  }

  public async flush(): Promise<void> {
    // No-op
  }

  public async shutdown(): Promise<void> {
    this.enabled = false;
  }

  public getExportedBatches(): ReadonlyArray<TelemetryBatch> {
    return freezeDeepSafe([...this.exportedBatches]) as ReadonlyArray<TelemetryBatch>;
  }

  public getExportedRecords(): ReadonlyArray<TelemetryRecord> {
    const records: TelemetryRecord[] = [];
    for (const b of this.exportedBatches) {
      records.push(...b.records);
    }
    return freezeDeepSafe(records) as ReadonlyArray<TelemetryRecord>;
  }

  public clear(): void {
    this.exportedBatches.length = 0;
  }
}
