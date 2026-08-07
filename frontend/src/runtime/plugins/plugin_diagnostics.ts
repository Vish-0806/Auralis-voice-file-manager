/**
 * Diagnostics & Telemetry Aggregator Engine (Phase 16.7).
 *
 * Implements IPluginDiagnostics to aggregate logs, statistics, health evaluations,
 * and performance snapshots across all subsystems.
 */

import {
  PluginDiagnostics,
  PluginSnapshot,
  PluginTelemetry,
  createPluginDiagnostics,
  createPluginSnapshot,
  createPluginTelemetry,
  createPluginState,
  createPluginHealth,
  createPluginStatistics,
} from './models';
import { IPluginDiagnostics, IPluginRegistry, IPluginLoader } from './interfaces';

export class PluginDiagnosticsManager implements IPluginDiagnostics {
  private readonly _registry: IPluginRegistry;
  private readonly _loader: IPluginLoader;
  private readonly _telemetryData = new Map<string, {
    executions: number;
    failures: number;
    totalDuration: number;
    logs: string[];
  }>();

  constructor(registry: IPluginRegistry, loader: IPluginLoader) {
    this._registry = registry;
    this._loader = loader;
  }

  public getDiagnostics(pluginId: string): PluginDiagnostics {
    const descriptor = this._registry.findPlugin(pluginId);
    const stateList = this._registry.listStates();
    const state = stateList.find(s => s.pluginId === pluginId) || createPluginState({ pluginId });

    const telem = this.telemetry(pluginId);
    const loaderStats = this._loader.statistics();

    const health = createPluginHealth({
      pluginId,
      healthy: state.lifecycleState !== 'FAILED' && telem.successRate >= 0.8,
      lifecycleState: state.lifecycleState,
      issues: state.error ? [state.error] : [],
      message: state.error ? `Plugin failed: ${state.error}` : 'Plugin diagnostics reporting operational.',
    });

    const statistics = createPluginStatistics({
      pluginId,
      loadTimeMs: loaderStats.averageLoadTimeMs || 0,
      activationTimeMs: 0, // Mock or update during lifecycle checks
      executionCount: telem.totalExecutions,
      errorCount: telem.failedExecutions,
    });

    return createPluginDiagnostics({
      pluginId,
      state,
      health,
      statistics,
      timestamp: new Date().toISOString(),
    });
  }

  public getSnapshot(pluginId: string): PluginSnapshot {
    const stateList = this._registry.listStates();
    const state = stateList.find(s => s.pluginId === pluginId) || createPluginState({ pluginId });

    return createPluginSnapshot({
      pluginId,
      state,
      configuration: {
        pluginId,
        settings: {},
      },
      timestamp: new Date().toISOString(),
    });
  }

  public aggregateDiagnostics(): ReadonlyArray<PluginDiagnostics> {
    const plugins = this._registry.listPlugins();
    return plugins.map(p => this.getDiagnostics(p.id));
  }

  public telemetry(pluginId: string): PluginTelemetry {
    const data = this._telemetryData.get(pluginId) || { executions: 0, failures: 0, totalDuration: 0, logs: [] };
    const successRate = data.executions > 0 ? (data.executions - data.failures) / data.executions : 1.0;
    const averageLatencyMs = data.executions > 0 ? data.totalDuration / data.executions : 0;

    return createPluginTelemetry({
      pluginId,
      totalExecutions: data.executions,
      failedExecutions: data.failures,
      successRate,
      averageLatencyMs,
      logs: data.logs,
    });
  }

  public recordTelemetry(pluginId: string, executionDurationMs: number, success: boolean, log?: string): void {
    if (!this._telemetryData.has(pluginId)) {
      this._telemetryData.set(pluginId, { executions: 0, failures: 0, totalDuration: 0, logs: [] });
    }
    const data = this._telemetryData.get(pluginId)!;
    data.executions++;
    if (!success) {
      data.failures++;
    }
    data.totalDuration += executionDurationMs;
    if (log) {
      data.logs.push(`[${new Date().toISOString()}] ${log}`);
    }
  }
}
