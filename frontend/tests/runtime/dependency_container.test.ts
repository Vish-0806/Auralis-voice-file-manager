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

describe('Phase 16.2.2 — Frontend Dependency Injection Service Registration Engine', () => {
  beforeEach(() => {
    resetDependencyContainer();
    resetServiceProvider();
  });

  describe('1. Immutable Models & Enums', () => {
    it('should verify ServiceLifetime and ContainerState enums', () => {
      expect(ServiceLifetime.SINGLETON).toBe('SINGLETON');
      expect(ServiceLifetime.TRANSIENT).toBe('TRANSIENT');
      expect(ServiceLifetime.SCOPED).toBe('SCOPED');

      expect(ContainerState.UNINITIALIZED).toBe('UNINITIALIZED');
      expect(ContainerState.READY).toBe('READY');
      expect(ContainerState.STOPPED).toBe('STOPPED');
    });

    it('should create default frozen ContainerConfiguration', () => {
      const config = createContainerConfiguration();
      expect(config.name).toBe('Auralis Container');
      expect(config.enableCircularCheck).toBe(true);
      expect(config.maxDepth).toBe(32);
      expect(config.validateOnBuild).toBe(true);
      expect(Object.isFrozen(config)).toBe(true);
    });

    it('should create extended ContainerCapabilities with aliases and replacement flags', () => {
      const caps = createContainerCapabilities();
      expect(caps.supportsScoped).toBe(true);
      expect(caps.supportsFactories).toBe(true);
      expect(caps.supportsInstances).toBe(true);
      expect(caps.supportsCircularDetection).toBe(true);
      expect(caps.supportsAliases).toBe(true);
      expect(caps.supportsTags).toBe(true);
      expect(caps.supportsReplacement).toBe(true);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create ServiceDescriptorModel with aliases and tags', () => {
      const model = createServiceDescriptorModel({
        descriptorId: 'd1',
        serviceType: 'IService',
        lifetime: ServiceLifetime.SINGLETON,
        aliases: ['Alias1'],
        tags: ['tag1'],
      });
      expect(model.descriptorId).toBe('d1');
      expect(model.serviceType).toBe('IService');
      expect(model.aliases).toContain('Alias1');
      expect(model.tags).toContain('tag1');
      expect(Object.isFrozen(model.aliases)).toBe(true);
      expect(Object.isFrozen(model.tags)).toBe(true);
      expect(Object.isFrozen(model)).toBe(true);
    });

    it('should exercise helper model factories', () => {
      const health = createContainerHealth();
      expect(health.healthy).toBe(false);

      const stats = createContainerStatistics();
      expect(stats.totalRegistrations).toBe(0);

      const ctx = createContainerContext();
      expect(ctx.containerId).toBe('default-container');

      const diag = createContainerDiagnostics();
      expect(diag.state).toBe(ContainerState.UNINITIALIZED);

      const node = createDependencyNode({ serviceType: 'S1', dependencies: ['D1'] });
      expect(node.dependencies).toContain('D1');

      const reg = createServiceRegistration({ descriptorId: 'desc_1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON });
      expect(reg.serviceType).toBe('S1');
    });
  });

  describe('2. Exception Hierarchy', () => {
    it('should verify exception hierarchy and instances', () => {
      const e1 = new DependencyInjectionException('base');
      const e2 = new ServiceRegistrationException('reg');
      const e3 = new ServiceResolutionException('res');
      const e4 = new CircularDependencyException('circ');
      const e5 = new ServiceValidationException('val');

      expect(e1).toBeInstanceOf(Error);
      expect(e2).toBeInstanceOf(DependencyInjectionException);
      expect(e3).toBeInstanceOf(DependencyInjectionException);
      expect(e4).toBeInstanceOf(DependencyInjectionException);
      expect(e5).toBeInstanceOf(DependencyInjectionException);
    });
  });

  describe('3. ServiceDescriptor Extensions & Equality', () => {
    it('should generate unique descriptorId, aliases, tags, and registeredAt', () => {
      const desc = new ServiceDescriptor(
        'DummyService',
        ServiceLifetime.SINGLETON,
        DummyService,
        { role: 'test' },
        { aliases: ['DummyAlias'], tags: ['tagA'] },
      );

      expect(desc.descriptorId).toBeDefined();
      expect(desc.descriptorId.startsWith('desc_')).toBe(true);
      expect(desc.serviceType).toBe('DummyService');
      expect(desc.aliases).toEqual(['DummyAlias']);
      expect(desc.tags).toEqual(['tagA']);
      expect(desc.registeredAt).toBeDefined();
      expect(Object.isFrozen(desc.aliases)).toBe(true);
      expect(Object.isFrozen(desc.tags)).toBe(true);
    });

    it('should verify equals() comparison between descriptors', () => {
      const d1 = new ServiceDescriptor('S1', ServiceLifetime.SINGLETON, DummyService);
      const d2 = new ServiceDescriptor(
        'S1',
        ServiceLifetime.TRANSIENT,
        () => new DummyService(),
      );
      const d3 = new ServiceDescriptor('S2', ServiceLifetime.SINGLETON, DummyService);

      expect(d1.equals(d2)).toBe(true);
      expect(d1.equals(d3)).toBe(false);
    });
  });

  describe('4. ServiceCollection Registration Engine', () => {
    it('should register singletons, transients, and scopeds with aliases', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService, undefined, { aliases: ['A1'] });
      collection.addTransient('S2', () => new DummyService(), undefined, { aliases: ['A2'] });
      collection.addScoped('S3', DummyService);

      expect(collection.count()).toBe(3);
      expect(collection.contains('S1')).toBe(true);
      expect(collection.containsAlias('A1')).toBe(true);
      expect(collection.containsAlias('A2')).toBe(true);

      const fetchedByAlias = collection.getDescriptorByAlias('A1');
      expect(fetchedByAlias).toBeDefined();
      expect(fetchedByAlias?.serviceType).toBe('S1');
    });

    it('should reject duplicate service types and throw ServiceRegistrationException', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);

      expect(() => collection.addSingleton('S1', DummyService)).toThrow(
        ServiceRegistrationException,
      );
    });

    it('should reject alias conflicts with existing service types or aliases', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService, undefined, { aliases: ['A1'] });

      expect(() =>
        collection.addSingleton('S2', DummyService, undefined, { aliases: ['S1'] }),
      ).toThrow(ServiceRegistrationException);

      expect(() =>
        collection.addSingleton('S3', DummyService, undefined, { aliases: ['A1'] }),
      ).toThrow(ServiceRegistrationException);
    });

    it('should replace existing service registration using replace()', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService, undefined, { aliases: ['OldAlias'] });

      const newDesc = new ServiceDescriptor(
        'S1',
        ServiceLifetime.TRANSIENT,
        () => new DummyService(),
        undefined,
        { aliases: ['NewAlias'] },
      );

      collection.replace(newDesc);

      expect(collection.count()).toBe(1);
      expect(collection.containsAlias('OldAlias')).toBe(false);
      expect(collection.containsAlias('NewAlias')).toBe(true);

      const updated = collection.getDescriptor('S1');
      expect(updated?.lifetime).toBe(ServiceLifetime.TRANSIENT);
      expect(collection.statistics().replacementsCount).toBe(1);
    });

    it('should safely attempt registration using tryAdd()', () => {
      const collection = new ServiceCollection();
      const d1 = new ServiceDescriptor('S1', ServiceLifetime.SINGLETON, DummyService);
      const d2 = new ServiceDescriptor('S1', ServiceLifetime.TRANSIENT, () => new DummyService());

      expect(collection.tryAdd(d1)).toBe(true);
      expect(collection.tryAdd(d2)).toBe(false);
      expect(collection.count()).toBe(1);
      expect(collection.statistics().rejectedRegistrationsCount).toBe(1);
    });

    it('should list descriptors by lifetime', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);
      collection.addSingleton('S2', DummyService);
      collection.addTransient('T1', () => new DummyService());

      const singletons = collection.listByLifetime(ServiceLifetime.SINGLETON);
      const transients = collection.listByLifetime(ServiceLifetime.TRANSIENT);

      expect(singletons.length).toBe(2);
      expect(transients.length).toBe(1);
    });

    it('should remove services and clean up alias mappings', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService, undefined, { aliases: ['A1'] });

      expect(collection.remove('S1')).toBe(true);
      expect(collection.contains('S1')).toBe(false);
      expect(collection.containsAlias('A1')).toBe(false);
      expect(collection.statistics().removalsCount).toBe(1);
    });

    it('should remove services matching predicate using removeAll()', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService, undefined, { tags: ['deprecated'] });
      collection.addSingleton('S2', DummyService, undefined, { tags: ['active'] });

      const removed = collection.removeAll((d) => d.tags.includes('deprecated'));
      expect(removed).toBe(1);
      expect(collection.contains('S1')).toBe(false);
      expect(collection.contains('S2')).toBe(true);
    });
  });

  describe('5. Container & Singleton Accessors Integration', () => {
    it('should instantiate DependencyContainer and verify singleton helpers', () => {
      const container = new DependencyContainer();
      expect(container.state()).toBe(ContainerState.UNINITIALIZED);

      const health = container.initialize();
      expect(health.healthy).toBe(true);
      expect(container.state()).toBe(ContainerState.READY);

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
    });
  });
});
