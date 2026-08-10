import type { IMonitoringRuntime } from '../interfaces/monitoring-runtime';
import type { IMonitoringProvider } from '../interfaces/monitoring-provider';
import { MonitoringProvider } from '../provider/MonitoringProvider';
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

export class MonitoringRuntime implements IMonitoringRuntime {
  private readonly _provider: IMonitoringProvider;

  constructor(provider?: IMonitoringProvider) {
    this._provider = provider || new MonitoringProvider();
  }

  public provider(): IMonitoringProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): MonitoringRuntimeStateValue {
    return this._provider.getState();
  }

  public registerComponent(component: {
    id: string;
    name: string;
    type: MonitoringComponentTypeValue;
    status?: MonitorStatusValue;
    enabled?: boolean;
    metadata?: Record<string, unknown>;
  }): MonitoringComponent {
    return this._provider.registerComponent(component);
  }

  public unregisterComponent(componentId: string): void {
    this._provider.unregisterComponent(componentId);
  }

  public getComponent(componentId: string): MonitoringComponent | null {
    return this._provider.getComponent(componentId);
  }

  public listComponents(): ReadonlyArray<MonitoringComponent> {
    return this._provider.listComponents();
  }

  public registerCheck(check: {
    id: string;
    componentId: string;
    name: string;
    description?: string;
    enabled?: boolean;
    executionOrder?: number;
    timeoutMs?: number;
    metadata?: Record<string, unknown>;
    execute: MonitoringCheckCallback;
  }): MonitoringCheck {
    return this._provider.registerCheck(check);
  }

  public unregisterCheck(checkId: string): void {
    this._provider.unregisterCheck(checkId);
  }

  public getCheck(checkId: string): MonitoringCheck | null {
    return this._provider.getCheck(checkId);
  }

  public listChecks(componentId?: string): ReadonlyArray<MonitoringCheck> {
    return this._provider.listChecks(componentId);
  }

  public executeCheck(checkId: string): Promise<MonitoringResult> {
    return this._provider.executeCheck(checkId);
  }

  public executeAllChecks(): Promise<ReadonlyArray<MonitoringResult>> {
    return this._provider.executeAllChecks();
  }

  public evaluateHealth(): MonitoringHealth {
    return this._provider.evaluateHealth();
  }

  public getStatistics(): MonitoringStatistics {
    return this._provider.getStatistics();
  }

  public getHealth(): MonitoringHealth {
    return this._provider.getHealth();
  }

  public getDiagnostics(): MonitoringDiagnostics {
    return this._provider.getDiagnostics();
  }
}
