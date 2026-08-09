import { describe, expect, it } from 'vitest';
import {
  PluginProvider,
  PluginRuntime,
  PluginManifestValidator,
  PluginLoader,
  PluginLifecycleManager,
  PluginPolicyManager,
  PluginSecurityManager,
  PluginSandboxManager,
  PluginPermissionScope,
  PluginPermissionAction,
  PluginPermissionError,
  PluginSandboxError,
  PluginResourceLimitError,
  type PluginManifest,
  type IPluginDiscoveryManager,
  type IPluginDependencyResolver,
  type IPluginModuleLoader
} from '../../src/plugins';

describe('Plugin Security & Sandboxing Runtime (Phase 17.7)', () => {

  const createManifest = (id: string, version: string, entryPoint: string): PluginManifest => {
    return PluginManifestValidator.parse({
      id,
      name: `${id} Plugin`,
      version,
      description: `Description of ${id}`,
      author: 'Test Author',
      schemaVersion: '1.0.0',
      entryPoint,
      dependencies: [],
      capabilities: [],
      metadata: {}
    });
  };

  const createMockDiscovery = (manifests: PluginManifest[]): IPluginDiscoveryManager => {
    return {
      registerSource: () => {},
      unregisterSource: () => {},
      getSources: () => [],
      discover: async () => ({ success: true, manifests, invalid: [], duplicates: [], failures: [] }),
      discoverFromSource: async () => ({ success: true, manifests, invalid: [], duplicates: [], failures: [] }),
      find: (id) => manifests.find(m => m.id === id) || null,
      findAll: () => Object.freeze([...manifests]),
      contains: (id) => manifests.some(m => m.id === id),
      remove: () => false,
      clear: () => {},
      statistics: () => ({ discoveryAttempts: 0, discoveredPlugins: 0, validManifests: manifests.length, invalidManifests: 0, duplicateAttempts: 0, discoveryFailures: 0, validationFailures: 0, registeredSources: 0 }),
      health: () => ({ healthy: true, message: 'healthy', issues: [] }),
      reset: () => {}
    };
  };

  const createMockResolver = (order: string[] = []): IPluginDependencyResolver => {
    return {
      resolve: () => ({ status: 'RESOLVED', plan: { order }, issues: [], resolvedIds: order, unresolvedIds: [] }),
      resolveAll: () => ({ status: 'RESOLVED', plan: { order }, issues: [], resolvedIds: order, unresolvedIds: [] }),
      resolvePlugin: (id) => ({ status: 'RESOLVED', plan: { order: [id] }, issues: [], resolvedIds: [id], unresolvedIds: [] }),
      graph: () => ({ nodes: new Map(), edges: [] }),
      dependenciesOf: () => [],
      dependentsOf: () => [],
      statistics: () => ({} as any),
      health: () => ({ healthy: true, unresolvedDependencyCount: 0, cycleCount: 0, conflictCount: 0, message: 'healthy' }),
      reset: () => {}
    };
  };

  class FakeModuleLoader implements IPluginModuleLoader {
    public async load(_entryPoint: string): Promise<unknown> {
      return { initialized: true };
    }
  }

  const createRuntimeContext = (manifests: PluginManifest[], order: string[] = []) => {
    const discovery = createMockDiscovery(manifests);
    const resolver = createMockResolver(order);
    const loader = new PluginLoader(discovery, resolver, new FakeModuleLoader());
    const lifecycle = new PluginLifecycleManager(discovery, resolver, loader);
    return { discovery, resolver, loader, lifecycle };
  };

  describe('Permissions Management', () => {
    // A. Permission registration
    // C. Permission lookup
    it('registers and looks up permissions successfully', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      const perm = security.registerPermission('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE, 'Read workspace files');
      expect(perm).toBeDefined();
      expect(perm.pluginId).toBe('p1');
      expect(perm.action).toBe(PluginPermissionAction.READ_FILES);
      expect(perm.scope).toBe(PluginPermissionScope.WORKSPACE);

      const lookup = security.getPermission('p1', perm.id);
      expect(lookup).toBeDefined();
      expect(lookup?.id).toBe(perm.id);
    });

    // B. Permission revocation
    it('revokes permissions successfully', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      const perm = security.registerPermission('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(security.getPermission('p1', perm.id)).not.toBeNull();

      security.revokePermission('p1', perm.id);
      expect(security.getPermission('p1', perm.id)).toBeNull();
    });

    it('rejects registering permission with invalid arguments', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      expect(() => {
        security.registerPermission('', '', '' as any);
      }).toThrow(PluginPermissionError);
    });
  });

  describe('Permission & Policy Evaluation', () => {
    // D. Permission scope evaluation
    // E. Explicit allow
    // H. Missing profile
    // AH. Fail-closed behavior
    it('evaluates permission scopes and profiles cleanly (fails closed by default)', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      // No profile -> fails closed
      let decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(false);
      expect(decision.reason).toContain('does not exist');

      // Create disabled profile -> fails closed
      security.createSecurityProfile('p1', {
        enabled: false,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(false);
      expect(decision.reason).toContain('disabled');

      // Enable profile -> still fails closed (default deny) because no permission or policy matches
      security.updateSecurityProfile('p1', { enabled: true });
      decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(false);
      expect(decision.reason).toContain('Default Deny');

      // Register ALLOW permission -> succeeds
      const perm = security.registerPermission('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(true);
      expect(decision.matchedPermissionId).toBe(perm.id);
    });

    // F. Explicit deny
    // G. DENY-overrides-ALLOW
    it('enforces explicit deny overriding explicit allow permissions', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      // Register ALLOW
      security.registerPermission('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      let decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(true);

      // Test that policy DENY overrides permission ALLOW!
      policy.registerPolicy({
        id: 'pol-deny',
        name: 'Deny policy',
        priority: 100,
        enabled: true,
        action: PluginPermissionAction.READ_FILES,
        scopes: [PluginPermissionScope.WORKSPACE],
        effect: 'DENY'
      });

      decision = security.evaluate('p1', PluginPermissionAction.READ_FILES, PluginPermissionScope.WORKSPACE);
      expect(decision.allowed).toBe(false);
      expect(decision.reason).toContain('policy DENY');
    });

    // J. Policy registration
    // K. Policy priority
    // L. Equal-priority deterministic ordering
    // M. Policy conflicts
    it('handles policy priority, FIFO tie ordering, and conflicts deterministically', () => {
      const policy = new PluginPolicyManager();

      // Register allow policy with priority 10
      policy.registerPolicy({
        id: 'pol-allow',
        name: 'Allow Policy',
        priority: 10,
        enabled: true,
        action: 'TEST_ACTION',
        scopes: [PluginPermissionScope.GLOBAL],
        effect: 'ALLOW'
      });

      let res = policy.evaluate('TEST_ACTION', PluginPermissionScope.GLOBAL, 'p1');
      expect(res.effect).toBe('ALLOW');
      expect(res.policyId).toBe('pol-allow');

      // Register deny policy with higher priority 20
      policy.registerPolicy({
        id: 'pol-deny',
        name: 'Deny Policy',
        priority: 20,
        enabled: true,
        action: 'TEST_ACTION',
        scopes: [PluginPermissionScope.GLOBAL],
        effect: 'DENY'
      });

      res = policy.evaluate('TEST_ACTION', PluginPermissionScope.GLOBAL, 'p1');
      expect(res.effect).toBe('DENY');
      expect(res.policyId).toBe('pol-deny');

      // Register another policy with priority 20 (equal priority) -> FIFO ordering
      policy.registerPolicy({
        id: 'pol-allow-equal',
        name: 'Allow Equal Policy',
        priority: 20,
        enabled: true,
        action: 'TEST_ACTION',
        scopes: [PluginPermissionScope.GLOBAL],
        effect: 'ALLOW'
      });

      // Still DENY since deny wins conflict when both evaluate (conflict behavior: DENY wins)
      res = policy.evaluate('TEST_ACTION', PluginPermissionScope.GLOBAL, 'p1');
      expect(res.effect).toBe('DENY');
    });

    // N. Capability authorization
    // O. Disabled capability rejection
    it('authorizes capabilities and rejects disabled/denied capabilities', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: ['blocked-cap']
      });

      security.registerPermission('p1', 'blocked-cap', PluginPermissionScope.GLOBAL);

      const decision = security.evaluate('p1', 'blocked-cap', PluginPermissionScope.GLOBAL);
      expect(decision.allowed).toBe(false);
      expect(decision.reason).toContain('explicitly denied');
    });
  });

  describe('Logical Sandbox & Resource Limits', () => {
    // P. Sandbox creation
    // Q. Sandbox state transitions
    it('creates logical sandbox and validates state transitions safely', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);
      const sandbox = new PluginSandboxManager(lifecycle, security);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: { maxConcurrentOperations: 5 },
        allowedCapabilities: ['cap1'],
        deniedCapabilities: []
      });

      const snap = sandbox.createSandbox('p1');
      expect(snap.state).toBe('CREATED');

      sandbox.updateSandboxState('p1', 'ACTIVE');
      expect(sandbox.getSandbox('p1')?.state).toBe('ACTIVE');

      sandbox.updateSandboxState('p1', 'SUSPENDED');
      expect(sandbox.getSandbox('p1')?.state).toBe('SUSPENDED');

      // Invalid transitions
      expect(() => {
        sandbox.updateSandboxState('p1', 'VIOLATION');
      }).toThrow(PluginSandboxError);
    });

    // R. Sandbox operation validation
    it('validates operation against sandbox capability scopes', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);
      const sandbox = new PluginSandboxManager(lifecycle, security);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: ['cap1'],
        deniedCapabilities: ['cap2']
      });

      sandbox.createSandbox('p1');
      sandbox.updateSandboxState('p1', 'ACTIVE');

      expect(sandbox.validateOperation('p1', 'cap1')).toBe(true);
      expect(sandbox.validateOperation('p1', 'cap2')).toBe(false); // explicit denied
      expect(sandbox.validateOperation('p1', 'cap3')).toBe(false); // not in allowed capabilities list
    });

    // S. Resource limit enforcement
    // T. Concurrent-operation limits
    it('enforces concurrent operation resource limits and records violations', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);
      const sandbox = new PluginSandboxManager(lifecycle, security);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: { maxConcurrentOperations: 2 },
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      sandbox.createSandbox('p1');
      sandbox.updateSandboxState('p1', 'ACTIVE');

      sandbox.incrementUsage('p1', 'maxConcurrentOperations'); // 1
      sandbox.incrementUsage('p1', 'maxConcurrentOperations'); // 2

      expect(() => {
        sandbox.incrementUsage('p1', 'maxConcurrentOperations'); // 3 -> limit is 2
      }).toThrow(PluginResourceLimitError);

      expect(sandbox.getSandbox('p1')?.state).toBe('VIOLATION');
      expect(security.statistics().violations).toBe(1);
    });
  });

  describe('Auditing, History & Diagnostics', () => {
    // W. Audit history
    // X. Bounded audit retention
    // Y. Security violation recording
    it('logs audit records and evicts oldest items when capacity is exceeded', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy, { maxAuditHistorySize: 3 });

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      // Triggers evaluation logs (which create audit records)
      security.evaluate('p1', 'act1', PluginPermissionScope.GLOBAL);
      security.evaluate('p1', 'act2', PluginPermissionScope.GLOBAL);
      security.evaluate('p1', 'act3', PluginPermissionScope.GLOBAL);
      
      expect(security.auditHistory()).toHaveLength(3);

      security.evaluate('p1', 'act4', PluginPermissionScope.GLOBAL); // Evicts act1 audit record
      expect(security.auditHistory()).toHaveLength(3);
      expect(security.auditHistory()[0].action).toBe('act2');
    });

    // Z. Statistics
    // AA. Health
    // AB. Diagnostics
    // AC. Immutability
    it('reports stats, health, and deep diagnostics immutably', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      const stats = security.statistics();
      expect(stats.totalDecisions).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = security.health();
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);

      const diag = security.diagnostics();
      expect(diag.statistics).toBeDefined();
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('Integration & Reset behavior', () => {
    // AD. Provider delegation
    // AE. Runtime delegation
    it('delegates security managers correctly through provider and runtime', () => {
      const provider = new PluginProvider();
      expect(provider.security()).toBeDefined();
      expect(provider.policies()).toBeDefined();
      expect(provider.sandbox()).toBeDefined();

      const runtime = new PluginRuntime(provider);
      expect(runtime.security()).toBeDefined();
      expect(runtime.policies()).toBeDefined();
      expect(runtime.sandbox()).toBeDefined();
    });

    // AF. Lifecycle integration
    it('automatically creates, suspends, and destroys sandboxes based on lifecycle state changes', async () => {
      const m1 = createManifest('p1', '1.0.0', 'p1.js');
      const { loader, lifecycle } = createRuntimeContext([m1], ['p1']);
      const security = new PluginSecurityManager(lifecycle, new PluginPolicyManager());
      const sandbox = new PluginSandboxManager(lifecycle, security);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      await loader.load('p1');
      await lifecycle.initializePlugin('p1');

      // On activation -> sandbox automatically initialized and set to ACTIVE
      await lifecycle.activatePlugin('p1');
      expect(sandbox.getSandbox('p1')).not.toBeNull();
      expect(sandbox.getSandbox('p1')?.state).toBe('ACTIVE');

      // On deactivation -> sandbox suspended
      await lifecycle.deactivatePlugin('p1');
      expect(sandbox.getSandbox('p1')?.state).toBe('SUSPENDED');

      // On disposal -> sandbox destroyed
      await lifecycle.disposePlugin('p1');
      expect(sandbox.getSandbox('p1')).toBeNull();
    });

    // AG. Reset behavior
    it('resets security registrations, profiles, audits, and violations cleanly', () => {
      const { lifecycle } = createRuntimeContext([]);
      const policy = new PluginPolicyManager();
      const security = new PluginSecurityManager(lifecycle, policy);

      security.createSecurityProfile('p1', {
        enabled: true,
        permissions: [],
        policies: [],
        resourceLimits: {},
        allowedCapabilities: [],
        deniedCapabilities: []
      });

      security.reset();
      expect(security.getSecurityProfile('p1')).toBeNull();
      expect(security.auditHistory()).toHaveLength(0);
    });
  });

});
