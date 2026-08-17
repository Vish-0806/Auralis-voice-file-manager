import { AlertSeverityValue } from '../../../alerting/models/severity';
import { AlertLifecycleStateValue } from '../../../alerting/models/lifecycle';
import { TelemetryTypeValue } from '../../../telemetry/models/telemetry';

export interface AlertingTelemetryPolicy {
  readonly id: string;
  readonly enabled: boolean;
  readonly priority: number;
  readonly alertId?: string;
  readonly fingerprint?: string;
  readonly ruleId?: string;
  readonly sourceId?: string;
  readonly lifecycleState?: AlertLifecycleStateValue;
  readonly severity?: AlertSeverityValue;
  readonly status?: string;
  readonly orchestrationStatus?: string;
  readonly notificationStatus?: string;
  readonly isGlobal?: boolean;
  readonly telemetryType: TelemetryTypeValue;
  readonly metadata?: Record<string, unknown>;
  readonly staticAttributes?: Record<string, unknown>;
  readonly samplingRate?: number;
  readonly bypassSamplingOnError?: boolean;
  readonly allowRepeat?: boolean;
}
