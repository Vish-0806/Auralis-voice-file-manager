import type { TelemetryRecord } from './telemetry';

export interface TelemetryBatch {
  readonly batchId: string;
  readonly records: ReadonlyArray<TelemetryRecord>;
  readonly createdAt: number;
  readonly size: number;
  readonly recordCount: number;
}
