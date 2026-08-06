import { beforeEach, describe, expect, it } from 'vitest';
import {
  createApplicationState,
  createStateCapabilities,
  createStateContainer,
  createStateContext,
  createStateHealth,
  createStateMetadata,
  createStateSnapshot,
  createStateStatistics,
  createStoreHealth,
  createStoreSnapshot,
  createStoreStatistics,
  getStateProvider,
  getStateRuntime,
  resetStateProvider,
  resetStateRuntime,
  StateContainerEngine,
  StateProvider,
  StateProviderException,
  StateRegistry,
  StateRuntime,
  StateStore,
  StateValidationException,
} from '../../src/runtime/state';

describe('Phase 16.5 — State Runtime Foundation, Containers & Stores', () => {
  beforeEach(() => {
    resetStateRuntime();
    resetStateProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable StateContainer model', () => {
      const container = createStateContainer({ name: 'user_profile', state: { name: 'Alice' } });
      expect(container.name).toBe('user_profile');
      expect(container.state).toEqual({ name: 'Alice' });
      expect(container.version).toBe(1);
      expect(Object.isFrozen(container)).toBe(true);
    });

    it('should create immutable StateSnapshot model', () => {
      const snap = createStateSnapshot({ containerId: 'c1', state: { count: 5 } });
      expect(snap.containerId).toBe('c1');
      expect(snap.state).toEqual({ count: 5 });
      expect(Object.isFrozen(snap)).toBe(true);
    });

    it('should create immutable StateMetadata and StateContext models', () => {
      const meta = createStateMetadata({ environment: 'test' });
      expect(meta.environment).toBe('test');
      expect(Object.isFrozen(meta)).toBe(true);

      const ctx = createStateContext({ environment: 'production' });
      expect(ctx.environment).toBe('production');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create immutable StateCapabilities, StateStatistics, and StateHealth models', () => {
      const caps = createStateCapabilities();
      expect(caps.supportsContainers).toBe(true);
      expect(Object.isFrozen(caps)).toBe(true);

      const stats = createStateStatistics({ initializations: 2 });
      expect(stats.initializations).toBe(2);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createStateHealth({ healthy: true });
      expect(health.healthy).toBe(true);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable ApplicationState, StoreSnapshot, StoreStatistics, StoreHealth models', () => {
      const appState = createApplicationState({ globalState: { theme: 'dark' } });
      expect(appState.globalState).toEqual({ theme: 'dark' });
      expect(Object.isFrozen(appState)).toBe(true);

      const ss = createStoreSnapshot({ storeId: 's1', state: {} });
      expect(ss.storeId).toBe('s1');
      expect(Object.isFrozen(ss)).toBe(true);

      const storeStats = createStoreStatistics({ readCount: 10 });
      expect(storeStats.readCount).toBe(10);
      expect(Object.isFrozen(storeStats)).toBe(true);

      const storeHealth = createStoreHealth({ healthy: true });
      expect(storeHealth.healthy).toBe(true);
      expect(Object.isFrozen(storeHealth)).toBe(true);
    });
  });

  describe('2. StateContainerEngine', () => {
    it('should create container engine and verify getState() and getContainer()', () => {
      const engine = new StateContainerEngine('counter', { val: 0 });
      expect(engine.getState()).toEqual({ val: 0 });
      expect(engine.getContainer().name).toBe('counter');
      expect(engine.getContainer().version).toBe(1);
    });

    it('should setState() and increment container version', () => {
      const engine = new StateContainerEngine('settings', { dark: false });
      const updated = engine.setState({ dark: true });

      expect(updated.state).toEqual({ dark: true });
      expect(updated.version).toBe(2);
      expect(engine.getState()).toEqual({ dark: true });
    });

    it('should replaceState()', () => {
      const engine = new StateContainerEngine('data', { a: 1 });
      const updated = engine.replaceState({ a: 2 });
      expect(updated.state).toEqual({ a: 2 });
    });

    it('should mergeState() into object state', () => {
      const engine = new StateContainerEngine('user', { name: 'Alice', age: 25 });
      const updated = engine.mergeState({ age: 26 });
      expect(updated.state).toEqual({ name: 'Alice', age: 26 });
    });

    it('should resetState() to initial state', () => {
      const engine = new StateContainerEngine('reset_test', { value: 100 });
      engine.setState({ value: 500 });
      expect(engine.getState()).toEqual({ value: 500 });

      const reset = engine.resetState();
      expect(reset.state).toEqual({ value: 100 });
    });

    it('should return cloned and frozen state via cloneState() and freezeState()', () => {
      const engine = new StateContainerEngine('freeze_test', { obj: { x: 1 } });
      const cloned = engine.cloneState();
      expect(cloned).toEqual({ obj: { x: 1 } });

      const frozen = engine.freezeState();
      expect(Object.isFrozen(frozen)).toBe(true);
    });

    it('should throw StateValidationException on empty name or null initial state', () => {
      expect(() => new StateContainerEngine('   ', {})).toThrow(StateValidationException);
      expect(() => new StateContainerEngine('valid', null as any)).toThrow(StateValidationException);
    });
  });

  describe('3. StateStore Engine', () => {
    it('should create and retrieve state containers from StateStore', () => {
      const store = new StateStore();
      const container = store.createContainer('app_config', { version: '1.0' });

      expect(container.name).toBe('app_config');
      expect(store.getContainer('app_config')?.name).toBe('app_config');
      expect(store.listContainers().length).toBe(1);
    });

    it('should reject creation of duplicate container name', () => {
      const store = new StateStore();
      store.createContainer('c1', { x: 1 });
      expect(() => store.createContainer('c1', { x: 2 })).toThrow(StateProviderException);
    });

    it('should remove container by name', () => {
      const store = new StateStore();
      store.createContainer('temp', { a: 1 });

      expect(store.removeContainer('temp')).toBe(true);
      expect(store.getContainer('temp')).toBeUndefined();
    });

    it('should capture store snapshot and track read/write statistics', () => {
      const store = new StateStore();
      store.createContainer('c1', { val: 10 });
      store.createContainer('c2', { val: 20 });

      const snapshot = store.snapshotStore();
      expect(snapshot.state).toEqual({ c1: { val: 10 }, c2: { val: 20 } });

      const stats = store.statistics();
      expect(stats.writeCount).toBe(2);
    });
  });

  describe('4. StateRegistry Engine', () => {
    it('should register and discover stores and containers in StateRegistry', () => {
      const registry = new StateRegistry();
      const store = new StateStore('s1');
      const container = createStateContainer({ name: 'cnt1', state: {} });

      registry.registerStore('s1', store);
      registry.registerContainer(container);

      expect(registry.getStore('s1')).toBe(store);
      expect(registry.getContainer('cnt1')).toBe(container);
      expect(registry.listStores()).toEqual(['s1']);
      expect(registry.listContainers().length).toBe(1);
    });

    it('should unregister stores and containers', () => {
      const registry = new StateRegistry();
      registry.registerStore('s1', new StateStore('s1'));
      registry.registerContainer(createStateContainer({ name: 'c1', state: {} }));

      expect(registry.unregisterStore('s1')).toBe(true);
      expect(registry.unregisterContainer('c1')).toBe(true);
      expect(registry.getStore('s1')).toBeUndefined();
      expect(registry.getContainer('c1')).toBeUndefined();
    });

    it('should clear all registered stores and containers', () => {
      const registry = new StateRegistry();
      registry.registerStore('s1', new StateStore('s1'));
      registry.registerContainer(createStateContainer({ name: 'c1', state: {} }));

      registry.clear();
      expect(registry.listStores().length).toBe(0);
      expect(registry.listContainers().length).toBe(0);
    });
  });

  describe('5. Provider & Runtime Delegation', () => {
    it('should initialize, shutdown, and restart StateProvider', () => {
      const provider = new StateProvider();
      expect(provider.health().healthy).toBe(false);

      provider.initialize();
      expect(provider.health().healthy).toBe(true);

      provider.shutdown();
      expect(provider.health().healthy).toBe(false);

      provider.restart();
      expect(provider.health().healthy).toBe(true);
    });

    it('should delegate container operations through StateProvider', () => {
      const provider = new StateProvider();
      provider.initialize();

      const container = provider.createContainer('session', { loggedIn: false });
      expect(container.name).toBe('session');

      provider.setState('session', { loggedIn: true });
      expect(provider.getState('session')).toEqual({ loggedIn: true });
    });

    it('should delegate operations through StateRuntime coordinator', () => {
      const runtime = new StateRuntime();
      runtime.initialize();

      runtime.createContainer('ui', { theme: 'light' });
      runtime.setState('ui', { theme: 'dark' });

      expect(runtime.getState('ui')).toEqual({ theme: 'dark' });
      expect(runtime.diagnostics().containersCount).toBe(1);
    });

    it('should support singleton runtime helpers (getStateRuntime, getStateProvider)', () => {
      const runtime = getStateRuntime();
      const provider = getStateProvider();

      provider.initialize();
      runtime.createContainer('glob', { active: true });

      expect(runtime.getState('glob')).toEqual({ active: true });
    });
  });
});
