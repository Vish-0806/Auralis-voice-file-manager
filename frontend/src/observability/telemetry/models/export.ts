import type { StructuredError } from '../../logging/models/log';

export interface TelemetryExportResult {
  readonly exporter: string;
  readonly batchId: string;
  readonly attempted: number;
  readonly exported: number;
  readonly failed: number;
  readonly duration: number;
  readonly success: boolean;
  readonly error?: StructuredError;
}
