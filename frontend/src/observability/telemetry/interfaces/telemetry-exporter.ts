import type { TelemetryBatch } from '../models/batch';
import type { TelemetryExportResult } from '../models/export';

export interface ITelemetryExporter {
  readonly name: string;
  enabled: boolean;
  export(batch: TelemetryBatch): Promise<TelemetryExportResult>;
  flush(): Promise<void>;
  shutdown(): Promise<void>;
}
