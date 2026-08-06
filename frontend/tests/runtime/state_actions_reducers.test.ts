import { beforeEach, describe, expect, it } from 'vitest';
import {
  ActionDispatcher,
  createAction,
  createActionContext,
  createMiddlewareExecution,
  createReducer,
  createReducerExecution,
  MiddlewareManager,
  ReducerEngine,
  ReducerException,
  resetStateProvider,
  resetStateRuntime,
  StateDispatchException,
  StateProvider,
  StateRuntime,
} from '../../src/runtime/state';

describe('Phase 16.5 — Actions, Reducers & Middleware Engine', () => {
  beforeEach(() => {
    resetStateRuntime();
    resetStateProvider();
  });

  describe('1. Action Models & Factory Functions', () => {
    it('should create immutable Action model', () => {
      const act = createAction({ type: 'ADD_ITEM', payload: { id: 'item1' } });
      expect(act.type).toBe('ADD_ITEM');
      expect(act.payload).toEqual({ id: 'item1' });
      expect(act.actionId).toBeDefined();
      expect(Object.isFrozen(act)).toBe(true);
    });

    it('should create immutable ActionContext model', () => {
      const ctx = createActionContext({ source: 'UI' });
      expect(ctx.source).toBe('UI');
      expect(Object.isFrozen(ctx)).toBe(true);
    });

    it('should create immutable ReducerExecution and MiddlewareExecution models', () => {
      const redExec = createReducerExecution({ reducerId: 'r1', actionType: 'ADD', success: true });
      expect(redExec.reducerId).toBe('r1');
      expect(redExec.success).toBe(true);
      expect(Object.isFrozen(redExec)).toBe(true);

      const mwExec = createMiddlewareExecution({ middlewareId: 'mw1', actionType: 'ADD', phase: 'BEFORE' });
      expect(mwExec.middlewareId).toBe('mw1');
      expect(mwExec.phase).toBe('BEFORE');
      expect(Object.isFrozen(mwExec)).toBe(true);
    });
  });

  describe('2. ActionDispatcher Engine', () => {
    it('should register action type and verify listActions()', () => {
      const dispatcher = new ActionDispatcher();
      dispatcher.registerAction('USER_LOGIN');

      expect(dispatcher.listActions()).toContain('USER_LOGIN');
    });

    it('should dispatch action and log to history', () => {
      const dispatcher = new ActionDispatcher();
      const act = dispatcher.dispatch(createAction({ type: 'PING', payload: {} }));

      expect(act.type).toBe('PING');
      expect(dispatcher.history().length).toBe(1);
      expect(dispatcher.history()[0].type).toBe('PING');
    });

    it('should dispatch asynchronous action via dispatchAsync()', async () => {
      const dispatcher = new ActionDispatcher();
      const act = await dispatcher.dispatchAsync(createAction({ type: 'ASYNC_ACT', payload: { x: 1 } }));

      expect(act.type).toBe('ASYNC_ACT');
      expect(dispatcher.history().length).toBe(1);
    });

    it('should throw StateDispatchException when dispatching null action', () => {
      const dispatcher = new ActionDispatcher();
      expect(() => dispatcher.dispatch(null as any)).toThrow(StateDispatchException);
    });

    it('should clear action history', () => {
      const dispatcher = new ActionDispatcher();
      dispatcher.dispatch(createAction({ type: 'A1', payload: {} }));

      expect(dispatcher.history().length).toBe(1);
      dispatcher.clearHistory();
      expect(dispatcher.history().length).toBe(0);
    });
  });

  describe('3. ReducerEngine', () => {
    it('should register reducer and execute reducers over state', () => {
      const reducerEngine = new ReducerEngine();
      const reducer = createReducer({
        name: 'CounterReducer',
        reduce: (state: any, action: any) => {
          if (action.type === 'INC') return { count: state.count + 1 };
          return state;
        },
      });

      reducerEngine.registerReducer(reducer);
      expect(reducerEngine.listReducers().length).toBe(1);

      const res = reducerEngine.executeReducers({ count: 0 }, { type: 'INC', payload: {} });
      expect(res.newState).toEqual({ count: 1 });
      expect(res.executions.length).toBe(1);
      expect(res.executions[0].success).toBe(true);
    });

    it('should isolate throwing reducers without halting execution', () => {
      const reducerEngine = new ReducerEngine();
      reducerEngine.registerReducer(
        createReducer({
          name: 'FaultyReducer',
          reduce: () => {
            throw new Error('Reducer error');
          },
        }),
      );

      const res = reducerEngine.executeReducers({ count: 0 }, { type: 'TEST', payload: {} });
      expect(res.newState).toEqual({ count: 0 }); // Preserves previous state
      expect(res.executions[0].success).toBe(false);
      expect(res.executions[0].error).toContain('Reducer error');
    });

    it('should reject duplicate reducer registration', () => {
      const reducerEngine = new ReducerEngine();
      const r1 = createReducer({ reducerId: 'r1', name: 'R1', reduce: (s) => s });
      const r2 = createReducer({ reducerId: 'r1', name: 'R2', reduce: (s) => s });

      reducerEngine.registerReducer(r1);
      expect(() => reducerEngine.registerReducer(r2)).toThrow(ReducerException);
    });
  });

  describe('4. MiddlewareManager Engine', () => {
    it('should execute before and after middleware hooks during action dispatch', () => {
      const mwManager = new MiddlewareManager();
      const phases: string[] = [];

      mwManager.registerBefore('before_mw', () => {
        phases.push('before');
      });
      mwManager.registerAfter('after_mw', () => {
        phases.push('after');
      });

      const act = createAction({ type: 'TEST_MW', payload: {} });
      mwManager.executeBefore(act);
      mwManager.executeAfter(act);

      expect(phases).toEqual(['before', 'after']);
    });

    it('should trap errors in error middleware hooks', () => {
      const mwManager = new MiddlewareManager();
      let trappedErr: Error | null = null;

      mwManager.registerError('err_mw', (_act, err) => {
        trappedErr = err;
      });

      const act = createAction({ type: 'ERR_ACT', payload: {} });
      mwManager.executeError(act, new Error('Dispatch error'));

      expect(trappedErr).toBeDefined();
      expect((trappedErr as any).message).toBe('Dispatch error');
    });
  });

  describe('5. Provider & Runtime Dispatch Integration', () => {
    it('should dispatch actions, run reducers, mutate container state, and notify subscribers', () => {
      const provider = new StateProvider();
      provider.initialize();

      provider.createContainer('cart', { total: 0 });
      provider.registerReducer('cart_reducer', (state: any, action: any) => {
        if (action.type === 'ADD_TO_CART') {
          return { total: state.total + action.payload.price };
        }
        return state;
      });

      let notifiedState: any = null;
      provider.subscribe('cart', (st) => {
        notifiedState = st;
      });

      provider.dispatch('ADD_TO_CART', { price: 25 });

      expect(provider.getState('cart')).toEqual({ total: 25 });
      expect(notifiedState).toEqual({ total: 25 });
    });

    it('should execute actions through StateRuntime coordinator', () => {
      const runtime = new StateRuntime();
      runtime.initialize();

      runtime.createContainer('counter', { val: 10 });
      runtime.registerReducer('inc_reducer', (state: any, action: any) => {
        if (action.type === 'INC') return { val: state.val + 1 };
        return state;
      });

      runtime.dispatch('INC', {});
      expect(runtime.getState('counter')).toEqual({ val: 11 });
    });
  });
});
