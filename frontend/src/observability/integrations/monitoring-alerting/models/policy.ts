export interface MonitoringAlertPolicy {
  readonly id: string;
  readonly enabled: boolean;
  readonly componentId?: string;
  readonly checkId?: string;
  readonly source?: string;
  readonly severity?: string;
  readonly ruleId: string;
  readonly metadata?: Record<string, unknown>;
}
