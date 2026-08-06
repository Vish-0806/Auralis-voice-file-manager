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

describe('Phase 16.2.1 — Frontend Dependency Injection Foundation', () => {
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

    it('should create default frozen ContainerCapabilities', () => {
      const caps = createContainerCapabilities();
      expect(caps.supportsScoped).toBe(true);
      expect(caps.supportsFactories).toBe(true);
      expect(caps.supportsInstances).toBe(true);
      expect(caps.supportsCircularDetection).toBe(true);
      expect(caps.maxDepth).toBe(32);
      expect(Object.isFrozen(caps)).toBe(true);
    });

    it('should create default frozen ContainerHealth', () => {
      const health = createContainerHealth();
      expect(health.healthy).toBe(false);
      expect(health.state).toBe(ContainerState.UNINITIALIZED);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create default frozen ContainerStatistics', () => {
      const stats = createContainerStatistics();
      expect(stats.totalRegistrations).toBe(0);
      expect(stats.singletonCount).toBe(0);
      expect(stats.transientCount).toBe(0);
      expect(stats.scopedCount).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create default frozen ContainerContext and Diagnostics', () => {
      const ctx = createContainerContext();
      expect(ctx.containerId).toBe('default-container');
      expect(Object.isFrozen(ctx)).toBe(true);

      const diag = createContainerDiagnostics();
      expect(diag.state).toBe(ContainerState.UNINITIALIZED);
      expect(Object.isFrozen(diag)).toBe(true);
    });

    it('should create ServiceDescriptorModel and DependencyNode correctly', () => {
      const model = createServiceDescriptorModel({
        serviceType: 'IService',
        lifetime: ServiceLifetime.SINGLETON,
      });
      expect(model.serviceType).toBe('IService');
      expect(Object.isFrozen(model)).toBe(true);

      const node = createDependencyNode({
        serviceType: 'IService',
        dependencies: ['IDepA'],
      });
      expect(node.dependencies).toContain('IDepA');
      expect(Object.isFrozen(node)).toBe(true);

      const reg = createServiceRegistration({
        serviceType: 'IService',
        lifetime: ServiceLifetime.TRANSIENT,
      });
      expect(reg.serviceType).toBe('IService');
      expect(Object.isFrozen(reg)).toBe(true);
    });
  });

  describe('2. Exception Hierarchy', () => {
    it('should instantiate DependencyInjectionException', () => {
      const err = new DependencyInjectionException('Base error');
      expect(err).toBeInstanceOf(Error);
      expect(err).toBeInstanceOf(DependencyInjectionException);
      expect(err.name).toBe('DependencyInjectionException');
    });

    it('should instantiate ServiceRegistrationException', () => {
      const err = new ServiceRegistrationException('Reg error');
      expect(err).toBeInstanceOf(DependencyInjectionException);
      expect(err.name).toBe('ServiceRegistrationException');
    });

    it('should instantiate ServiceResolutionException', () => {
      const err = new ServiceResolutionException('Res error');
      expect(err).toBeInstanceOf(DependencyInjectionException);
      expect(err.name).toBe('ServiceResolutionException');
    });

    it('should instantiate CircularDependencyException', () => {
      const err = new CircularDependencyException('Circ error');
      expect(err).toBeInstanceOf(DependencyInjectionException);
      expect(err.name).toBe('CircularDependencyException');
    });

    it('should instantiate ServiceValidationException', () => {
      const err = new ServiceValidationException('Val error');
      expect(err).toBeInstanceOf(DependencyInjectionException);
      expect(err.name).toBe('ServiceValidationException');
    });
  });

  describe('3. ServiceDescriptor & Validation', () => {
    it('should construct class implementation descriptor', () => {
      const desc = new ServiceDescriptor('DummyService', ServiceLifetime.SINGLETON, DummyService);
      expect(desc.serviceType).toBe('DummyService');
      expect(desc.lifetime).toBe(ServiceLifetime.SINGLETON);
      expect(desc.implementation).toBe(DummyService);
      expect(desc.factory).toBeUndefined();
      expect(desc.instance).toBeUndefined();
      expect(desc.toModel().implementationType).toBe('DummyService');
    });

    it('should construct factory descriptor', () => {
      const factory = () => new DummyService();
      const desc = new ServiceDescriptor('DummyService', ServiceLifetime.TRANSIENT, factory);
      expect(desc.factory).toBe(factory);
      expect(desc.toModel().hasFactory).toBe(true);
    });

    it('should construct instance descriptor for SINGLETON', () => {
      const instance = new DummyService();
      const desc = new ServiceDescriptor('DummyService', ServiceLifetime.SINGLETON, instance);
      expect(desc.instance).toBe(instance);
      expect(desc.toModel().hasInstance).toBe(true);
    });

    it('should throw exception if non-singleton attempts instance registration', () => {
      const instance = new DummyService();
      expect(
        () => new ServiceDescriptor('DummyService', ServiceLifetime.TRANSIENT, instance),
      ).toThrow(ServiceRegistrationException);
    });

    it('should throw exception on invalid serviceType or target', () => {
      expect(() => new ServiceDescriptor('', ServiceLifetime.SINGLETON, DummyService)).toThrow(
        ServiceRegistrationException,
      );
      expect(
        () => new ServiceDescriptor('DummyService', ServiceLifetime.SINGLETON, null),
      ).toThrow(ServiceRegistrationException);
    });
  });

  describe('4. ServiceCollection Operations', () => {
    it('should register singletons, transients, and scopeds', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);
      collection.addTransient('S2', () => new DummyService());
      collection.addScoped('S3', DummyService);

      expect(collection.count()).toBe(3);
      expect(collection.contains('S1')).toBe(true);
      expect(collection.contains('S2')).toBe(true);
      expect(collection.contains('S3')).toBe(true);
    });

    it('should list all registered services as frozen array', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);
      const list = collection.listServices();
      expect(list.length).toBe(1);
      expect(Object.isFrozen(list)).toBe(true);
    });

    it('should remove and clear services', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);
      expect(collection.remove('S1')).toBe(true);
      expect(collection.count()).toBe(0);

      collection.addSingleton('S1', DummyService);
      collection.clear();
      expect(collection.count()).toBe(0);
    });
  });

  describe('5. ServiceProvider & Telemetry', () => {
    it('should initialize and shutdown provider correctly', () => {
      const provider = new ServiceProvider();
      expect(provider.state()).toBe(ContainerState.UNINITIALIZED);

      const healthReady = provider.initialize();
      expect(healthReady.healthy).toBe(true);
      expect(provider.state()).toBe(ContainerState.READY);

      const healthStopped = provider.shutdown();
      expect(healthStopped.healthy).toBe(false);
      expect(provider.state()).toBe(ContainerState.STOPPED);
    });

    it('should calculate statistics based on registrations', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('S1', DummyService);
      collection.addTransient('S2', () => new DummyService());
      collection.addScoped('S3', DummyService);

      const provider = new ServiceProvider(collection);
      const stats = provider.statistics();

      expect(stats.totalRegistrations).toBe(3);
      expect(stats.singletonCount).toBe(1);
      expect(stats.transientCount).toBe(1);
      expect(stats.scopedCount).toBe(1);
    });

    it('should throw Not Implemented ServiceResolutionException on resolve', () => {
      const provider = new ServiceProvider();
      expect(() => provider.resolve('DummyService')).toThrow(ServiceResolutionException);
      expect(() => provider.tryResolve('DummyService')).toThrow(ServiceResolutionException);
    });
  });

  describe('6. DependencyContainer & Singleton Accessors', () => {
    it('should instantiate DependencyContainer and delegate provider operations', () => {
      const container = new DependencyContainer();
      expect(container.state()).toBe(ContainerState.UNINITIALIZED);

      const health = container.initialize();
      expect(health.healthy).toBe(true);
      expect(container.state()).toBe(ContainerState.READY);
    });

    it('should manage global service provider singleton accessors', () => {
      const p1 = getServiceProvider();
      const p2 = getServiceProvider();
      expect(p1).toBe(p2);

      const customP = new ServiceProvider();
      setServiceProvider(customP);
      expect(getServiceProvider()).toBe(customP);

      resetServiceProvider();
      expect(getServiceProvider()).not.toBe(customP);
    });

    it('should manage global dependency container singleton accessors', () => {
      const c1 = getDependencyContainer();
      const c2 = getDependencyContainer();
      expect(c1).toBe(c2);

      const customC = new DependencyContainer();
      setDependencyContainer(customC);
      expect(getDependencyContainer()).toBe(customC);

      resetDependencyContainer();
      expect(getDependencyContainer()).not.toBe(customC);
    });
  });
});
