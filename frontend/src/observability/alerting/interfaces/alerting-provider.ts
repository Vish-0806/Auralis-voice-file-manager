import type { AlertRecord } from '../models/alert';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertingRuntimeStateValue } from '../models/runtime';

export interface IAlertingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): AlertingRuntimeStateValue;

  registerAlert(alert: AlertRecord): void;
  getAlert(alertId: string): AlertRecord | null;
  hasAlert(alertId: string): boolean;
  removeAlert(alertId: string): void;
  listAlerts(): ReadonlyArray<AlertRecord>;
  clearAlerts(): void;

  getStatistics(): AlertingStatistics;
  getDiagnostics(): AlertingDiagnostics;
}