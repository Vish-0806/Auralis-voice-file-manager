import type { IMonitoringProvider } from '../interfaces/monitoring-provider';
import {
  type MonitoringComponent,
  type MonitoringCheck,
  type MonitoringResult,
  type MonitoringStatistics,
  type MonitoringDiagnostics,
  type MonitoringComponentTypeValue,
  freezeDeepSafe
} from '../models/monitoring';
import { MonitorStatus, type MonitoringHealth, type MonitorStatusValue } from '../models/health';
import { MonitoringRuntimeState, type MonitoringRuntimeStateValue } from '../models/runtime';
import { MonitoringRegistry } from '../registry/MonitoringRegistry';
import {
  MonitoringStateError,
  MonitoringInitializationError,
  MonitoringCheckNotFoundError
} from '../errors/MonitoringErrors';
import { createMonitoringResult } from '../factories/monitoringFactories';

export class MonitoringProvider implements IMonitoringProvider {
  private lifecycleState: MonitoringRuntimeStateValue = MonitoringRuntimeState.UNINITIALIZED;
  private readonly registry = new MonitoringRegistry();

  // Statistics counters
  private totalChecks = 0;
  private successfulChecks = 0;
  private degradedChecks = 0;
  private failedChecks = 0;
  private skippedChecks = 0;
  private totalExecutionTimeMs = 0;
  private lastCheckAt?: number;

