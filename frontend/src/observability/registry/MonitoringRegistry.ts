import {
  type MonitoringComponent,
  type MonitoringCheck,
  freezeDeepSafe,
  type MonitoringComponentTypeValue
} from '../models/monitoring';
import { type MonitorStatusValue } from '../models/health';
import {
  createMonitoringComponent,
  createMonitoringCheck
} from '../factories/monitoringFactories';
import {
  MonitoringRegistrationError,
  MonitoringComponentNotFoundError,
  MonitoringCheckNotFoundError
} from '../errors/MonitoringErrors';

export class MonitoringRegistry {
  private readonly components = new Map<string, MonitoringComponent>();
  private readonly checks = new Map<string, MonitoringCheck>();

  public registerComponent(componentInput: {
    id: string;
    name: string;
    type: MonitoringComponentTypeValue;
    status?: MonitorStatusValue;
    enabled?: boolean;
    metadata?: Record<string, unknown>;
  }): MonitoringComponent {
    if (this.components.has(componentInput.id)) {
      throw new MonitoringRegistrationError(`Component with ID '${componentInput.id}' is already registered.`);
    }

    const component = createMonitoringComponent(componentInput);
    this.components.set(component.id, component);
    return component;
  }

  public unregisterComponent(componentId: string): void {
    if (!this.components.has(componentId)) {
      throw new MonitoringComponentNotFoundError(`Component with ID '${componentId}' not found.`, componentId);
    }

    this.components.delete(componentId);

    for (const [checkId, check] of this.checks.entries()) {
      if (check.componentId === componentId) {
        this.checks.delete(checkId);
      }
    }
  }

  public updateComponentStatus(componentId: string, status: MonitorStatusValue): void {
    const component = this.components.get(componentId);
    if (!component) {
      throw new MonitoringComponentNotFoundError(`Component with ID '${componentId}' not found.`, componentId);
    }
    this.components.set(componentId, freezeDeepSafe({
      ...component,
      status,
      lastCheckedAt: Date.now()
    }));
  }

  public getComponent(componentId: string): MonitoringComponent | null {
    return this.components.get(componentId) || null;
  }

  public hasComponent(componentId: string): boolean {
    return this.components.has(componentId);
  }

  public listComponents(): ReadonlyArray<MonitoringComponent> {
    const list = Array.from(this.components.values());
    list.sort((a, b) => a.id.localeCompare(b.id));
    return Object.freeze(list.map(c => freezeDeepSafe(c))) as ReadonlyArray<MonitoringComponent>;
  }

  public registerCheck(checkInput: {
    id: string;
    componentId: string;
    name: string;
    description?: string;
    enabled?: boolean;
    executionOrder?: number;
    timeoutMs?: number;
    metadata?: Record<string, unknown>;
    execute: () => void | Promise<void>;
  }): MonitoringCheck {
    if (this.checks.has(checkInput.id)) {
      throw new MonitoringRegistrationError(`Check with ID '${checkInput.id}' is already registered.`);
    }

    if (!this.components.has(checkInput.componentId)) {
      throw new MonitoringComponentNotFoundError(`Cannot register check '${checkInput.id}' because target component '${checkInput.componentId}' not found.`, checkInput.componentId);
    }

    const check = createMonitoringCheck(checkInput);
    this.checks.set(check.id, check);
    return check;
  }

  public unregisterCheck(checkId: string): void {
    if (!this.checks.has(checkId)) {
      throw new MonitoringCheckNotFoundError(`Check with ID '${checkId}' not found.`, checkId);
    }
    this.checks.delete(checkId);
  }

  public getCheck(checkId: string): MonitoringCheck | null {
    return this.checks.get(checkId) || null;
  }

  public hasCheck(checkId: string): boolean {
    return this.checks.has(checkId);
  }

  public listChecks(componentId?: string): ReadonlyArray<MonitoringCheck> {
    let list = Array.from(this.checks.values());
    if (componentId !== undefined) {
      list = list.filter(c => c.componentId === componentId);
    }
    list.sort((a, b) => {
      if (a.executionOrder !== b.executionOrder) {
        return a.executionOrder - b.executionOrder;
      }
      return a.id.localeCompare(b.id);
    });
    return Object.freeze(list.map(c => freezeDeepSafe(c))) as ReadonlyArray<MonitoringCheck>;
  }

  public clear(): void {
    this.components.clear();
    this.checks.clear();
  }

  public getStatistics(): { componentCount: number; checkCount: number } {
    return freezeDeepSafe({
      componentCount: this.components.size,
      checkCount: this.checks.size
    });
  }
}
