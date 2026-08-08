// Core State Management Boundary Types for Future Phase 16.5 Integration

export interface Action<P = unknown> {
  readonly type: string;
  readonly payload?: P;
}

export type Reducer<S, A extends Action = Action> = (state: S | undefined, action: A) => S;

export type Listener = () => void;

export interface Store<S, A extends Action = Action> {
  getState(): S;
  dispatch(action: A): void;
  subscribe(listener: Listener): () => void;
}

export type Selector<S, T> = (state: S) => T;
export type DerivedSelector<S, T, Args extends unknown[]> = (state: S, ...args: Args) => T;
export type MemoizedSelector<S, T> = Selector<S, T> & {
  clearCache(): void;
};