  private ensureReady(): void {
    if (this.lifecycleState !== MonitoringRuntimeState.READY) {
      throw new MonitoringStateError(`Monitoring provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (this.lifecycleState === MonitoringRuntimeState.READY) {
      return;
    }

    if (
      this.lifecycleState === MonitoringRuntimeState.STOPPING ||
      this.lifecycleState === MonitoringRuntimeState.STOPPED
    ) {
      throw new MonitoringStateError(`Cannot initialize monitoring provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = MonitoringRuntimeState.INITIALIZING;
    try {
      // In-memory initialization
      this.lifecycleState = MonitoringRuntimeState.READY;
    } catch (err: any) {
      this.lifecycleState = MonitoringRuntimeState.ERROR;
      throw new MonitoringInitializationError(`Failed to initialize monitoring provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === MonitoringRuntimeState.STOPPED) {
      return;
    }

    if (this.lifecycleState === MonitoringRuntimeState.UNINITIALIZED) {
      throw new MonitoringStateError('Cannot shutdown monitoring provider: it is not initialized.');
    }

    this.lifecycleState = MonitoringRuntimeState.STOPPING;
    this.lifecycleState = MonitoringRuntimeState.STOPPED;
  }

  public getState(): MonitoringRuntimeStateValue {
    return this.lifecycleState;
  }

  public registerComponent(component: {
    id: string;
    name: string;
    type: MonitoringComponentTypeValue;
    status?: MonitorStatusValue;
    enabled?: boolean;
    metadata?: Record<string, unknown>;
  }): MonitoringComponent {
    this.ensureReady();
    return this.registry.registerComponent(component);
  }

  public unregisterComponent(componentId: string): void {
    this.ensureReady();
    this.registry.unregisterComponent(componentId);
  }

  public getComponent(componentId: string): MonitoringComponent | null {
    this.ensureReady();
    return this.registry.getComponent(componentId);
  }

  public listComponents(): ReadonlyArray<MonitoringComponent> {
    this.ensureReady();
    return this.registry.listComponents();
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
    execute: () => void | Promise<void>;
  }): MonitoringCheck {
    this.ensureReady();
    return this.registry.registerCheck(check);
  }

  public unregisterCheck(checkId: string): void {
    this.ensureReady();
    this.registry.unregisterCheck(checkId);
  }

  public getCheck(checkId: string): MonitoringCheck | null {
    this.ensureReady();
    return this.registry.getCheck(checkId);
  }

  public listChecks(componentId?: string): ReadonlyArray<MonitoringCheck> {
    this.ensureReady();
    return this.registry.listChecks(componentId);
  }

  public async executeCheck(checkId: string): Promise<MonitoringResult> {
    this.ensureReady();
    const check = this.registry.getCheck(checkId);
    if (!check) {
      throw new MonitoringCheckNotFoundError(`Check with ID '${checkId}' not found.`, checkId);
    }

    const startTime = Date.now();
    this.lastCheckAt = startTime;

    if (!check.enabled) {
      this.totalChecks += 1;
      this.skippedChecks += 1;
      const result = createMonitoringResult({
        checkId: check.id,
        componentId: check.componentId,
        status: MonitorStatus.DISABLED,
        startedAt: startTime,
        completedAt: startTime,
        durationMs: 0,
        message: `Check '${check.id}' is disabled.`
      });
      return result;
    }

    let status: MonitorStatusValue = MonitorStatus.HEALTHY;
    let message: string | undefined = undefined;
    let details: unknown = undefined;
    let error: Error | undefined = undefined;

    try {
      const promiseOrValue = check.execute();
      if (promiseOrValue instanceof Promise) {
        const timeoutPromise = new Promise<never>((_, reject) =>
          setTimeout(() => reject(new Error(`Check execution timed out after ${check.timeoutMs}ms.`)), check.timeoutMs)
        );
        const resultValue = await Promise.race([promiseOrValue, timeoutPromise]);
        if (typeof resultValue === 'string' && Object.values(MonitorStatus).includes(resultValue as any)) {
          status = resultValue as MonitorStatusValue;
        }
      } else {
        const resultValue = promiseOrValue;
        if (typeof resultValue === 'string' && Object.values(MonitorStatus).includes(resultValue as any)) {
          status = resultValue as MonitorStatusValue;
        }
      }
    } catch (err: any) {
      error = err instanceof Error ? err : new Error(String(err));
      if (err && typeof err === 'object' && 'status' in err && Object.values(MonitorStatus).includes(err.status)) {
        status = err.status;
      } else {
        status = MonitorStatus.UNHEALTHY;
      }
      message = err.message || String(err);
      details = err.details || undefined;
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Update provider statistics
    this.totalChecks += 1;
    this.totalExecutionTimeMs += duration;

    if (status === MonitorStatus.HEALTHY) {
      this.successfulChecks += 1;
    } else if (status === MonitorStatus.DEGRADED) {
      this.degradedChecks += 1;
    } else if (status === MonitorStatus.UNHEALTHY) {
      this.failedChecks += 1;
    } else {
      this.skippedChecks += 1;
    }

    const result = createMonitoringResult({
      checkId: check.id,
      componentId: check.componentId,
      status,
      startedAt: startTime,
      completedAt: endTime,
      durationMs: duration,
      message,
      details,
      error
    });

    // Update the relevant component status in the registry
    this.updateComponentStatusWithLatest(check.componentId, check.id, status);

    return result;
  }

  public async executeAllChecks(): Promise<ReadonlyArray<MonitoringResult>> {
    this.ensureReady();
    const checks = this.registry.listChecks();
    const results: MonitoringResult[] = [];
    for (const check of checks) {
      const res = await this.executeCheck(check.id);
      results.push(res);
    }
    return Object.freeze(results);
  }

  private readonly checkStatuses = new Map<string, MonitorStatusValue>();

  private updateComponentStatusWithLatest(componentId: string, checkId: string, status: MonitorStatusValue): void {
    this.checkStatuses.set(checkId, status);

    const component = this.registry.getComponent(componentId);
    if (!component) return;

    const componentChecks = this.registry.listChecks(componentId);
    let worstStatus: MonitorStatusValue = MonitorStatus.HEALTHY;
    let hasEvaluated = false;

    for (const check of componentChecks) {
      if (!check.enabled) continue;
      const latest = this.checkStatuses.get(check.id);
      if (latest) {
        hasEvaluated = true;
        if (latest === MonitorStatus.UNHEALTHY) {
          worstStatus = MonitorStatus.UNHEALTHY;
          break;
        } else if (latest === MonitorStatus.DEGRADED) {
          worstStatus = MonitorStatus.DEGRADED;
        }
      }
    }

    if (hasEvaluated) {
      this.registry.updateComponentStatus(componentId, worstStatus);
    }
  }

  public evaluateHealth(): MonitoringHealth {
    this.ensureReady();
    const components = this.registry.listComponents();
    const checks = this.registry.listChecks();

    const registeredComponentCount = components.length;
    const registeredCheckCount = checks.length;

    let healthyComponentCount = 0;
    let degradedComponentCount = 0;
    let unhealthyComponentCount = 0;

    const warnings: string[] = [];

    // Evaluate component status counters
    for (const component of components) {
      if (component.status === MonitorStatus.HEALTHY) {
        healthyComponentCount += 1;
      } else if (component.status === MonitorStatus.DEGRADED) {
        degradedComponentCount += 1;
        warnings.push(`Component '${component.id}' is DEGRADED.`);
      } else if (component.status === MonitorStatus.UNHEALTHY) {
        unhealthyComponentCount += 1;
        warnings.push(`Component '${component.id}' is UNHEALTHY.`);
      }
    }

    let status: MonitorStatusValue = MonitorStatus.HEALTHY;
    const enabledComponents = components.filter(c => c.enabled);

    if (registeredComponentCount === 0) {
      status = MonitorStatus.UNKNOWN;
      warnings.push('No components registered.');
    } else if (enabledComponents.length === 0) {
      status = MonitorStatus.UNKNOWN;
      warnings.push('All components are disabled.');
    } else {
      const activeUnhealthy = enabledComponents.filter(c => c.status === MonitorStatus.UNHEALTHY).length;
      const activeDegraded = enabledComponents.filter(c => c.status === MonitorStatus.DEGRADED).length;

      if (activeUnhealthy > 0) {
        status = MonitorStatus.UNHEALTHY;
      } else if (activeDegraded > 0) {
        status = MonitorStatus.DEGRADED;
      }
    }

    const health: MonitoringHealth = {
      status,
      registeredComponentCount,
      registeredCheckCount,
      healthyComponentCount,
      degradedComponentCount,
      unhealthyComponentCount,
      lastEvaluationAt: Date.now(),
      warnings: Object.freeze(warnings)
    };

    return freezeDeepSafe(health);
  }

  public getStatistics(): MonitoringStatistics {
    this.ensureReady();
    const average = this.totalChecks - this.skippedChecks > 0
      ? this.totalExecutionTimeMs / (this.totalChecks - this.skippedChecks)
      : 0;

    const stats: MonitoringStatistics = {
      totalChecks: this.totalChecks,
      successfulChecks: this.successfulChecks,
      degradedChecks: this.degradedChecks,
      failedChecks: this.failedChecks,
      skippedChecks: this.skippedChecks,
      totalExecutionTimeMs: this.totalExecutionTimeMs,
      averageExecutionTimeMs: average,
      lastCheckAt: this.lastCheckAt
    };

    return freezeDeepSafe(stats);
  }

  public getHealth(): MonitoringHealth {
    this.ensureReady();
    return this.evaluateHealth();
  }

  public getDiagnostics(): MonitoringDiagnostics {
    this.ensureReady();
    const diag: MonitoringDiagnostics = {
      runtimeState: this.lifecycleState,
      componentCount: this.registry.listComponents().length,
      checkCount: this.registry.listChecks().length,
      statistics: this.getStatistics(),
      health: this.getHealth(),
      generatedAt: Date.now()
    };
    return freezeDeepSafe(diag);
  }
}
