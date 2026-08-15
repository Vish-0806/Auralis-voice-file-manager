import { NotificationChannelRegistry } from './NotificationChannelRegistry';
import {
  NotificationRequest,
  NotificationDeliveryResult,
  NotificationDeliveryAttempt,
  NotificationDeliveryStatusValue,
  NotificationPriority,
  NotificationChannelType
} from '../models/notification';
import {
  NotificationValidationError,
  NotificationChannelNotFoundError,
  NotificationDispatchError
} from '../errors/AlertingErrors';
import {
  createNotificationDeliveryResult,
  createNotificationDeliveryAttempt
} from '../factories/alertingFactories';

export class NotificationDispatcher {
  private readonly _registry: NotificationChannelRegistry;
  private readonly _history: NotificationDeliveryResult[] = [];
  private readonly _maxHistorySize: number;
  private readonly _deliveredNotificationIds = new Set<string>();

  private _notificationRequests = 0;
  private _validationFailures = 0;
  private _dispatchedNotifications = 0;
  private _deliveredNotifications = 0;
  private _failedNotifications = 0;
  private _skippedNotifications = 0;
  private _cancelledNotifications = 0;
  private _retryAttempts = 0;
  private _totalDeliveryDuration = 0;

  constructor(registry: NotificationChannelRegistry, maxHistorySize = 1000) {
    this._registry = registry;
    this._maxHistorySize = maxHistorySize;
  }

  public async dispatch(
    request: NotificationRequest,
    maxAttempts = 3
  ): Promise<NotificationDeliveryResult> {
    this._notificationRequests++;

    try {
      this.validateRequest(request);
    } catch (err: any) {
      this._validationFailures++;
      throw err;
    }

    if (this._deliveredNotificationIds.has(request.id)) {
      throw new NotificationDispatchError(`Notification with ID ${request.id} was already successfully delivered.`);
    }

    const channel = this._registry.get(request.channelId);
    if (!channel) {
      this._failedNotifications++;
      const start = Date.now();
      const result = createNotificationDeliveryResult({
        notificationId: request.id,
        channelId: request.channelId,
        status: 'FAILED',
        error: { name: 'ChannelNotFoundError', message: `Channel with ID ${request.channelId} not found` },
        attemptedAt: start,
        completedAt: start,
        duration: 0,
        attempts: 0,
        history: []
      });
      this.logResult(result);
      throw new NotificationChannelNotFoundError(`Channel with ID ${request.channelId} not found`);
    }

    if (!channel.enabled) {
      this._skippedNotifications++;
      const start = Date.now();
      const result = createNotificationDeliveryResult({
        notificationId: request.id,
        channelId: channel.id,
        status: 'SKIPPED',
        attemptedAt: start,
        completedAt: start,
        duration: 0,
        attempts: 0,
        history: []
      });
      this.logResult(result);
      return result;
    }

    this._dispatchedNotifications++;
    const attemptsHistory: NotificationDeliveryAttempt[] = [];
    const startTime = Date.now();
    let currentAttempt = 0;
    let finalStatus: NotificationDeliveryStatusValue = 'FAILED';
    let lastError: { name: string; message: string; stack?: string } | undefined;

    while (currentAttempt < maxAttempts) {
      currentAttempt++;
      const attemptStart = Date.now();

      try {
        const attemptResult = await channel.send(request);
        const attemptDuration = Date.now() - attemptStart;

        if (attemptResult.status === 'DELIVERED') {
          const attemptRecord = createNotificationDeliveryAttempt({
            notificationId: request.id,
            attempt: currentAttempt,
            status: 'DELIVERED',
            timestamp: attemptStart,
            duration: attemptDuration
          });
          attemptsHistory.push(attemptRecord);
          finalStatus = 'DELIVERED';
          lastError = undefined;
          this._deliveredNotificationIds.add(request.id);
          break;
        } else {
          lastError = attemptResult.error || { name: 'DeliveryError', message: 'Delivery failed' };
          const attemptRecord = createNotificationDeliveryAttempt({
            notificationId: request.id,
            attempt: currentAttempt,
            status: 'FAILED',
            timestamp: attemptStart,
            duration: attemptDuration,
            error: lastError
          });
          attemptsHistory.push(attemptRecord);
          if (currentAttempt < maxAttempts) {
            this._retryAttempts++;
          }
        }
      } catch (err: any) {
        const attemptDuration = Date.now() - attemptStart;
        lastError = {
          name: err.name || 'DispatchError',
          message: err.message || 'Exception caught during channel dispatch',
          stack: err.stack
        };
        const attemptRecord = createNotificationDeliveryAttempt({
          notificationId: request.id,
          attempt: currentAttempt,
          status: 'FAILED',
          timestamp: attemptStart,
          duration: attemptDuration,
          error: lastError
        });
        attemptsHistory.push(attemptRecord);
        if (currentAttempt < maxAttempts) {
          this._retryAttempts++;
        }
      }
    }

    const totalDuration = Date.now() - startTime;
    this._totalDeliveryDuration += totalDuration;

    if (finalStatus === 'DELIVERED') {
      this._deliveredNotifications++;
    } else {
      this._failedNotifications++;
    }

    const finalResult = createNotificationDeliveryResult({
      notificationId: request.id,
      channelId: channel.id,
      status: finalStatus,
      error: lastError,
      attemptedAt: startTime,
      completedAt: Date.now(),
      duration: totalDuration,
      attempts: currentAttempt,
      history: attemptsHistory
    });

    this.logResult(finalResult);
    return finalResult;
  }

