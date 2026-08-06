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

class DummyService {
  public getValue(): string {
    return 'dummy';
  }
}

class ServiceA {
  constructor(public b: ServiceB) {}
}

class ServiceB {
  constructor(public c: ServiceC) {}
}

class ServiceC {
  public name = 'ServiceC';
}

class CircA {
  constructor(public b: CircB) {}
}

class CircB {
  constructor(public a: CircA) {}
}

describe('Phase 16.2.3 — Frontend Dependency Resolution Engine', () => {
  beforeEach(() => {
    resetDependencyContainer();
    resetServiceProvider();
  });

  describe('1. Models, Capabilities & Exception Verification', () => {
    it('should verify ContainerDiagnostics and statistics model extensions', () => {
      const stats = createContainerStatistics({
        totalResolutions: 10,
        singletonCacheHits: 5,
        singletonCreations: 2,
        transientCreations: 3,
      });
      expect(stats.totalResolutions).toBe(10);
      expect(stats.singletonCacheHits).toBe(5);

      const diag = createContainerDiagnostics({
        registeredServices: ['S1'],
        resolvedServices: ['S1'],
        cachedSingletons: ['S1'],
      });
      expect(diag.registeredServices).toContain('S1');
      expect(diag.resolvedServices).toContain('S1');
      expect(Object.isFrozen(diag)).toBe(true);

      const caps = createContainerCapabilities();
      expect(caps.supportsScoped).toBe(true);

      const cfg = createContainerConfiguration();
      expect(cfg.name).toBe('Auralis Container');

      const ctx = createContainerContext();
      expect(ctx.containerId).toBe('default-container');

      const health = createContainerHealth();
      expect(health.healthy).toBe(false);

      const node = createDependencyNode({ serviceType: 'S1', dependencies: ['D1'] });
      expect(node.dependencies).toContain('D1');

      const model = createServiceDescriptorModel({ descriptorId: 'd1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON });
      expect(model.serviceType).toBe('S1');

      const reg = createServiceRegistration({ descriptorId: 'r1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON });
      expect(reg.serviceType).toBe('S1');
    });

    it('should verify exception types', () => {
      expect(new CircularDependencyException('circ')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceResolutionException('res')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceRegistrationException('reg')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceValidationException('val')).toBeInstanceOf(DependencyInjectionException);
    });
  });

  describe('2. Singleton Lifetime & Caching', () => {
    it('should cache and reuse singleton instances', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('DummyService', DummyService);

      const provider = new ServiceProvider(collection);
      const instance1 = provider.resolve<DummyService>('DummyService');
      const instance2 = provider.resolve<DummyService>('DummyService');

      expect(instance1).toBe(instance2);
      expect(instance1.getValue()).toBe('dummy');

      const stats = provider.statistics();
      expect(stats.totalResolutions).toBe(2);
      expect(stats.singletonCacheHits).toBe(1);
      expect(stats.singletonCreations).toBe(1);
    });

    it('should resolve singleton instances registered directly', () => {
      const collection = new ServiceCollection();
      const directInstance = new DummyService();
      collection.addSingleton('DummyService', directInstance);

      const provider = new ServiceProvider(collection);
      const res = provider.resolve<DummyService>('DummyService');
      expect(res).toBe(directInstance);
    });
  });

  describe('3. Transient Lifetime', () => {
    it('should create a new instance on every resolution for TRANSIENT services', () => {
      const collection = new ServiceCollection();
      collection.addTransient('DummyService', () => new DummyService());

      const provider = new ServiceProvider(collection);
      const i1 = provider.resolve<DummyService>('DummyService');
      const i2 = provider.resolve<DummyService>('DummyService');

      expect(i1).not.toBe(i2);
      expect(i1.getValue()).toBe('dummy');

      const stats = provider.statistics();
      expect(stats.transientCreations).toBe(2);
      expect(stats.factoryExecutions).toBe(2);
    });
  });

  describe('4. Factory Execution', () => {
    it('should execute factory functions passing ServiceProvider', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('DepC', ServiceC);
      collection.addTransient('FactoryB', (sp: IServiceProvider) => {
        const c = sp.resolve<ServiceC>('DepC');
        return new ServiceB(c);
      });

      const provider = new ServiceProvider(collection);
      const b = provider.resolve<ServiceB>('FactoryB');

      expect(b.c).toBeDefined();
      expect(b.c.name).toBe('ServiceC');
    });
  });

  describe('5. Recursive Constructor Dependency Injection', () => {
    it('should recursively resolve constructor dependencies declared in metadata', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('ServiceC', ServiceC);
      collection.addSingleton('ServiceB', ServiceB, { dependencies: ['ServiceC'] });
      collection.addSingleton('ServiceA', ServiceA, { dependencies: ['ServiceB'] });

      const provider = new ServiceProvider(collection);
      const a = provider.resolve<ServiceA>('ServiceA');

      expect(a).toBeDefined();
      expect(a.b).toBeDefined();
      expect(a.b.c).toBeDefined();
      expect(a.b.c.name).toBe('ServiceC');
    });

    it('should instantiate class directly via createInstance using static dependencies', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('ServiceC', ServiceC);
      collection.addSingleton('ServiceB', ServiceB, { dependencies: ['ServiceC'] });

      (ServiceA as any).$dependencies = ['ServiceB'];

      const provider = new ServiceProvider(collection);
      const a = provider.createInstance(ServiceA);

      expect(a.b.c.name).toBe('ServiceC');
    });
  });

  describe('6. Circular Dependency Detection', () => {
    it('should detect circular dependencies and throw CircularDependencyException', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('CircA', CircA, { dependencies: ['CircB'] });
      collection.addSingleton('CircB', CircB, { dependencies: ['CircA'] });

      const provider = new ServiceProvider(collection);
      expect(() => provider.resolve('CircA')).toThrow(CircularDependencyException);

      const stats = provider.statistics();
      expect(stats.circularDependencyDetections).toBe(1);
    });
  });

  describe('7. Resolution API Variants & Scoped Error', () => {
    it('should support tryResolve, resolveRequired, and resolveAll', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('DummyService', DummyService);

      const provider = new ServiceProvider(collection);
      expect(provider.resolveRequired<DummyService>('DummyService')).toBeDefined();
      expect(provider.tryResolve<DummyService>('NonExistent')).toBeUndefined();

      const all = provider.resolveAll<DummyService>('DummyService');
      expect(all.length).toBe(1);
      expect(provider.resolveAll('NonExistent').length).toBe(0);
    });

    it('should throw ServiceResolutionException on Scoped resolution in root provider', () => {
      const collection = new ServiceCollection();
      collection.addScoped('ScopedService', DummyService);

      const provider = new ServiceProvider(collection);
      expect(() => provider.resolve('ScopedService')).toThrow(ServiceResolutionException);
    });
  });

  describe('8. DependencyContainer & Singleton Accessors Integration', () => {
    it('should delegate resolution APIs from DependencyContainer and test singleton accessors', () => {
      const container = new DependencyContainer();
      container.collection().addSingleton('DummyService', DummyService);

      const resolved = container.resolve<DummyService>('DummyService');
      expect(resolved).toBeDefined();
      expect(resolved.getValue()).toBe('dummy');

      expect(container.resolveRequired<DummyService>('DummyService')).toBeDefined();
      expect(container.tryResolve('NonExistent')).toBeUndefined();
      expect(container.resolveAll('DummyService').length).toBe(1);

      const sp1 = getServiceProvider();
      const sp2 = getServiceProvider();
      expect(sp1).toBe(sp2);

      const customSP = new ServiceProvider();
      setServiceProvider(customSP);
      expect(getServiceProvider()).toBe(customSP);

      const dc1 = getDependencyContainer();
      const dc2 = getDependencyContainer();
      expect(dc1).toBe(dc2);

      const customDC = new DependencyContainer();
      setDependencyContainer(customDC);
      expect(getDependencyContainer()).toBe(customDC);

      const desc = new ServiceDescriptor('S1', ServiceLifetime.SINGLETON, DummyService);
      expect(desc.serviceType).toBe('S1');
      expect(container.state()).toBe(ContainerState.UNINITIALIZED);
    });
  });
});
