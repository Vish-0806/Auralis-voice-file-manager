/**
 * Retry Manager Engine (Phase 16.4.5).
 *
 * Implements IRetryManager managing retry policy evaluations, retry attempt tracking,
 * retry failure counters, and retry statistics reporting.
 */

import {
  createRetryPolicy,
  createRetryRecord,
  createRetryStatistics,
  RetryPolicy,
  RetryRecord,
  RetryStatistics,
} from './models';
import { IRetryManager } from './interfaces';

export class RetryManager implements IRetryManager {
  private readonly _policy: RetryPolicy;
  private readonly _records: RetryRecord[] = [];

  private _totalRetries = 0;
  private _successfulRetries = 0;
  private _failedRetries = 0;
  private _exhaustedRetries = 0;

  constructor(policy?: RetryPolicy) {
    this._policy = policy ?? createRetryPolicy();
  }

  public shouldRetry(attemptCount: number): boolean {
    return attemptCount < this._policy.maxRetries;
  }

  public recordRetry(
    queueId: string,
    eventId: string,
    attempt: number,
    success: boolean,
    error?: string,
  ): RetryRecord {
    this._totalRetries++;

    if (success) {
      this._successfulRetries++;
    } else {
      this._failedRetries++;
      if (attempt >= this._policy.maxRetries) {
        this._exhaustedRetries++;
      }
    }

    const rec = createRetryRecord({
      queueId,
      eventId,
      attempt,
      success,
      error,
    });

    this._records.push(rec);
    return rec;
  }

  public statistics(): RetryStatistics {
    return createRetryStatistics({
      totalRetries: this._totalRetries,
      successfulRetries: this._successfulRetries,
      failedRetries: this._failedRetries,
      exhaustedRetries: this._exhaustedRetries,
    });
  }
}
