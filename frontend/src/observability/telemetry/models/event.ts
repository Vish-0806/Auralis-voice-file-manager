import type { TelemetryRecord } from './telemetry';

export interface TelemetryEventRecord extends TelemetryRecord {
  readonly eventName: string;
}
