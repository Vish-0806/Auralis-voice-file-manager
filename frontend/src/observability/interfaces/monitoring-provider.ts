import type {
  MonitoringComponent,
  MonitoringCheck,
  MonitoringResult,
  MonitoringStatistics,
  MonitoringDiagnostics,
  MonitoringComponentTypeValue,
  MonitoringCheckCallback
} from '../models/monitoring';
import type { MonitoringHealth, MonitorStatusValue } from '../models/health';
import type { MonitoringRuntimeStateValue } from '../models/runtime';

export interface IMonitoringProvider {
  initialize(): Promise<void>;
  shutdown(): Promise<void>;
  getState(): MonitoringRuntimeStateValue;

  registerComponent(component: {
    id: string;
    name: string;
    type: MonitoringComponentTypeValue;
    status?: MonitorStatusValue;
    enabled?: boolean;
    metadata?: Record<string, unknown>;
  }): MonitoringComponent;
  unregisterComponent(componentId: string): void;
  getComponent(componentId: string): MonitoringComponent | null;
  listComponents(): ReadonlyArray<MonitoringComponent>;

  registerCheck(check: {
    id: string;
    componentId: string;
    name: string;
    description?: string;
    enabled?: boolean;
    executionOrder?: number;
    timeoutMs?: number;
    metadata?: Record<string, unknown>;
    execute: MonitoringCheckCallback;
  }): MonitoringCheck;
  unregisterCheck(checkId: string): void;
  getCheck(checkId: string): MonitoringCheck | null;
  listChecks(componentId?: string): ReadonlyArray<MonitoringCheck>;

  executeCheck(checkId: string): Promise<MonitoringResult>;
  executeAllChecks(): Promise<ReadonlyArray<MonitoringResult>>;

  evaluateHealth(): MonitoringHealth;

  getStatistics(): MonitoringStatistics;
  getHealth(): MonitoringHealth;
  getDiagnostics(): MonitoringDiagnostics;
}
