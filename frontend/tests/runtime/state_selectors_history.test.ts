import { beforeEach, describe, expect, it } from 'vitest';
import {
  createPersistenceRecord,
  createRedoRecord,
  createSelector,
  createSelectorResult,
  createStateHistory,
  createSynchronizationRecord,
  createUndoRecord,
  HistoryManager,
  PersistenceManager,
  resetStateProvider,
  resetStateRuntime,
  SelectorEngine,
  SelectorException,
  StateCertifier,
  StateContainerEngine,
  StateProvider,
  StateRuntime,
  StateSynchronizer,
  UndoRedoManager,
} from '../../src/runtime/state';

describe('Phase 16.5 — Selectors, History, Persistence & Certification Engine', () => {
  beforeEach(() => {
    resetStateRuntime();
    resetStateProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable Selector and SelectorResult models', () => {
      const sel = createSelector({ name: 'SelectCount', select: (s: any) => s.count });
      expect(sel.name).toBe('SelectCount');
      expect(Object.isFrozen(sel)).toBe(true);

      const res = createSelectorResult({ value: 42, memoized: true });
      expect(res.value).toBe(42);
      expect(res.memoized).toBe(true);
      expect(Object.isFrozen(res)).toBe(true);
    });

    it('should create immutable StateHistory, UndoRecord, and RedoRecord models', () => {
      const hist = createStateHistory({ maxSize: 100 });
      expect(hist.maxSize).toBe(100);
      expect(Object.isFrozen(hist)).toBe(true);

      const undo = createUndoRecord({ previousState: { val: 1 } });
      expect(undo.previousState).toEqual({ val: 1 });
      expect(Object.isFrozen(undo)).toBe(true);

      const redo = createRedoRecord({ nextState: { val: 2 } });
      expect(redo.nextState).toEqual({ val: 2 });
      expect(Object.isFrozen(redo)).toBe(true);
    });

    it('should create immutable PersistenceRecord and SynchronizationRecord models', () => {
      const prec = createPersistenceRecord({ containerId: 'c1', key: 'k1', version: 1 });
      expect(prec.containerId).toBe('c1');
      expect(prec.key).toBe('k1');
      expect(Object.isFrozen(prec)).toBe(true);

      const syncRec = createSynchronizationRecord({ sourceContainerId: 's1', targetContainerId: 't1' });
      expect(syncRec.sourceContainerId).toBe('s1');
      expect(Object.isFrozen(syncRec)).toBe(true);
    });
  });

  describe('2. SelectorEngine & Memoization', () => {
    it('should register and evaluate selector function', () => {
      const selectorEngine = new SelectorEngine();
      const sel = createSelector({ selectorId: 'sel1', name: 'GetCount', select: (state: any) => state.count });

      selectorEngine.registerSelector(sel);
      const res = selectorEngine.evaluate('sel1', { count: 10 });

      expect(res.value).toBe(10);
      expect(res.memoized).toBe(false);
    });

    it('should return memoized result on consecutive evaluations with identical state reference', () => {
      const selectorEngine = new SelectorEngine();
      selectorEngine.registerSelector(createSelector({ selectorId: 'sel1', name: 'GetCount', select: (s: any) => s.count }));

      const stateObj = { count: 20 };
      const res1 = selectorEngine.evaluate('sel1', stateObj);
      expect(res1.memoized).toBe(false);

      const res2 = selectorEngine.evaluate('sel1', stateObj);
      expect(res2.memoized).toBe(true);
      expect(res2.value).toBe(20);
    });

    it('should throw SelectorException when evaluating unregistered selector', () => {
      const selectorEngine = new SelectorEngine();
      expect(() => selectorEngine.evaluate('invalid_id', {})).toThrow(SelectorException);
    });

    it('should clear selector cache', () => {
      const selectorEngine = new SelectorEngine();
      selectorEngine.registerSelector(createSelector({ selectorId: 'sel1', name: 'S1', select: (s: any) => s.x }));

      const stateObj = { x: 5 };
      selectorEngine.evaluate('sel1', stateObj);

      selectorEngine.clearCache();
      const res = selectorEngine.evaluate('sel1', stateObj);
      expect(res.memoized).toBe(false);
    });
  });

  describe('3. HistoryManager & UndoRedoManager Engine', () => {
    it('should push snapshots and execute undo / redo operations', () => {
      const historyManager = new HistoryManager<{ count: number }>();
      historyManager.pushSnapshot('c1', { count: 1 });
      historyManager.pushSnapshot('c1', { count: 2 });
      historyManager.pushSnapshot('c1', { count: 3 });

      expect(historyManager.canUndo()).toBe(true);
      expect(historyManager.canRedo()).toBe(false);

      const undo1 = historyManager.undo();
      expect(undo1?.previousState).toEqual({ count: 2 });

      expect(historyManager.canRedo()).toBe(true);
      const redo1 = historyManager.redo();
      expect(redo1?.nextState).toEqual({ count: 3 });
    });

    it('should support UndoRedoManager wrapper', () => {
      const manager = new UndoRedoManager<{ a: number }>();
      manager.pushSnapshot('c1', { a: 10 });
      manager.pushSnapshot('c1', { a: 20 });

      const undo = manager.undo();
      expect(undo?.previousState).toEqual({ a: 10 });
      expect(manager.canRedo()).toBe(true);
    });
  });

  describe('4. PersistenceManager & StateSynchronizer Engines', () => {
    it('should save, load, and clear state records in PersistenceManager', () => {
      const persistenceManager = new PersistenceManager();
      const rec = persistenceManager.save('cnt1', 'user_key', { name: 'Bob' });

      expect(rec.containerId).toBe('cnt1');
      expect(rec.version).toBe(1);

      const loaded = persistenceManager.load('cnt1', 'user_key');
      expect(loaded).toEqual({ name: 'Bob' });

      expect(persistenceManager.snapshot().length).toBe(1);

      persistenceManager.clear('cnt1');
      expect(persistenceManager.load('cnt1', 'user_key')).toBeUndefined();
    });

    it('should synchronize containers and detect version conflicts via StateSynchronizer', () => {
      const synchronizer = new StateSynchronizer();
      const c1 = new StateContainerEngine('c1', { v: 1 });
      const c2 = new StateContainerEngine('c2', { v: 2 });

      const syncRec = synchronizer.synchronize(c1.getContainer(), c2.getContainer());
      expect(syncRec.sourceContainerId).toBe(c1.getContainer().containerId);
      expect(syncRec.targetContainerId).toBe(c2.getContainer().containerId);
      expect(syncRec.conflictDetected).toBe(true);
    });
  });

  describe('5. StateCertifier Engine & Report Generation', () => {
    it('should certify operational StateProvider and produce 100/100 report', () => {
      const provider = new StateProvider();
      provider.initialize();

      const certifier = new StateCertifier();
      const report = certifier.runCertification(provider);

      expect(report.certification.certified).toBe(true);
      expect(report.certification.score).toBe(100);
      expect(report.summary.status).toBe('PASSED');
    });

    it('should return certification snapshot via certify()', () => {
      const provider = new StateProvider();
      provider.initialize();

      const certifier = new StateCertifier();
      const cert = certifier.certify(provider);

      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
    });
  });

  describe('6. Provider & Runtime Coordinator Integration', () => {
    it('should delegate selectors, history, persistence, and certification via StateProvider and StateRuntime', () => {
      const provider = new StateProvider();
      provider.initialize();
      const runtime = new StateRuntime(provider);

      runtime.createContainer('app', { count: 1 });
      runtime.setState('app', { count: 2 });

      runtime.registerSelector('app_count', (s: any) => s.count);
      const res = runtime.select('app_count', { count: 2 });
      expect(res.value).toBe(2);

      const undo = runtime.undo();
      expect(undo?.previousState).toEqual({ count: 1 });

      const prec = runtime.save('app', 'save_1');
      expect(prec.version).toBe(1);

      const cert = runtime.certify();
      expect(cert.certified).toBe(true);
    });
  });
});
