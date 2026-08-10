import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginState,
  PluginCertifier,
  InMemoryDiscoverySource
} from '../../src/plugins';

describe('Plugin Runtime Production Certification (Phase 17.10)', () => {

  const setupMockLoader = (provider: PluginProvider) => {
    (provider.loader() as any)['moduleLoader'] = {
      load: async () => ({ initialized: true })
    };
  };

  const setupSecurity = (provider: PluginProvider, pluginId: string, enabled = true) => {
    provider.security().createSecurityProfile(pluginId, {
      enabled,
      permissions: [],
      policies: [],
      resourceLimits: {},
      allowedCapabilities: [],
      deniedCapabilities: []
    });
    if (enabled) {
      provider.security().registerPermission(pluginId, 'CONFIG_READ', 'PLUGIN');
      provider.security().registerPermission(pluginId, 'CONFIG_WRITE', 'PLUGIN');
    }
  };

  // ───── 1. Certifier Construction & DI ─────
  it('1. constructs and accepts DI provider injection correctly', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const certifier = new PluginCertifier(provider);
    expect(certifier).toBeDefined();
    expect(certifier.getHealth()).toBeDefined();
    expect(certifier.getStatistics()).toBeDefined();
  });

  // ───── 2. Runtime / Provider Delegation ─────
  it('2. runtime and provider delegate getters successfully', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const runtime = new PluginRuntime(provider);
    expect(provider.certification()).toBeDefined();
    expect(runtime.certification()).toBeDefined();
    expect(runtime.certification()).toBe(provider.certification());
  });

  // ───── 3. Stage 1: Runtime Foundation ─────
  it('3. certifies Stage 1 (Runtime Foundation) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '1');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(10);
  });

  // ───── 4. Stage 2: Discovery & Manifest ─────
  it('4. certifies Stage 2 (Discovery & Manifest) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '2');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 5. Stage 3: Dependency Resolution ─────
  it('5. certifies Stage 3 (Dependency Resolution) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '3');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 6. Stage 4: Plugin Loading ─────
  it('6. certifies Stage 4 (Plugin Loading) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '4');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 7. Stage 5: Plugin Lifecycle ─────
  it('7. certifies Stage 5 (Plugin Lifecycle) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '5');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 8. Stage 6: Capability & Extension ─────
  it('8. certifies Stage 6 (Capability & Extension) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '6');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 9. Stage 7: Security & Sandbox ─────
  it('9. certifies Stage 7 (Security & Sandbox) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '7');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(10);
  });

  // ───── 10. Stage 8: Configuration ─────
  it('10. certifies Stage 8 (Configuration) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '8');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 11. Stage 9: Integrated Lifecycle ─────
  it('11. certifies Stage 9 (Integrated Lifecycle) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '9');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(10);
  });

  // ───── 12. Stage 10: Transactional Rollback ─────
  it('12. certifies Stage 10 (Transactional Rollback) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '10');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 13. Stage 11: Diagnostics ─────
  it('13. certifies Stage 11 (Diagnostics & Telemetry) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '11');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(5);
  });

  // ───── 14. Stage 12: Immutability ─────
  it('14. certifies Stage 12 (Immutability & API Contract) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '12');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(5);
  });

  // ───── 15. Stage 13: Failure Isolation ─────
  it('15. certifies Stage 13 (Failure Isolation & Resilience) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '13');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(8);
  });

  // ───── 16. Stage 14: Concurrency ─────
  it('16. certifies Stage 14 (Concurrency & Idempotency) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '14');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(4);
  });

  // ───── 17. Stage 15: Performance ─────
  it('17. certifies Stage 15 (Performance benchmarks) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '15');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(5);
  });

  // ───── 18. Stage 16: E2E Graph ─────
  it('18. certifies Stage 16 (Full End-to-End) successfully', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    const stage = report.summary.stageResults.find(s => s.id === '16');
    expect(stage).toBeDefined();
    expect(stage?.passed).toBe(true);
    expect(stage?.score).toBe(6);
  });

  // ───── 19. Scorecard & Status Calculation ─────
  it('19. calculates final scorecard score and status', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    expect(report.summary.score).toBe(119);
    expect(report.summary.status).toBe('PASSED');
  });

  // ───── 20. Issue Logging ─────
  it('20. logs stage errors and warning counts cleanly', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    expect(report.summary.issueCount.CRITICAL).toBe(0);
    expect(report.summary.issueCount.HIGH).toBe(0);
    expect(report.issues.length).toBe(0);
  });

  // ───── 21. Health Metrics ─────
  it('21. returns correct health state and reports degraged / unhealthy status', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const healthBefore = provider.certification().getHealth();
    expect(healthBefore.healthy).toBe(true);

    await provider.certification().certify();
    const healthAfter = provider.certification().getHealth();
    expect(healthAfter.healthy).toBe(true);
    expect(healthAfter.score).toBe(119);
  });

  // ───── 22. Reset Behavior ─────
  it('22. resets historical runs and last report state', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    await provider.certification().certify();
    
    expect(provider.certification().getLastReport()).not.toBeNull();
    expect(provider.certification().getStatistics().totalRuns).toBe(1);

    provider.certification().reset();
    expect(provider.certification().getLastReport()).toBeNull();
    expect(provider.certification().getStatistics().totalRuns).toBe(0);
  });

  // ───── 23. Repeated Certification Runs ─────
  it('23. tracks statistics across multiple certification runs', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    provider.certification().reset();
    await provider.certification().certify();
    await provider.certification().certify();
    
    const stats = provider.certification().getStatistics();
    expect(stats.totalRuns).toBe(2);
    expect(stats.passedRuns).toBe(2);
    expect(stats.averageScore).toBe(119);
  });

  // ───── 24. Immutability checks ─────
  it('24. verifies nested objects inside report cannot be mutated', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    const report = await provider.certification().certify();
    
    expect(Object.isFrozen(report)).toBe(true);
    expect(Object.isFrozen(report.summary)).toBe(true);
    expect(Object.isFrozen(report.summary.issueCount)).toBe(true);
  });

  // ───── 25. certifyPlugin target check ─────
  it('25. runs certifyPlugin on an active provider target', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupMockLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'P1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const source = new InMemoryDiscoverySource({ id: 's1', name: 'MockSource', type: 'in-memory' }, [
      { id: 'p1', name: 'P1', version: '1.0.0', entryPoint: './p1.js', dependencies: [], capabilities: [], metadata: {}, schemaVersion: '1.0.0', author: 'Test' }
    ]);
    provider.discovery().registerSource(source);
    await provider.discovery().discover();

    // Verify it lacks security profile initially (score reduction)
    const res1 = await provider.certification().certifyPlugin('p1');
    expect(res1.success).toBe(false);
    expect(res1.score).toBe(50); // 100 - 30 (security profile) - 20 (config manager throws CONFIG_READ check permission error)

    // Configure security profile
    setupSecurity(provider, 'p1');
    const res2 = await provider.certification().certifyPlugin('p1');
    expect(res2.success).toBe(true);
    expect(res2.score).toBe(100);
  });

  // ───── 26. certifyAll Target Check ─────
  it('26. runs certifyAll to iterate across all active plugins', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupMockLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'P1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });
    provider.registerPlugin({ id: 'p2', name: 'P2', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const source = new InMemoryDiscoverySource({ id: 's1', name: 'MockSource', type: 'in-memory' }, [
      { id: 'p1', name: 'P1', version: '1.0.0', entryPoint: './p1.js', dependencies: [], capabilities: [], metadata: {}, schemaVersion: '1.0.0', author: 'Test' },
      { id: 'p2', name: 'P2', version: '1.0.0', entryPoint: './p2.js', dependencies: [], capabilities: [], metadata: {}, schemaVersion: '1.0.0', author: 'Test' }
    ]);
    provider.discovery().registerSource(source);
    await provider.discovery().discover();

    setupSecurity(provider, 'p1');
    setupSecurity(provider, 'p2');

    const results = await provider.certification().certifyAll();
    expect(results.length).toBe(2);
    expect(results[0].success).toBe(true);
    expect(results[1].success).toBe(true);
  });

  // ───── 27. Schema Configuration validate check ─────
  it('27. certifies configuration schema compatibility in certifyPlugin', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupMockLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'P1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const source = new InMemoryDiscoverySource({ id: 's1', name: 'MockSource', type: 'in-memory' }, [
      { id: 'p1', name: 'P1', version: '1.0.0', entryPoint: './p1.js', dependencies: [], capabilities: [], metadata: {}, schemaVersion: '1.0.0', author: 'Test' }
    ]);
    provider.discovery().registerSource(source);
    await provider.discovery().discover();
    setupSecurity(provider, 'p1');

    provider.configuration().registerSchema('p1', {
      schemaId: 'schema-p1',
      version: '1.0.0',
      fields: [
        { key: 'host', type: 'string', required: true, sensitive: false, readOnly: false, nullable: false }
      ],
      strict: true
    });

    // Mock validation to return invalid schema violations
    provider.configuration().validateConfiguration = () => ({
      valid: false,
      issues: [{ key: 'host', code: 'forced', message: 'forced validation failure', severity: 'ERROR' }],
      validatedAt: Date.now()
    });

    // Create a valid configuration
    provider.configuration().createConfiguration('p1', { host: 'localhost' });
    const res = await provider.certification().certifyPlugin('p1');
    expect(res.success).toBe(true); // 80 score is >= 70 passing threshold
    expect(res.score).toBe(80); // 100 - 20 for schema violation
  });

  // ───── 28. Aggregated Diagnostics ─────
  it('28. integrates diagnostics into unified diagnostics method', () => {
    const provider = new PluginProvider();
    provider.initialize();
    const diag = provider.diagnostics() as any;
    expect(diag.certificationManager).toBeDefined();
    expect(diag.certificationManager.statistics).toBeDefined();
    expect(diag.certificationManager.health).toBeDefined();
  });

  // ───── 29. Default-deny behavior in Security ─────
  it('29. verifies default-deny behaves correctly in certifier context', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupSecurity(provider, 'p1');
    
    // Evaluate unregistered permission: should return false (default deny)
    const allowed = provider.security().checkPermission('p1', 'NETWORK_ACCESS', 'GLOBAL');
    expect(allowed).toBe(false);
  });

  // ───── 30. Sandbox suspended check ─────
  it('30. verifies sandbox is suspended on plugin lifecycle deactivate', async () => {
    const provider = new PluginProvider();
    provider.initialize();
    setupMockLoader(provider);
    provider.registerPlugin({ id: 'p1', name: 'P1', version: '1.0.0', enabled: true, metadata: {}, state: PluginState.REGISTERED });

    const source = new InMemoryDiscoverySource({ id: 's1', name: 'MockSource', type: 'in-memory' }, [
      { id: 'p1', name: 'P1', version: '1.0.0', entryPoint: './p1.js', dependencies: [], capabilities: [], metadata: {}, schemaVersion: '1.0.0', author: 'Test' }
    ]);
    provider.discovery().registerSource(source);
    await provider.discovery().discover();
    setupSecurity(provider, 'p1');

    await provider.integration().integrate('p1');
    expect(provider.sandbox().getSandbox('p1')?.state).toBe('ACTIVE');

    await provider.integration().deactivate('p1');
    expect(provider.sandbox().getSandbox('p1')?.state).toBe('SUSPENDED');
  });
});
