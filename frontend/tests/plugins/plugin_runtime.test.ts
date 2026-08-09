import { describe, expect, it } from 'vitest';

import {
  PluginProvider,
  PluginRuntime,
  PluginRuntimeError,
  PluginInitializationError,
  PluginRegistrationError,
  PluginStateError,
  PluginRuntimeState,
  PluginState,
  createPlugin,
  createPluginRuntime,
  type IPluginProvider,
} from '../../src/plugins';

describe('plugin runtime foundation', () => {
  it('creates a plugin model', () => {
    const plugin = createPlugin({
      id: 'demo-plugin',
      name: 'Demo Plugin',
      version: '1.0.0',
      description: 'Example plugin',
      author: 'Auralis',
      enabled: true,
      metadata: { category: 'utility' },
    });

    expect(plugin.id).toBe('demo-plugin');
    expect(plugin.name).toBe('Demo Plugin');
    expect(plugin.version).toBe('1.0.0');
    expect(plugin.enabled).toBe(true);
  });

  it('freezes plugin models', () => {
    const plugin = createPlugin({
      id: 'frozen-plugin',
      name: 'Frozen Plugin',
      version: '1.0.0',
      enabled: false,
    });

    expect(Object.isFrozen(plugin)).toBe(true);
    expect(Object.isFrozen(plugin.metadata)).toBe(true);
    expect(() => {
      (plugin as { name: string }).name = 'changed';
    }).toThrow(TypeError);
  });

  it('exposes plugin runtime state values', () => {
    expect(PluginRuntimeState.UNINITIALIZED).toBe('UNINITIALIZED');
    expect(PluginRuntimeState.READY).toBe('READY');
    expect(PluginRuntimeState.STOPPED).toBe('STOPPED');
  });

  it('exposes plugin state values', () => {
    expect(PluginState.UNREGISTERED).toBe('UNREGISTERED');
    expect(PluginState.REGISTERED).toBe('REGISTERED');
    expect(PluginState.DISPOSED).toBe('DISPOSED');
  });

  it('preserves the error hierarchy', () => {
    const error = new PluginInitializationError('init failed');
    expect(error).toBeInstanceOf(PluginRuntimeError);
    expect(error).toBeInstanceOf(Error);
    expect(error.name).toBe('PluginInitializationError');
    expect(error.message).toBe('init failed');
    expect(error.stack).toContain('PluginInitializationError');
  });

  it('initializes the provider', () => {
    const provider = new PluginProvider();
    const lifecycle = provider.initialize();

    expect(lifecycle.state).toBe(PluginRuntimeState.READY);
    expect(provider.state()).toBe(PluginRuntimeState.READY);
    expect(provider.health().healthy).toBe(true);
  });

  it('initializes idempotently', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const lifecycle = provider.initialize();

    expect(lifecycle.state).toBe(PluginRuntimeState.READY);
    expect(provider.statistics().initializationCount).toBe(1);
  });

  it('shuts down the provider', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const lifecycle = provider.shutdown();

    expect(lifecycle.state).toBe(PluginRuntimeState.STOPPED);
    expect(provider.state()).toBe(PluginRuntimeState.STOPPED);
  });

  it('shuts down idempotently', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.shutdown();
    const lifecycle = provider.shutdown();

    expect(lifecycle.state).toBe(PluginRuntimeState.STOPPED);
    expect(provider.statistics().shutdownCount).toBe(1);
  });

  it('handles invalid lifecycle transitions safely', () => {
    const provider = new PluginProvider();
    const shutdownResult = provider.shutdown();
    const initializeResult = provider.initialize();

    expect(shutdownResult.state).toBe(PluginRuntimeState.UNINITIALIZED);
    expect(initializeResult.state).toBe(PluginRuntimeState.READY);
    expect(provider.statistics().initializationCount).toBe(1);
    expect(provider.statistics().shutdownCount).toBe(0);
  });

  it('registers plugins', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const registration = provider.registerPlugin(createPlugin({
      id: 'plugin-a',
      name: 'Plugin A',
      version: '1.0.0',
      enabled: true,
    }));

    expect(registration.success).toBe(true);
    expect(registration.plugin.id).toBe('plugin-a');
    expect(registration.plugin.state).toBe(PluginState.REGISTERED);
    expect(provider.hasPlugin('plugin-a')).toBe(true);
  });

  it('rejects duplicate plugin registration', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.registerPlugin(createPlugin({
      id: 'plugin-a',
      name: 'Plugin A',
      version: '1.0.0',
      enabled: true,
    }));

    expect(() => provider.registerPlugin(createPlugin({
      id: 'plugin-a',
      name: 'Plugin A',
      version: '1.0.0',
      enabled: true,
    }))).toThrow(PluginRegistrationError);
  });

  it('looks up registered plugins', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.registerPlugin(createPlugin({
      id: 'plugin-b',
      name: 'Plugin B',
      version: '1.0.0',
      enabled: false,
    }));

    const plugin = provider.getPlugin('plugin-b');
    expect(plugin?.id).toBe('plugin-b');
    expect(plugin?.state).toBe(PluginState.REGISTERED);
  });

  it('checks plugin existence', () => {
    const provider = new PluginProvider();
    expect(provider.hasPlugin('missing')).toBe(false);
  });

  it('lists plugins', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.registerPlugin(createPlugin({
      id: 'plugin-c',
      name: 'Plugin C',
      version: '1.0.0',
      enabled: true,
    }));

    const plugins = provider.listPlugins();
    expect(plugins).toHaveLength(1);
    expect(plugins[0].id).toBe('plugin-c');
  });

  it('unregisters plugins', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.registerPlugin(createPlugin({
      id: 'plugin-d',
      name: 'Plugin D',
      version: '1.0.0',
      enabled: true,
    }));

    const result = provider.unregisterPlugin('plugin-d');

    expect(result.success).toBe(true);
    expect(result.pluginId).toBe('plugin-d');
    expect(provider.hasPlugin('plugin-d')).toBe(false);
  });

  it('rejects missing plugin unregistration', () => {
    const provider = new PluginProvider();
    expect(() => provider.unregisterPlugin('missing')).toThrow(PluginStateError);
  });

  it('delegates runtime operations', () => {
    const runtime = createPluginRuntime();
    const lifecycle = runtime.initialize();

    expect(lifecycle.state).toBe(PluginRuntimeState.READY);
    expect(runtime.state()).toBe(PluginRuntimeState.READY);
  });

  it('supports dependency injection with a mock provider', () => {
    const calls: string[] = [];
    const provider: IPluginProvider = {
      initialize: () => {
        calls.push('initialize');
        return { state: PluginRuntimeState.READY, healthy: true, message: 'ready' };
      },
      shutdown: () => {
        calls.push('shutdown');
        return { state: PluginRuntimeState.STOPPED, healthy: false, message: 'stopped' };
      },
      state: () => PluginRuntimeState.READY,
      status: () => ({ state: PluginRuntimeState.READY, healthy: true, message: 'ready' }),
      statistics: () => ({ registeredPlugins: 0, enabledPlugins: 0, disabledPlugins: 0, initializationCount: 0, shutdownCount: 0, errors: 0, uptime: 0 }),
      health: () => ({ healthy: true, state: PluginRuntimeState.READY, registeredPluginCount: 0, enabledPluginCount: 0, errorCount: 0, message: 'ready' }),
      registerPlugin: () => ({ success: true, plugin: createPlugin({ id: 'mock', name: 'Mock', version: '1.0.0', enabled: true }), pluginId: 'mock', message: 'mock registered' }),
      unregisterPlugin: () => { throw new PluginStateError('missing'); },
      hasPlugin: () => false,
      getPlugin: () => null,
      listPlugins: () => [],
      diagnostics: () => ({ runtimeState: PluginRuntimeState.READY, pluginCounts: { registered: 0, enabled: 0, disabled: 0 }, statistics: { registeredPlugins: 0, enabledPlugins: 0, disabledPlugins: 0, initializationCount: 0, shutdownCount: 0, errors: 0, uptime: 0 }, health: { healthy: true, state: PluginRuntimeState.READY, registeredPluginCount: 0, enabledPluginCount: 0, errorCount: 0, message: 'ready' }, capabilities: [] }),
      discovery: () => ({
        registerSource: () => {},
        unregisterSource: () => {},
        getSources: () => [],
        discover: async () => ({ success: true, manifests: [], invalid: [], duplicates: [], failures: [] }),
        discoverFromSource: async () => ({ success: true, manifests: [], invalid: [], duplicates: [], failures: [] }),
        find: () => null,
        findAll: () => [],
        contains: () => false,
        remove: () => false,
        clear: () => {},
        statistics: () => ({ discoveryAttempts: 0, discoveredPlugins: 0, validManifests: 0, invalidManifests: 0, duplicateAttempts: 0, discoveryFailures: 0, validationFailures: 0, registeredSources: 0 }),
        health: () => ({ healthy: true, message: 'healthy', issues: [] }),
        reset: () => {}
      }),
    };

    const runtime = new PluginRuntime(provider);
    runtime.initialize();
    runtime.shutdown();

    expect(calls).toEqual(['initialize', 'shutdown']);
  });

  it('tracks statistics', () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.registerPlugin(createPlugin({ id: 's1', name: 'S1', version: '1.0.0', enabled: true }));
    provider.registerPlugin(createPlugin({ id: 's2', name: 'S2', version: '1.0.0', enabled: false }));
    const stats = provider.statistics();

    expect(stats.registeredPlugins).toBe(2);
    expect(stats.enabledPlugins).toBe(1);
    expect(stats.disabledPlugins).toBe(1);
    expect(stats.initializationCount).toBe(1);
  });

  it('returns health snapshots', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const health = provider.health();

    expect(health.healthy).toBe(true);
    expect(health.state).toBe(PluginRuntimeState.READY);
    expect(health.registeredPluginCount).toBe(0);
  });

  it('returns immutable diagnostics', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const diagnostics = provider.diagnostics();

    expect(Object.isFrozen(diagnostics)).toBe(true);
    expect(Object.isFrozen(diagnostics.statistics)).toBe(true);
    expect(Object.isFrozen(diagnostics.health)).toBe(true);
    expect(() => {
      (diagnostics as { runtimeState: string }).runtimeState = 'BROKEN';
    }).toThrow(TypeError);
  });
});
