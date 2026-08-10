import { describe, expect, it } from 'vitest';
import {
  InMemoryDiscoverySource,
  PluginProvider,
  PluginState,
  PluginIntegrationPhase
} from '../../src/plugins';

describe('Plugin Runtime Integration (Phase 17.9)', () => {

  const createRawManifest = (id: string, deps: string[] = [], caps: any[] = []): any => {
    return {
      id,
      name: `${id} Plugin`,
      version: '1.0.0',
      description: `Plugin ${id}`,
      author: 'Test Author',
      schemaVersion: '1.0.0',
      entryPoint: `./plugins/${id}.js`,
      dependencies: deps.map(d => ({ id: d, versionRange: '>=1.0.0' })),
      capabilities: caps,
      metadata: {}
    };
  };

  const setupSecurity = (provider: PluginProvider, pluginId: string, enabled = true) => {
    const security = provider.security();
    security.createSecurityProfile(pluginId, {
      enabled,
      permissions: [],
      policies: [],
      resourceLimits: {},
      allowedCapabilities: [],
      deniedCapabilities: []
    });
    if (enabled) {
      security.registerPermission(pluginId, 'CONFIG_READ', 'PLUGIN');
      security.registerPermission(pluginId, 'CONFIG_WRITE', 'PLUGIN');
    }
  };

  const setupLoader = (provider: PluginProvider) => {
    (provider.loader() as any)['moduleLoader'] = {
      load: async () => ({ initialized: true })
    };
  };

  // ───── 1. Manager Construction & DI ─────
  it('1. constructs and performs DI successfully', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const integration = provider.integration();
    expect(integration).toBeDefined();
    expect(integration.statistics()).toBeDefined();
    expect(integration.health()).toBeDefined();
  });

  // ───── 2. Single Plugin Integration ─────
  it('2. integrates a single plugin successfully', async () => {
    const m = createRawManifest('p1');
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    
    provider.registerPlugin({
      id: 'p1',
      name: 'p1 Plugin',
      version: '1.0.0',
      description: 'Test plugin',
      author: 'Author',
      enabled: true,
      metadata: {},
      state: PluginState.REGISTERED
    });

    const discovery = provider.discovery();
    discovery.reset();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');

    const result = await provider.integration().integrate('p1');
    expect(result.success).toBe(true);
    expect(result.phase).toBe(PluginIntegrationPhase.READY);
    expect(result.currentState).toBe(PluginState.ACTIVE);
  });

  // ───── 3. Discovery Failure ─────
  it('3. stops integration on discovery failure', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    const result = await provider.integration().integrate('nonexistent');
    expect(result.success).toBe(false);
    expect(result.phase).toBe(PluginIntegrationPhase.DISCOVERY);
  });

  // ───── 4. Security Preflight Failure ─────
  it('4. stops integration on security preflight failure', async () => {
    const m = createRawManifest('p1');
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    provider.registerPlugin({
      id: 'p1',
      name: 'p1 Plugin',
      version: '1.0.0',
      enabled: true,
      metadata: {},
      state: PluginState.REGISTERED
    });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1', false); // disabled profile

    const result = await provider.integration().integrate('p1');
    expect(result.success).toBe(false);
    expect(result.phase).toBe(PluginIntegrationPhase.SECURITY_PREFLIGHT);
  });

  // ───── 5. Dependency Failure ─────
  it('5. stops integration when a required dependency fails topological resolution', async () => {
    const m = createRawManifest('p1', ['missing_dep']);
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    provider.registerPlugin({
      id: 'p1',
      name: 'p1 Plugin',
      version: '1.0.0',
      enabled: true,
      metadata: {},
      state: PluginState.REGISTERED
    });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');

    const result = await provider.integration().integrate('p1');
    expect(result.success).toBe(false);
    expect(result.phase).toBe(PluginIntegrationPhase.DEPENDENCY_RESOLUTION);
  });

  // ───── 6. Rollback behavior ─────
  it('6. rolls back successfully when a later step fails', async () => {
    const m = createRawManifest('p1', [], [{ type: 'COMMAND', properties: {} }]);
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    provider.registerPlugin({
      id: 'p1',
      name: 'p1 Plugin',
      version: '1.0.0',
      enabled: true,
      metadata: {},
      state: PluginState.REGISTERED
    });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');

    // Spy on registerCapability to throw a forced registration error
    const capManager = provider.capabilities();
    capManager.registerCapability = () => {
      throw new Error('Forced capability registration error');
    };

    const result = await provider.integration().integrate('p1');
    expect(result.success).toBe(false);
    expect(result.phase).toBe(PluginIntegrationPhase.CAPABILITY_REGISTRATION);
    
    // Check that state was rolled back to UNLOADED
    expect(provider.lifecycle().getLifecycleState('p1')).toBe(PluginState.UNLOADED);
    expect(provider.sandbox().getSandbox('p1')).toBeNull();
  });

  // ───── 7. Dependency-Aware Bulk Integration ─────
  it('7. integrates multiple plugins in topological dependency order', async () => {
    const m1 = createRawManifest('p1');
    const m2 = createRawManifest('p2', ['p1']);
    
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);

    provider.registerPlugin({ id: 'p1', name: 'p1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });
    provider.registerPlugin({ id: 'p2', name: 'p2', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m1, m2]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');
    setupSecurity(provider, 'p2');

    const results = await provider.integration().integrateMany(['p2', 'p1']);
    expect(results.length).toBe(2);
    expect(results[0].pluginId).toBe('p1'); // p1 must integrate first
    expect(results[0].success).toBe(true);
    expect(results[1].pluginId).toBe('p2'); // p2 integrates second
    expect(results[1].success).toBe(true);
  });

  // ───── 8. Startup / Shutdown Orchestration ─────
  it('8. orchestrates startup and shutdown reverse deactivation order', async () => {
    const m1 = createRawManifest('p1');
    const m2 = createRawManifest('p2', ['p1']);
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);

    provider.registerPlugin({ id: 'p1', name: 'p1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });
    provider.registerPlugin({ id: 'p2', name: 'p2', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m1, m2]
    );
    discovery.registerSource(source);

    setupSecurity(provider, 'p1');
    setupSecurity(provider, 'p2');

    const startupResults = await provider.integration().startup();
    expect(startupResults.length).toBe(2);
    expect(startupResults[0].pluginId).toBe('p1');
    expect(startupResults[1].pluginId).toBe('p2');

    // Shutdown deactivates p2 then p1
    const shutdownResults = await provider.integration().shutdown();
    expect(shutdownResults.length).toBe(2);
    expect(shutdownResults[0].pluginId).toBe('p2'); // p2 deactivated first
    expect(shutdownResults[1].pluginId).toBe('p1'); // p1 deactivated second
  });

  // ───── 9. Idempotency & Concurrency ─────
  it('9. provides idempotent operations and handles concurrent requests gracefully', async () => {
    const m = createRawManifest('p1');
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'p1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');

    // Call integrate concurrently
    const [r1, r2] = await Promise.all([
      provider.integration().integrate('p1'),
      provider.integration().integrate('p1')
    ]);

    expect(r1.success).toBe(true);
    expect(r2.success).toBe(true);
    expect(r1.duration).toBe(r2.duration); // Should return the exact same in-flight result promise
  });

  // ───── 10. Reload ─────
  it('10. reloads a plugin successfully', async () => {
    const m = createRawManifest('p1');
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'p1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const discovery = provider.discovery();
    const source = new InMemoryDiscoverySource(
      { id: 's1', name: 'Source 1', type: 'in-memory' },
      [m]
    );
    discovery.registerSource(source);
    await discovery.discover();

    setupSecurity(provider, 'p1');

    await provider.integration().integrate('p1');
    const reloadRes = await provider.integration().reload('p1');
    expect(reloadRes.success).toBe(true);
    expect(reloadRes.phase).toBe(PluginIntegrationPhase.READY);
  });

  // ───── 11. Diagnostics & Health ─────
  it('11. returns correct diagnostics, statistics, and health models', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupLoader(provider);
    
    const diag = provider.integration().diagnostics();
    expect(diag.statistics).toBeDefined();
    expect(diag.health).toBeDefined();
    expect(diag.activeIntegrations).toBeDefined();
    expect(diag.historyDepth).toBe(0);

    const providerDiag = provider.diagnostics() as any;
    expect(providerDiag.integrationManager).toBeDefined();
  });
});
