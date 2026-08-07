import { beforeEach, describe, expect, it } from 'vitest';
import {
  PluginRegistry,
  PluginLoader,
  PluginDiagnosticsManager,
  createPluginManifest,
  PluginLifecycleState,
} from '../../src/runtime/plugins';

describe('Phase 16.7 — Diagnostics & Telemetry Engine Tests', () => {
  let registry: PluginRegistry;
  let loader: PluginLoader;
  let diagnostics: PluginDiagnosticsManager;

  beforeEach(() => {
    registry = new PluginRegistry();
    loader = new PluginLoader();
    diagnostics = new PluginDiagnosticsManager(registry, loader);
  });

  describe('1. Diagnostics Aggregation', () => {
    it('should generate diagnostics report for a registered plugin', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);

      const report = diagnostics.getDiagnostics('p1');
      expect(report.pluginId).toBe('p1');
      expect(report.state.lifecycleState).toBe(PluginLifecycleState.REGISTERED);
      expect(report.health.healthy).toBe(true);
      expect(report.statistics.executionCount).toBe(0);
    });

    it('should aggregate diagnostics for all plugins', () => {
      const p1 = createPluginManifest({ id: 'p1', name: 'P1' });
      const p2 = createPluginManifest({ id: 'p2', name: 'P2' });
      registry.registerPlugin(p1);
      registry.registerPlugin(p2);

      const list = diagnostics.aggregateDiagnostics();
      expect(list.length).toBe(2);
      expect(list[0].pluginId).toBe('p1');
      expect(list[1].pluginId).toBe('p2');
    });

    it('should retrieve snapshot containing configuration and state', () => {
      const manifest = createPluginManifest({ id: 'p1', name: 'P1' });
      registry.registerPlugin(manifest);

      const snapshot = diagnostics.getSnapshot('p1');
      expect(snapshot.pluginId).toBe('p1');
      expect(snapshot.state).toBeDefined();
      expect(snapshot.configuration).toBeDefined();
    });
  });

  describe('2. Telemetry and Performance metrics', () => {
    it('should record execution telemetry and compute latency', () => {
      diagnostics.recordTelemetry('p1', 12.5, true, 'Executed command successfully');
      diagnostics.recordTelemetry('p1', 27.5, true, 'Executed query successfully');
      diagnostics.recordTelemetry('p1', 5.0, false, 'Failed file save');

      const telem = diagnostics.telemetry('p1');
      expect(telem.totalExecutions).toBe(3);
      expect(telem.failedExecutions).toBe(1);
      expect(telem.successRate).toBeCloseTo(0.666);
      expect(telem.averageLatencyMs).toBe(15); // (12.5 + 27.5 + 5) / 3 = 15
      expect(telem.logs.length).toBe(3);
    });

    it('should return default zero telemetry if none exists', () => {
      const telem = diagnostics.telemetry('ghost');
      expect(telem.totalExecutions).toBe(0);
      expect(telem.successRate).toBe(1.0);
      expect(telem.averageLatencyMs).toBe(0);
    });
  });
});
