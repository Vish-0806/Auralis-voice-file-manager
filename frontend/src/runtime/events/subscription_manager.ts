/**
 * Subscription Manager Engine (Phase 16.4.3).
 *
 * Implements ISubscriptionManager executing priority-ordered subscriber callbacks upon event publication.
 * Ensures strict exception isolation so throwing subscribers never interrupt remaining subscribers,
 * measures execution duration, and tracks telemetry statistics and subscriber health.
 */

import {
  createSubscriberHealth,
  createSubscriberStatistics,
  createSubscriptionExecution,
  createSubscriptionResult,
  PublishedEvent,
  SubscriberHealth,
  SubscriberRegistration,
  SubscriberStatistics,
  SubscriptionExecution,
  SubscriptionResult,
} from './models';
import { ISubscriptionManager } from './interfaces';

export class SubscriptionManager implements ISubscriptionManager {
  private _totalExecutions = 0;
  private _successfulExecutions = 0;
  private _failedExecutions = 0;
  private _totalDurationMs = 0;

  public executeSubscribers<T = unknown>(
    publishedEvent: PublishedEvent<T>,
    subscribers: ReadonlyArray<SubscriberRegistration<T>>,
  ): SubscriptionResult {
    const executions: SubscriptionExecution[] = [];

    for (const sub of subscribers) {
      const start = performance ? performance.now() : Date.now();
      let success = true;
      let errorMsg: string | undefined;

      try {
        sub.handler(publishedEvent.event);
      } catch (err: any) {
        success = false;
        errorMsg = err?.message ?? String(err);
      }

      const end = performance ? performance.now() : Date.now();
      const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);

      this._totalExecutions++;
      this._totalDurationMs += durationMs;

      if (success) {
        this._successfulExecutions++;
      } else {
        this._failedExecutions++;
      }

      executions.push(
        createSubscriptionExecution({
          subscriptionId: sub.subscriptionId,
          eventId: publishedEvent.event.eventId,
          eventType: publishedEvent.event.eventType,
          success,
          durationMs,
          error: errorMsg,
        }),
      );
    }

    return createSubscriptionResult({
      publishedEvent,
      executions,
      totalExecutions: executions.length,
      successfulExecutions: executions.filter((e) => e.success).length,
      failedExecutions: executions.filter((e) => !e.success).length,
    });
  }

  public statistics(): SubscriberStatistics {
    const avgMs =
      this._totalExecutions > 0 ? Math.round((this._totalDurationMs / this._totalExecutions) * 100) / 100 : 0;

    return createSubscriberStatistics({
      totalSubscriptions: 0,
      activeSubscriptions: 0,
      totalExecutions: this._totalExecutions,
      successfulExecutions: this._successfulExecutions,
      failedExecutions: this._failedExecutions,
      averageExecutionMs: avgMs,
    });
  }

  public health(): SubscriberHealth {
    const errorRate =
      this._totalExecutions > 0 ? Math.round((this._failedExecutions / this._totalExecutions) * 100) / 100 : 0;
    const healthy = errorRate <= 0.1; // Healthy if error rate <= 10%

    return createSubscriberHealth({
      healthy,
      activeSubscriptionsCount: 0,
      totalExecutionsCount: this._totalExecutions,
      errorRate,
    });
  }
}
