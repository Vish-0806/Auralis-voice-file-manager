import {
  MonitoringAlertPolicy,
  MonitoringAlertIntegrationResult,
  MonitoringAlertIntegrationStatistics,
  MonitoringAlertIntegrationDiagnostics
} from '../models';
import { MonitoringResult } from '../../../models/monitoring';

export interface IMonitoringAlertingProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): string;
  getHealth(): string;
  getStatistics(): MonitoringAlertIntegrationStatistics;
  getDiagnostics(): MonitoringAlertIntegrationDiagnostics;

  registerPolicy(policy: MonitoringAlertPolicy): void;
  unregisterPolicy(policyId: string): void;
  getPolicy(policyId: string): MonitoringAlertPolicy | null;
  listPolicies(): ReadonlyArray<MonitoringAlertPolicy>;
  enablePolicy(policyId: string): void;
  disablePolicy(policyId: string): void;

  processResult(result: MonitoringResult): Promise<MonitoringAlertIntegrationResult>;
}
