import { beforeEach, describe, expect, it } from 'vitest';
import { ServiceRegistry, createPluginService } from '../../src/runtime/plugins';

describe('Phase 16.7 — Service Registry Engine Tests', () => {
  let registry: ServiceRegistry;

  beforeEach(() => {
    registry = new ServiceRegistry();
  });

  describe('1. Service Resolution & Scopes', () => {
    it('should register and resolve a singleton service instance', () => {
      let factoryRunCount = 0;
      const svc = createPluginService({
        id: 'svc1',
        pluginId: 'p1',
        interfaceName: 'ILogService',
        scope: 'singleton',
      });

      registry.registerService('p1', svc, () => {
        factoryRunCount++;
        return { name: 'LogInstance' };
      });

      const inst1 = registry.resolveService<any>('ILogService');
      const inst2 = registry.resolveService<any>('ILogService');

      expect(inst1).toBeDefined();
      expect(inst1.name).toBe('LogInstance');
      expect(inst2).toBe(inst1);
      expect(factoryRunCount).toBe(1);
    });

    it('should register and resolve a transient service instance on every call', () => {
      let factoryRunCount = 0;
      const svc = createPluginService({
        id: 'svc2',
        pluginId: 'p1',
        interfaceName: 'IDatabaseConnection',
        scope: 'transient',
      });

      registry.registerService('p1', svc, () => {
        factoryRunCount++;
        return { connId: factoryRunCount };
      });

      const inst1 = registry.resolveService<any>('IDatabaseConnection');
      const inst2 = registry.resolveService<any>('IDatabaseConnection');

      expect(inst1.connId).toBe(1);
      expect(inst2.connId).toBe(2);
      expect(factoryRunCount).toBe(2);
    });

    it('should throw error when registering duplicate service interface', () => {
      const svc = createPluginService({ id: 's1', pluginId: 'p1', interfaceName: 'ISame' });
      registry.registerService('p1', svc, () => ({}));

      expect(() => registry.registerService('p1', svc, () => ({}))).toThrow();
    });

    it('should replace a service registry dynamically', () => {
      const svc = createPluginService({ id: 's1', pluginId: 'p1', interfaceName: 'ISame' });
      registry.registerService('p1', svc, () => 'old');

      registry.replaceService('p1', svc, () => 'new');
      expect(registry.resolveService('ISame')).toBe('new');
    });

    it('should return undefined when resolving non-existent service', () => {
      expect(registry.resolveService('INothing')).toBeUndefined();
    });

    it('should clear all service registrations', () => {
      const svc = createPluginService({ id: 's1', pluginId: 'p1', interfaceName: 'ISame' });
      registry.registerService('p1', svc, () => 'old');
      registry.clear();

      expect(registry.resolveService('ISame')).toBeUndefined();
    });
  });
});
