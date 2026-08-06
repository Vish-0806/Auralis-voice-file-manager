/**
 * Dispatch Manager Engine (Phase 16.4.4).
 *
 * Implements IDispatchManager coordinating event dispatch execution, subscriber ordering,
 * dead-letter record generation for failed deliveries, and telemetry reporting.
 */

import {
  createDeadLetterRecord,
  createDispatchHealth,
  createDispatchPolicy,
  createDispatchRecord,
  createDispatchStatistics,
  createPublishedEvent,
  DeadLetterRecord,
  DispatchHealth,
  DispatchPolicy,
  DispatchRecord,
  DispatchStatistics,
  RoutingDecision,
  SubscriberRegistration,
  SubscriptionExecution,
} from './models';
import { IDispatchManager, ISubscriptionManager } from './interfaces';
import { SubscriptionManager } from './subscription_manager';

export class DispatchManager implements IDispatchManager {
  private readonly _subscriptionManager: ISubscriptionManager;
  private readonly _policy: DispatchPolicy;

  private readonly _deadLetters: DeadLetterRecord[] = [];

  private _totalDispatches = 0;
  private _successfulDispatches = 0;
  private _failedDispatches = 0;
  private _totalDurationMs = 0;

  constructor(subscriptionManager?: ISubscriptionManager, policy?: DispatchPolicy) {
    this._subscriptionManager = subscriptionManager ?? new SubscriptionManager();
    this._policy = policy ?? createDispatchPolicy();
  }

  public dispatch<T = unknown>(
    decision: RoutingDecision,
    subscribers: ReadonlyArray<SubscriberRegistration<T>>,
  ): DispatchRecord {
    const start = performance ? performance.now() : Date.now();
    this._totalDispatches++;

    const executions: SubscriptionExecution[] = [];
    const publishedEvt = createPublishedEvent<T>({
      event: decision.event as any,
      sequenceNumber: 0,
    });

    if (subscribers.length > 0) {
      const res = this._subscriptionManager.executeSubscribers(publishedEvt, subscribers);
      executions.push(...res.executions);

      // Dead Letter processing if any subscriber failed
      if (res.failedExecutions > 0 && this._policy.deadLetterEnabled) {
        for (const exec of res.executions) {
          if (!exec.success) {
            this._deadLetters.push(
              createDeadLetterRecord({
                event: decision.event,
                reason: `Subscriber execution failed on subscription '${exec.subscriptionId}'`,
                error: exec.error,
              }),
            );
          }
        }
      }
    }

    const end = performance ? performance.now() : Date.now();
    const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);
    this._totalDurationMs += durationMs;

    const overallSuccess = executions.length === 0 || executions.every((e) => e.success);
    if (overallSuccess) {
      this._successfulDispatches++;
    } else {
      this._failedDispatches++;
    }

    return createDispatchRecord({
      decision,
      executions: Object.freeze(executions),
      success: overallSuccess,
      totalDurationMs: durationMs,
    });
  }

  public listDeadLetters(): ReadonlyArray<DeadLetterRecord> {
    return Object.freeze([...this._deadLetters]);
  }

  public clearDeadLetters(): void {
    this._deadLetters.length = 0;
  }

  public statistics(): DispatchStatistics {
    const avgMs =
      this._totalDispatches > 0 ? Math.round((this._totalDurationMs / this._totalDispatches) * 100) / 100 : 0;

    return createDispatchStatistics({
      totalDispatches: this._totalDispatches,
      successfulDispatches: this._successfulDispatches,
      failedDispatches: this._failedDispatches,
      averageDispatchMs: avgMs,
      deadLetterCount: this._deadLetters.length,
    });
  }

  public health(): DispatchHealth {
    const errorRate =
      this._totalDispatches > 0 ? Math.round((this._failedDispatches / this._totalDispatches) * 100) / 100 : 0;
    const healthy = errorRate <= 0.1;

    return createDispatchHealth({
      healthy,
      activeRulesCount: 0,
      dispatchErrorRate: errorRate,
    });
  }
}
