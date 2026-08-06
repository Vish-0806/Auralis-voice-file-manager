/**
 * State History Engine (Phase 16.5).
 *
 * Implements IHistoryManager managing snapshot timeline logging, history stack capacity limits,
 * undo/redo operations, and time travel state restoration.
 */

import {
  createRedoRecord,
  createStateHistory,
  createStateSnapshot,
  createUndoRecord,
  RedoRecord,
  StateHistory,
  StateSnapshot,
  UndoRecord,
} from './models';
import { IHistoryManager } from './interfaces';

export class HistoryManager<T = unknown> implements IHistoryManager<T> {
  private readonly _snapshots: StateSnapshot<T>[] = [];
  private _currentIndex = -1;
  private readonly _maxSize: number;

  constructor(maxSize = 50) {
    this._maxSize = maxSize;
  }

  public pushSnapshot(containerId: string, state: T): StateSnapshot<T> {
    // If pushing after undo operations, truncate redone timeline
    if (this._currentIndex < this._snapshots.length - 1) {
      this._snapshots.splice(this._currentIndex + 1);
    }

    const version = this._snapshots.length + 1;
    const snap = createStateSnapshot<T>({
      containerId,
      state: this.deepClone(state),
      version,
    });

    this._snapshots.push(snap);
    if (this._snapshots.length > this._maxSize) {
      this._snapshots.shift();
    }

    this._currentIndex = this._snapshots.length - 1;
    return snap;
  }

  public undo(): UndoRecord<T> | undefined {
    if (!this.canUndo()) return undefined;
    this._currentIndex--;
    const prevSnap = this._snapshots[this._currentIndex];

    return createUndoRecord<T>({
      previousState: this.deepClone(prevSnap.state),
    });
  }

  public redo(): RedoRecord<T> | undefined {
    if (!this.canRedo()) return undefined;
    this._currentIndex++;
    const nextSnap = this._snapshots[this._currentIndex];

    return createRedoRecord<T>({
      nextState: this.deepClone(nextSnap.state),
    });
  }

  public canUndo(): boolean {
    return this._currentIndex > 0;
  }

  public canRedo(): boolean {
    return this._currentIndex >= 0 && this._currentIndex < this._snapshots.length - 1;
  }

  public history(): StateHistory<T> {
    return createStateHistory<T>({
      snapshots: [...this._snapshots],
      currentIndex: this._currentIndex,
      maxSize: this._maxSize,
    });
  }

  public clearHistory(): void {
    this._snapshots.length = 0;
    this._currentIndex = -1;
  }

  private deepClone<V>(val: V): V {
    if (val === null || typeof val !== 'object') return val;
    try {
      return JSON.parse(JSON.stringify(val));
    } catch {
      return val;
    }
  }
}
