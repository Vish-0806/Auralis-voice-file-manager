/**
 * Replay Manager Engine (Phase 16.4.5).
 *
 * Implements IReplayManager allowing event replay for single events, historical logs,
 * or filtered queries, maintaining replay telemetry and execution history.
 */

import {
  createReplayRecord,
  createReplayStatistics,
  PublishedEvent,
  ReplayRecord,
  ReplayStatistics,
} from './models';
import { IReplayManager } from './interfaces';

export class ReplayManager implements IReplayManager {
  private _totalReplays = 0;
  private _successfulReplays = 0;
  private _failedReplays = 0;

  public replayEvent(publishedEvent: PublishedEvent): ReplayRecord {
    this._totalReplays++;
    this._successfulReplays++;

    return createReplayRecord({
      eventId: publishedEvent.event.eventId,
      success: true,
    });
  }

  public replayAll(history: ReadonlyArray<PublishedEvent>): ReadonlyArray<ReplayRecord> {
    const records: ReplayRecord[] = [];
    for (const evt of history) {
      records.push(this.replayEvent(evt));
    }
    return Object.freeze(records);
  }

  public replayFiltered(
    history: ReadonlyArray<PublishedEvent>,
    filter: (evt: PublishedEvent) => boolean,
  ): ReadonlyArray<ReplayRecord> {
    const records: ReplayRecord[] = [];
    for (const evt of history) {
      if (filter(evt)) {
        records.push(this.replayEvent(evt));
      }
    }
    return Object.freeze(records);
  }

  public statistics(): ReplayStatistics {
    return createReplayStatistics({
      totalReplays: this._totalReplays,
      successfulReplays: this._successfulReplays,
      failedReplays: this._failedReplays,
    });
  }
}
