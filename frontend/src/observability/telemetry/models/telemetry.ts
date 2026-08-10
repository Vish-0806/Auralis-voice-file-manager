export const TelemetryType = {
  LOG: 'LOG',
  METRIC: 'METRIC',
  TRACE: 'TRACE',
  EVENT: 'EVENT',
  CUSTOM: 'CUSTOM'
} as const;

export type TelemetryTypeValue = typeof TelemetryType[keyof typeof TelemetryType];

export const Severity = {
  DEBUG: 'DEBUG',
  INFO: 'INFO',
  WARN: 'WARN',
  ERROR: 'ERROR',
  FATAL: 'FATAL'
} as const;

export type SeverityValue = typeof Severity[keyof typeof Severity];

export interface TelemetryRecord {
  readonly id: string;
  readonly timestamp: number;
  readonly type: TelemetryTypeValue;
  readonly source: string;
  readonly name: string;
  readonly severity: SeverityValue;
  readonly attributes?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
  readonly traceId?: string;
  readonly spanId?: string;
  readonly correlationId?: string;
  readonly requestId?: string;
}
