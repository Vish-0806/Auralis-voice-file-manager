import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  InMemoryNotificationChannel,
  AlertingProvider,
  AlertingRuntime,
  AlertNotificationError,
  NotificationChannelNotFoundError,
  NotificationDispatchError,
  createNotificationRequest,
  createAlertRecord
} from '../../../src/observability';

describe('Notification Channel Runtime Tests', () => {
  let provider: AlertingProvider;
  let runtime: AlertingRuntime;
  let mockRequest: any;

  beforeEach(async () => {
    provider = new AlertingProvider();
    runtime = new AlertingRuntime(provider);
    await runtime.initialize();

    mockRequest = createNotificationRequest({
      id: 'notif-1',
      alertId: 'alert-1',
      channelId: 'ch-test-1',
      payload: {
        title: 'Database CPU Spike',
        message: 'CPU usage is at 98%',
        severity: 'CRITICAL',
        metadata: { server: 'prod-db-1' }
      },
      priority: 'HIGH',
      channelType: 'CUSTOM',
      recipient: {
        id: 'recip-1',
        name: 'System Admin',
        address: 'admin@auralis.io'
      },
      createdAt: Date.now()
    });
  });

  afterEach(async () => {
    await runtime.shutdown();
  });

  it('1. Channel registration, unique ID, lookup, and removal', () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');

    runtime.registerNotificationChannel(channel);
    expect(runtime.listNotificationChannels()).toHaveLength(1);
    expect(runtime.getNotificationChannel('ch-test-1')).toBeDefined();

    expect(() => runtime.registerNotificationChannel(channel)).toThrow(AlertNotificationError);

    runtime.unregisterNotificationChannel('ch-test-1');
    expect(runtime.listNotificationChannels()).toHaveLength(0);
  });

  it('2. Channel enable/disable toggling', () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    runtime.registerNotificationChannel(channel);

    expect(runtime.getNotificationChannel('ch-test-1')?.enabled).toBe(true);

    runtime.disableNotificationChannel('ch-test-1');
    expect(runtime.getNotificationChannel('ch-test-1')?.enabled).toBe(false);

    runtime.enableNotificationChannel('ch-test-1');
    expect(runtime.getNotificationChannel('ch-test-1')?.enabled).toBe(true);

    runtime.unregisterNotificationChannel('ch-test-1');
  });

  it('3. Successful dispatch, statistics, and bounded delivery history', async () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    runtime.registerNotificationChannel(channel);

    const result = await runtime.dispatchNotification(mockRequest);
    expect(result.status).toBe('DELIVERED');
    expect(result.attempts).toBe(1);
    expect(result.history).toHaveLength(1);

    const stats = runtime.getStatistics();
    expect(stats.notificationRequests).toBe(1);
    expect(stats.deliveredNotifications).toBe(1);

    const history = runtime.getNotificationDeliveryHistory();
    expect(history).toHaveLength(1);
    expect(history[0].status).toBe('DELIVERED');

    runtime.unregisterNotificationChannel('ch-test-1');
  });

  it('4. Missing channel handling throws NotificationChannelNotFoundError', async () => {
    await expect(runtime.dispatchNotification(mockRequest)).rejects.toThrow(
      NotificationChannelNotFoundError
    );
  });

  it('5. Disabled channel returns SKIPPED status without calling send()', async () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    channel.enabled = false;
    runtime.registerNotificationChannel(channel);

    const result = await runtime.dispatchNotification(mockRequest);
    expect(result.status).toBe('SKIPPED');
    expect(result.attempts).toBe(0);

    const stats = runtime.getStatistics();
    expect(stats.skippedNotifications).toBe(1);

    runtime.unregisterNotificationChannel('ch-test-1');
  });

  it('6. Failed channel behavior, retry limits, and error normalization', async () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    channel.simulateFailures(3);
    runtime.registerNotificationChannel(channel);

    const result = await runtime.dispatchNotification(mockRequest, 2);
    expect(result.status).toBe('FAILED');
    expect(result.attempts).toBe(2);
    expect(result.error?.name).toBe('SimulatedFailure');

    const stats = runtime.getStatistics();
    expect(stats.failedNotifications).toBe(1);
    expect(stats.retryAttempts).toBe(1);

    runtime.unregisterNotificationChannel('ch-test-1');
  });

  it('7. Duplicate dispatch protection throws error', async () => {
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    runtime.registerNotificationChannel(channel);

    await runtime.dispatchNotification(mockRequest);

    await expect(runtime.dispatchNotification(mockRequest)).rejects.toThrow(
      NotificationDispatchError
    );

    runtime.unregisterNotificationChannel('ch-test-1');
  });

  it('8. Lifecycle and Suppression Independence', async () => {
    const alert = createAlertRecord({
      id: 'alert-1',
      sourceId: 'src-1',
      severity: 'ERROR',
      state: 'ACTIVE',
      title: 'Alert 1',
      message: 'Message 1',
      createdAt: 1000,
      updatedAt: 1000,
      metadata: {}
    });

    runtime.registerAlert(alert);
    const channel = new InMemoryNotificationChannel('ch-test-1', 'Test Channel');
    runtime.registerNotificationChannel(channel);

    const result = await runtime.dispatchNotification(mockRequest);
    expect(result.status).toBe('DELIVERED');

    expect(runtime.getAlertLifecycle('alert-1')?.state).toBe('ACTIVE');

    runtime.unregisterNotificationChannel('ch-test-1');
  });
});
