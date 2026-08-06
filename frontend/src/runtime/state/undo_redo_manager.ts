/**
 * Undo Redo Manager Engine (Phase 16.5).
 *
 * Provides specialized undo and redo management delegation for state container changes.
 */

import { RedoRecord, StateHistory, StateSnapshot, UndoRecord } from './models';
import { HistoryManager } from './state_history';

export class UndoRedoManager<T = unknown> {
  private readonly _historyManager: HistoryManager<T>;

  constructor(maxSize = 50) {
    this._historyManager = new HistoryManager<T>(maxSize);
  }

  public pushSnapshot(containerId: string, state: T): StateSnapshot<T> {
    return this._historyManager.pushSnapshot(containerId, state);
  }

  public undo(): UndoRecord<T> | undefined {
    return this._historyManager.undo();
  }

  public redo(): RedoRecord<T> | undefined {
    return this._historyManager.redo();
  }

  public canUndo(): boolean {
    return this._historyManager.canUndo();
  }

  public canRedo(): boolean {
    return this._historyManager.canRedo();
  }

  public history(): StateHistory<T> {
    return this._historyManager.history();
  }

  public clear(): void {
    this._historyManager.clearHistory();
  }
}
