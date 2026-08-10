export interface TelemetryStatistics {
  readonly recordsAccepted: number;
  readonly recordsRejected: number;
  readonly recordsSampled: number;
  readonly recordsBuffered: number;
  readonly recordsEvicted: number;
  readonly recordsExported: number;
  readonly recordsFailed: number;
  readonly batchesCreated: number;
  readonly batchesExported: number;
  readonly exportFailures: number;
  readonly retryAttempts: number;
  readonly exporterCount: number;
  readonly averageExportDuration: number;
}

export interface TelemetryDiagnostics {
  readonly runtimeState: string;
  readonly bufferSize: number;
  readonly bufferCapacity: number;
  readonly exporterCount: number;
  readonly enabledExporterCount: number;
  readonly statistics: TelemetryStatistics;
  readonly generatedTimestamp: number;
}
