import { beforeEach, describe, expect, it } from 'vitest';
import {
  CircularDependencyException,
  ContainerState,
  createContainerCapabilities,
  createContainerConfiguration,
  createContainerContext,
  createContainerDiagnostics,
  createContainerHealth,
  createContainerStatistics,
  createDependencyNode,
  createScopedContainer,
  createServiceDescriptorModel,
  createServiceRegistration,
  DependencyContainer,
  DependencyInjectionException,
  getDependencyContainer,
  getServiceProvider,
  IServiceProvider,
  resetDependencyContainer,
  resetServiceProvider,
  ServiceCollection,
  ServiceDescriptor,
  ServiceLifetime,
  ServiceProvider,
  ServiceRegistrationException,
  ServiceResolutionException,
  ServiceValidationException,
  setDependencyContainer,
  setServiceProvider,
} from '../../src/runtime/di';

class LoggerService {
  public id = Math.random();
}

class UserSessionService {
  public id = Math.random();
}

class TransientService {
  public id = Math.random();
}

describe('Phase 16.2.4 — Frontend Dependency Injection Scoped Lifetime & Child Container Engine', () => {
  beforeEach(() => {
    resetDependencyContainer();
    resetServiceProvider();
  });

  describe('1. ScopedContainer Models, Exceptions & Capabilities', () => {
    it('should create immutable ScopedContainer model', () => {
      const scopeModel = createScopedContainer({ scopeId: 'scope_1', parentScopeId: 'root' });
      expect(scopeModel.scopeId).toBe('scope_1');
      expect(scopeModel.parentScopeId).toBe('root');
      expect(scopeModel.active).toBe(true);
      expect(Object.isFrozen(scopeModel)).toBe(true);
    });

    it('should verify ContainerCapabilities supportsScopes = true', () => {
      const caps = createContainerCapabilities();
      expect(caps.supportsScopes).toBe(true);
    });

    it('should verify diagnostics includes activeScopes, scopeHierarchy, and scopedCacheSize', () => {
      const diag = createContainerDiagnostics({
        activeScopes: ['root', 'scope_1'],
        scopeHierarchy: { scope_1: 'root' },
        scopedCacheSize: 2,
      });

      expect(diag.activeScopes).toContain('scope_1');
      expect(diag.scopeHierarchy['scope_1']).toBe('root');
      expect(diag.scopedCacheSize).toBe(2);

      const cfg = createContainerConfiguration();
      expect(cfg.name).toBe('Auralis Container');

      const ctx = createContainerContext();
      expect(ctx.containerId).toBe('default-container');

      const health = createContainerHealth();
      expect(health.healthy).toBe(false);

      const stats = createContainerStatistics();
      expect(stats.totalRegistrations).toBe(0);

      const node = createDependencyNode({ serviceType: 'S1', dependencies: ['D1'] });
      expect(node.dependencies).toContain('D1');

      const descModel = createServiceDescriptorModel({ descriptorId: 'd1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON });
      expect(descModel.serviceType).toBe('S1');

      const reg = createServiceRegistration({ descriptorId: 'r1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON });
      expect(reg.serviceType).toBe('S1');

      expect(ContainerState.UNINITIALIZED).toBe('UNINITIALIZED');
    });

    it('should exercise exception hierarchy', () => {
      expect(new CircularDependencyException('circ')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceResolutionException('res')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceRegistrationException('reg')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceValidationException('val')).toBeInstanceOf(DependencyInjectionException);
    });
  });

  describe('2. Scope Creation, Hierarchy & Disposal', () => {
    it('should create child scope and verify parent-child relationship', () => {
      const rootProvider = new ServiceProvider();
      const scope1 = rootProvider.createScope();

      expect(rootProvider.isScope()).toBe(false);
      expect(scope1.isScope()).toBe(true);
      expect(scope1.scopeId()).toBeDefined();
      expect(scope1.parentScope()).toBe(rootProvider);
    });

    it('should dispose scope and invalidate child resolution', () => {
      const rootProvider = new ServiceProvider();
      rootProvider.initialize();

      const scope1 = rootProvider.createScope();
      const collection = new ServiceCollection();
      collection.addScoped('Session', UserSessionService);

      const scopedProvider = new ServiceProvider(collection, undefined, undefined, undefined, scope1 as any);

      expect(scopedProvider.resolve('Session')).toBeDefined();

      scopedProvider.disposeScope();
      expect(() => scopedProvider.resolve('Session')).toThrow(ServiceResolutionException);
    });

    it('should dispose all nested child scopes when parent scope is disposed', () => {
      const root = new ServiceProvider();
      const scopeA = root.createScope();
      const scopeB = scopeA.createScope();

      expect(scopeA.isScope()).toBe(true);
      expect(scopeB.isScope()).toBe(true);

      scopeA.disposeScope();

      expect(() => scopeB.resolve('Any')).toThrow(ServiceResolutionException);
    });
  });

  describe('3. Scoped Lifetime Isolation & Singleton Sharing', () => {
    it('should share singletons across scopes but isolate scoped services per scope', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('Logger', LoggerService);
      collection.addScoped('UserSession', UserSessionService);
      collection.addTransient('Transient', TransientService);

      const rootProvider = new ServiceProvider(collection);
      rootProvider.initialize();

      const scopeA = rootProvider.createScope();
      const scopeB = rootProvider.createScope();

      // Singleton is shared across root and all child scopes
      const logRoot = rootProvider.resolve<LoggerService>('Logger');
      const logA = scopeA.resolve<LoggerService>('Logger');
      const logB = scopeB.resolve<LoggerService>('Logger');

      expect(logA).toBe(logRoot);
      expect(logB).toBe(logRoot);

      // Scoped is cached within same scope, but different across different scopes
      const sessA1 = scopeA.resolve<UserSessionService>('UserSession');
      const sessA2 = scopeA.resolve<UserSessionService>('UserSession');
      const sessB1 = scopeB.resolve<UserSessionService>('UserSession');

      expect(sessA1).toBe(sessA2);
      expect(sessA1).not.toBe(sessB1);

      // Transient is fresh everywhere
      const trA1 = scopeA.resolve<TransientService>('Transient');
      const trA2 = scopeA.resolve<TransientService>('Transient');
      expect(trA1).not.toBe(trA2);
    });
  });

  describe('4. DependencyContainer Scope Delegation & Singleton Accessors', () => {
    it('should create child scope from DependencyContainer and verify accessors', () => {
      const rootContainer = new DependencyContainer();
      rootContainer.collection().addSingleton('Logger', LoggerService);
      rootContainer.collection().addScoped('UserSession', UserSessionService);

      const scopeContainerA = rootContainer.createScope();
      const scopeContainerB = rootContainer.createScope();

      const logA = scopeContainerA.resolve<LoggerService>('Logger');
      const logB = scopeContainerB.resolve<LoggerService>('Logger');
      expect(logA).toBe(logB);

      const sessA = scopeContainerA.resolve<UserSessionService>('UserSession');
      const sessB = scopeContainerB.resolve<UserSessionService>('UserSession');
      expect(sessA).not.toBe(sessB);

      scopeContainerA.disposeScope();

      const sp1 = getServiceProvider();
      expect(sp1).toBeDefined();

      const customSP = new ServiceProvider();
      setServiceProvider(customSP);
      expect(getServiceProvider()).toBe(customSP);

      const dc1 = getDependencyContainer();
      expect(dc1).toBeDefined();

      const customDC = new DependencyContainer();
      setDependencyContainer(customDC);
      expect(getDependencyContainer()).toBe(customDC);

      const desc = new ServiceDescriptor('S1', ServiceLifetime.SINGLETON, LoggerService);
      expect(desc.serviceType).toBe('S1');
    });
  });

  describe('5. Telemetry & Statistics Integration', () => {
    it('should track scope statistics and diagnostics telemetry', () => {
      const collection = new ServiceCollection();
      collection.addScoped('Session', UserSessionService);

      const root = new ServiceProvider(collection);
      const scopeA = root.createScope();
      const scopeB = root.createScope();

      scopeA.resolve('Session');
      scopeA.resolve('Session');

      const stats = root.statistics();
      expect(stats.scopesCreated).toBe(2);
      expect(stats.scopedCacheHits).toBe(1);
      expect(stats.scopedInstancesCreated).toBe(1);

      const diag = (scopeA as IServiceProvider).diagnostics();
      expect(diag.activeScopes.length).toBeGreaterThan(0);
      expect(diag.scopedCacheSize).toBe(1);

      scopeB.disposeScope();
      expect(root.statistics().scopesDisposed).toBe(1);
    });
  });
});