  private validateRequest(request: NotificationRequest): void {
    if (!request) {
      throw new NotificationValidationError('Notification request is required');
    }
    if (!request.id) {
      throw new NotificationValidationError('Notification ID is required');
    }
    if (!request.alertId) {
      throw new NotificationValidationError('Alert ID is required');
    }
    if (!request.channelId) {
      throw new NotificationValidationError('Channel ID is required');
    }
    if (!request.payload) {
      throw new NotificationValidationError('Payload is required');
    }
    if (!request.payload.title) {
      throw new NotificationValidationError('Payload title is required');
    }
    if (!request.payload.message) {
      throw new NotificationValidationError('Payload message is required');
    }
    if (!request.payload.severity) {
      throw new NotificationValidationError('Payload severity is required');
    }
    if (!request.recipient) {
      throw new NotificationValidationError('Recipient is required');
    }
    if (!request.recipient.id) {
      throw new NotificationValidationError('Recipient ID is required');
    }
    if (!request.recipient.name) {
      throw new NotificationValidationError('Recipient name is required');
    }
    if (typeof request.createdAt !== 'number' || isNaN(request.createdAt) || request.createdAt < 0) {
      throw new NotificationValidationError('Invalid createdAt timestamp');
    }
    if (!Object.values(NotificationPriority).includes(request.priority)) {
      throw new NotificationValidationError(`Invalid notification priority: ${request.priority}`);
    }
    if (!Object.values(NotificationChannelType).includes(request.channelType)) {
      throw new NotificationValidationError(`Invalid notification channelType: ${request.channelType}`);
    }
  }

  public getHistory(): ReadonlyArray<NotificationDeliveryResult> {
    return this._history;
  }

  public getStats() {
    const averageDeliveryDuration = this._dispatchedNotifications > 0 ? this._totalDeliveryDuration / this._dispatchedNotifications : 0;
    return {
      notificationRequests: this._notificationRequests,
      validationFailures: this._validationFailures,
      dispatchedNotifications: this._dispatchedNotifications,
      deliveredNotifications: this._deliveredNotifications,
      failedNotifications: this._failedNotifications,
      skippedNotifications: this._skippedNotifications,
      cancelledNotifications: this._cancelledNotifications,
      retryAttempts: this._retryAttempts,
      averageDeliveryDuration
    };
  }

  public clear(): void {
    this._history.length = 0;
    this._deliveredNotificationIds.clear();
    this._notificationRequests = 0;
    this._validationFailures = 0;
    this._dispatchedNotifications = 0;
    this._deliveredNotifications = 0;
    this._failedNotifications = 0;
    this._skippedNotifications = 0;
    this._cancelledNotifications = 0;
    this._retryAttempts = 0;
    this._totalDeliveryDuration = 0;
  }

  private logResult(result: NotificationDeliveryResult): void {
    this._history.push(result);
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }
  }
}
