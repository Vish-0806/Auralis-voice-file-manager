export const MonitorStatus = {
  UNKNOWN: 'UNKNOWN',
  HEALTHY: 'HEALTHY',
  DEGRADED: 'DEGRADED',
  UNHEALTHY: 'UNHEALTHY',
  DISABLED: 'DISABLED'
} as const;

export type MonitorStatusValue = typeof MonitorStatus[keyof typeof MonitorStatus];

export interface MonitoringHealth {
  readonly status: MonitorStatusValue;
  readonly registeredComponentCount: number;
  readonly registeredCheckCount: number;
  readonly healthyComponentCount: number;
  readonly degradedComponentCount: number;
  readonly unhealthyComponentCount: number;
  readonly lastEvaluationAt: number;
  readonly warnings: ReadonlyArray<string>;
}
