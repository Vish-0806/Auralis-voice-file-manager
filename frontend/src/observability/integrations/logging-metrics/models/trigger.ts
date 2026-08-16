import { LogLevelValue } from '../../../logging/models/log';

export interface LoggingMetricTrigger {
  readonly triggerId: string;
  readonly timestamp: number;
  readonly loggerName: string;
  readonly logLevel: LogLevelValue;
  readonly correlationId?: string;
  readonly requestId?: string;
  readonly message: string;
  readonly metadata?: Record<string, unknown>;
  readonly labels: Record<string, string>;
}
