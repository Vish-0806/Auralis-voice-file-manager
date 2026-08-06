import { beforeEach, describe, expect, it } from 'vitest';
import {
  createAcknowledgement,
  createEventRegistration,
  createFrontendEvent,
  createQueueConfiguration,
  createQueueHealth,
  createQueueStatistics,
  createQueuedEvent,
  createReliabilityHealth,
  createReliabilityStatistics,
  createReplayRecord,
  createReplayStatistics,
  createRetryPolicy,
  createRetryRecord,
  createRetryStatistics,
  DeliveryStatus,
  EventBus,
  EventPriority,
  EventProvider,
  EventProviderException,
  EventQueue,
  EventRegistry,
  EventRuntime,
  getEventProvider,
  getEventRuntime,
  ReplayManager,
  resetEventProvider,
  resetEventRuntime,
  RetryManager,
} from '../../src/runtime/events';

describe('Phase 16.4.5 — Frontend Asynchronous Event Queue, Retry & Reliability Engine', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable QueuedEvent model', () => {
      const evt = createFrontendEvent({ eventType: 'user.signup', payload: { id: 'u1' } });
      const queued = createQueuedEvent({ event: evt, priority: EventPriority.HIGH });

      expect(queued.event).toBe(evt);
      expect(queued.priority).toBe(EventPriority.HIGH);
      expect(queued.status).toBe(DeliveryStatus.PENDING);
      expect(queued.attemptCount).toBe(0);
      expect(Object.isFrozen(queued)).toBe(true);
    });

    it('should create immutable QueuedEvent model with custom parameters', () => {
      const evt = createFrontendEvent({ eventType: 'custom.q', payload: {} });
      const queued = createQueuedEvent({
        queueId: 'q_custom_1',
        event: evt,
        attemptCount: 2,
        status: DeliveryStatus.RETRIED,
      });

      expect(queued.queueId).toBe('q_custom_1');
      expect(queued.attemptCount).toBe(2);
      expect(queued.status).toBe(DeliveryStatus.RETRIED);
      expect(Object.isFrozen(queued)).toBe(true);
    });

    it('should create immutable QueueStatistics and QueueHealth models', () => {
      const stats = createQueueStatistics({ enqueuedCount: 10, dequeuedCount: 8, currentDepth: 2, maxCapacity: 100 });
      expect(stats.enqueuedCount).toBe(10);
      expect(stats.currentDepth).toBe(2);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createQueueHealth({ healthy: true, depth: 2, capacity: 100 });
      expect(health.healthy).toBe(true);
      expect(health.depth).toBe(2);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create default QueueStatistics and QueueHealth models', () => {
      const stats = createQueueStatistics();
      expect(stats.enqueuedCount).toBe(0);
      expect(stats.maxCapacity).toBe(1000);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createQueueHealth();
      expect(health.healthy).toBe(true);
      expect(health.capacity).toBe(1000);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable QueueConfiguration and RetryPolicy models', () => {
      const config = createQueueConfiguration({ maxCapacity: 500, dropStrategy: 'DROP_OLDEST' });
      expect(config.maxCapacity).toBe(500);
      expect(config.dropStrategy).toBe('DROP_OLDEST');
      expect(Object.isFrozen(config)).toBe(true);

      const policy = createRetryPolicy({ maxRetries: 5, initialDelayMs: 200, backoffMultiplier: 1.5 });
      expect(policy.maxRetries).toBe(5);
      expect(policy.initialDelayMs).toBe(200);
      expect(policy.backoffMultiplier).toBe(1.5);
      expect(Object.isFrozen(policy)).toBe(true);
    });

    it('should create default QueueConfiguration and RetryPolicy models', () => {
      const config = createQueueConfiguration();
      expect(config.maxCapacity).toBe(1000);
      expect(config.dropStrategy).toBe('DROP_OLDEST');
      expect(Object.isFrozen(config)).toBe(true);

      const policy = createRetryPolicy();
      expect(policy.maxRetries).toBe(3);
      expect(policy.initialDelayMs).toBe(100);
      expect(Object.isFrozen(policy)).toBe(true);
    });

    it('should create immutable RetryRecord and RetryStatistics models', () => {
      const rec = createRetryRecord({ queueId: 'q1', eventId: 'e1', attempt: 1, success: true });
      expect(rec.queueId).toBe('q1');
      expect(rec.success).toBe(true);
      expect(Object.isFrozen(rec)).toBe(true);

      const stats = createRetryStatistics({ totalRetries: 5, successfulRetries: 4, failedRetries: 1 });
      expect(stats.totalRetries).toBe(5);
      expect(stats.successfulRetries).toBe(4);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create default RetryStatistics model', () => {
      const stats = createRetryStatistics();
      expect(stats.totalRetries).toBe(0);
      expect(stats.exhaustedRetries).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable ReplayRecord and ReplayStatistics models', () => {
      const rpl = createReplayRecord({ eventId: 'e99', success: true });
      expect(rpl.eventId).toBe('e99');
      expect(rpl.success).toBe(true);
      expect(Object.isFrozen(rpl)).toBe(true);

      const stats = createReplayStatistics({ totalReplays: 3, successfulReplays: 3 });
      expect(stats.totalReplays).toBe(3);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create default ReplayStatistics model', () => {
      const stats = createReplayStatistics();
      expect(stats.totalReplays).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable Acknowledgement, ReliabilityStatistics, and ReliabilityHealth models', () => {
      const ack = createAcknowledgement({ queueId: 'q1', eventId: 'e1', status: DeliveryStatus.DELIVERED });
      expect(ack.queueId).toBe('q1');
      expect(ack.status).toBe(DeliveryStatus.DELIVERED);
      expect(Object.isFrozen(ack)).toBe(true);

      const relStats = createReliabilityStatistics({ acknowledgementCount: 15 });
      expect(relStats.acknowledgementCount).toBe(15);
      expect(Object.isFrozen(relStats)).toBe(true);

      const relHealth = createReliabilityHealth({ healthy: true, retryErrorRate: 0.02 });
      expect(relHealth.healthy).toBe(true);
      expect(relHealth.retryErrorRate).toBe(0.02);
      expect(Object.isFrozen(relHealth)).toBe(true);
    });

    it('should create default ReliabilityStatistics and ReliabilityHealth models', () => {
      const relStats = createReliabilityStatistics();
      expect(relStats.acknowledgementCount).toBe(0);
      expect(Object.isFrozen(relStats)).toBe(true);

      const relHealth = createReliabilityHealth();
      expect(relHealth.healthy).toBe(true);
      expect(relHealth.retryErrorRate).toBe(0);
      expect(Object.isFrozen(relHealth)).toBe(true);
    });
  });

  describe('2. EventQueue Engine & Priority Ordering', () => {
    it('should enqueue and dequeue events maintaining priority order (CRITICAL > HIGH > NORMAL > LOW)', () => {
      const queue = new EventQueue();

      queue.enqueue(createFrontendEvent({ eventType: 'normal.evt', payload: {}, priority: EventPriority.NORMAL }));
      queue.enqueue(createFrontendEvent({ eventType: 'critical.evt', payload: {}, priority: EventPriority.CRITICAL }));
      queue.enqueue(createFrontendEvent({ eventType: 'high.evt', payload: {}, priority: EventPriority.HIGH }));
      queue.enqueue(createFrontendEvent({ eventType: 'low.evt', payload: {}, priority: EventPriority.LOW }));

      expect(queue.size()).toBe(4);

      expect(queue.dequeue()?.event.eventType).toBe('critical.evt');
      expect(queue.dequeue()?.event.eventType).toBe('high.evt');
      expect(queue.dequeue()?.event.eventType).toBe('normal.evt');
      expect(queue.dequeue()?.event.eventType).toBe('low.evt');
      expect(queue.size()).toBe(0);
    });

    it('should maintain FIFO order within the same priority level', () => {
      const queue = new EventQueue();

      queue.enqueue(createFrontendEvent({ eventType: 'first.high', payload: {}, priority: EventPriority.HIGH }));
      queue.enqueue(createFrontendEvent({ eventType: 'second.high', payload: {}, priority: EventPriority.HIGH }));

      expect(queue.dequeue()?.event.eventType).toBe('first.high');
      expect(queue.dequeue()?.event.eventType).toBe('second.high');
    });

    it('should support peek() without removing highest priority item', () => {
      const queue = new EventQueue();
      queue.enqueue(createFrontendEvent({ eventType: 'peek.test', payload: {}, priority: EventPriority.HIGH }));

      expect(queue.peek()?.event.eventType).toBe('peek.test');
      expect(queue.size()).toBe(1); // Item remains in queue
    });

    it('should return undefined when dequeuing or peeking an empty queue', () => {
      const queue = new EventQueue();
      expect(queue.dequeue()).toBeUndefined();
      expect(queue.peek()).toBeUndefined();
    });

    it('should throw EventProviderException when enqueuing null or undefined event', () => {
      const queue = new EventQueue();
      expect(() => queue.enqueue(null as any)).toThrow(EventProviderException);
    });

    it('should handle capacity overflow with DROP_OLDEST strategy', () => {
      const config = createQueueConfiguration({ maxCapacity: 3, dropStrategy: 'DROP_OLDEST' });
      const queue = new EventQueue(config);

      queue.enqueue(createFrontendEvent({ eventType: 'e1', payload: {}, priority: EventPriority.LOW }));
      queue.enqueue(createFrontendEvent({ eventType: 'e2', payload: {}, priority: EventPriority.NORMAL }));
      queue.enqueue(createFrontendEvent({ eventType: 'e3', payload: {}, priority: EventPriority.HIGH }));

      // Queue is full (size 3). Enqueuing e4 drops lowest priority item e1
      queue.enqueue(createFrontendEvent({ eventType: 'e4', payload: {}, priority: EventPriority.CRITICAL }));

      expect(queue.size()).toBe(3);
      expect(queue.statistics().overflowCount).toBe(1);
      expect(queue.health().isOverflowed).toBe(true);
    });

    it('should throw EventProviderException when capacity is exceeded with REJECT_NEW strategy', () => {
      const config = createQueueConfiguration({ maxCapacity: 2, dropStrategy: 'REJECT_NEW' });
      const queue = new EventQueue(config);

      queue.enqueue(createFrontendEvent({ eventType: 'e1', payload: {} }));
      queue.enqueue(createFrontendEvent({ eventType: 'e2', payload: {} }));

      expect(() => queue.enqueue(createFrontendEvent({ eventType: 'e3', payload: {} }))).toThrow(
        EventProviderException,
      );
    });

    it('should clear queue items and reset size', () => {
      const queue = new EventQueue();
      queue.enqueue(createFrontendEvent({ eventType: 'e1', payload: {} }));
      queue.enqueue(createFrontendEvent({ eventType: 'e2', payload: {} }));

      queue.clear();
      expect(queue.size()).toBe(0);
    });
  });

  describe('3. RetryManager & ReplayManager Engines', () => {
    it('should evaluate shouldRetry() according to maximum retries policy', () => {
      const retryManager = new RetryManager(createRetryPolicy({ maxRetries: 3 }));

      expect(retryManager.shouldRetry(0)).toBe(true);
      expect(retryManager.shouldRetry(1)).toBe(true);
      expect(retryManager.shouldRetry(2)).toBe(true);
      expect(retryManager.shouldRetry(3)).toBe(false);
    });

    it('should record retries and aggregate statistics including exhausted retries', () => {
      const retryManager = new RetryManager(createRetryPolicy({ maxRetries: 2 }));

      retryManager.recordRetry('q1', 'e1', 1, true);
      retryManager.recordRetry('q2', 'e2', 1, false);
      retryManager.recordRetry('q2', 'e2', 2, false); // Exhausted

      const stats = retryManager.statistics();
      expect(stats.totalRetries).toBe(3);
      expect(stats.successfulRetries).toBe(1);
      expect(stats.failedRetries).toBe(2);
      expect(stats.exhaustedRetries).toBe(1);
    });

    it('should replay single event, all events, and filtered events via ReplayManager', () => {
      const replayManager = new ReplayManager();
      const pubEvt1 = { event: { eventId: 'e1', eventType: 'type1', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      const pubEvt2 = { event: { eventId: 'e2', eventType: 'type2', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 2 };

      const r1 = replayManager.replayEvent(pubEvt1 as any);
      expect(r1.eventId).toBe('e1');

      const allRecords = replayManager.replayAll([pubEvt1 as any, pubEvt2 as any]);
      expect(allRecords.length).toBe(2);

      const filteredRecords = replayManager.replayFiltered(
        [pubEvt1 as any, pubEvt2 as any],
        (evt) => evt.event.eventType === 'type2',
      );
      expect(filteredRecords.length).toBe(1);
      expect(filteredRecords[0].eventId).toBe('e2');

      const stats = replayManager.statistics();
      expect(stats.totalReplays).toBe(4);
      expect(stats.successfulReplays).toBe(4);
    });

    it('should return empty replay records array when replayFiltered finds no matches', () => {
      const replayManager = new ReplayManager();
      const pubEvt1 = { event: { eventId: 'e1', eventType: 'type1', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };

      const filtered = replayManager.replayFiltered([pubEvt1 as any], (e) => e.event.eventType === 'non_existent');
      expect(filtered.length).toBe(0);
    });
  });

  describe('4. EventBus Reliability Pipeline Integration', () => {
    it('should run publish through queue, dequeue, route, and acknowledge delivery', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'reliable.order' }));

      const bus = new EventBus(eventRegistry);
      let payloadReceived: any = null;

      bus.subscribe('reliable.order', (evt) => {
        payloadReceived = evt.payload;
      });

      const published = bus.publish('reliable.order', { id: 'r100' });
      expect(published.event.eventType).toBe('reliable.order');
      expect(payloadReceived).toEqual({ id: 'r100' });
    });

    it('should support manual enqueue, dequeue, peek, and queueSize on EventBus', () => {
      const eventRegistry = new EventRegistry();
      const bus = new EventBus(eventRegistry);

      const evt = createFrontendEvent({ eventType: 'manual.q', payload: {} });
      bus.enqueue(evt);

      expect(bus.queueSize()).toBe(1);
      expect(bus.peek()?.event.eventType).toBe('manual.q');
      expect(bus.dequeue()?.event.eventType).toBe('manual.q');
      expect(bus.queueSize()).toBe(0);
    });

    it('should support replay of history on EventBus', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'historical.evt' }));

      const bus = new EventBus(eventRegistry);
      bus.publish('historical.evt', { a: 1 });
      bus.publish('historical.evt', { a: 2 });

      const replayRecords = bus.replay();
      expect(replayRecords.length).toBe(2);
    });

    it('should support manual retry and delivery acknowledgement on EventBus', () => {
      const eventRegistry = new EventRegistry();
      const bus = new EventBus(eventRegistry);

      expect(bus.retry('q_manual')).toBe(true);

      const ack = bus.acknowledge('q_ack', DeliveryStatus.DELIVERED);
      expect(ack.queueId).toBe('q_ack');
      expect(ack.status).toBe(DeliveryStatus.DELIVERED);
    });
  });

  describe('5. Provider Integration & Runtime Delegation', () => {
    it('should delegate enqueue, dequeue, peek, queueSize, retry, replay, acknowledge, deadLetters through EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'prov.queue' }));

      const evt = createFrontendEvent({ eventType: 'prov.queue', payload: {} });
      provider.enqueue(evt);

      expect(provider.queueSize()).toBe(1);
      expect(provider.peek()?.event.eventType).toBe('prov.queue');
      expect(provider.dequeue()?.event.eventType).toBe('prov.queue');

      const ack = provider.acknowledge('q100', DeliveryStatus.DELIVERED);
      expect(ack.queueId).toBe('q100');

      expect(provider.retry('q100')).toBe(true);
      expect(provider.deadLetters()).toBeDefined();

      provider.clearDeadLetters();
      expect(provider.deadLetters().length).toBe(0);
    });

    it('should accept custom EventQueue, RetryManager, ReplayManager in EventProvider constructor', () => {
      const queue = new EventQueue();
      const retryManager = new RetryManager();
      const replayManager = new ReplayManager();

      const provider = new EventProvider(
        undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined,
        queue, retryManager, replayManager,
      );
      provider.initialize();

      const evt = createFrontendEvent({ eventType: 'custom.provider.queue', payload: {} });
      provider.enqueue(evt);
      expect(provider.queueSize()).toBe(1);
    });

    it('should delegate queue and reliability APIs through EventRuntime coordinator', () => {
      const runtime = new EventRuntime();
      runtime.initialize();

      const evt = createFrontendEvent({ eventType: 'rt.queue', payload: {} });
      runtime.enqueue(evt);

      expect(runtime.queueSize()).toBe(1);
      expect(runtime.peek()?.event.eventType).toBe('rt.queue');
      expect(runtime.dequeue()?.event.eventType).toBe('rt.queue');

      expect(runtime.retry('q_rt')).toBe(true);
      expect(runtime.replay()).toBeDefined();
    });

    it('should include reliability statistics and health in provider diagnostics()', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'diag.rel' }));

      provider.publish('diag.rel', { x: 1 });

      const diag = provider.diagnostics();
      expect(diag.queueDepth).toBeDefined();
      expect(diag.retryStatistics).toBeDefined();
      expect(diag.replayStatistics).toBeDefined();
      expect(diag.reliabilityStatistics).toBeDefined();
      expect(diag.deadLetterQueueSize).toBeDefined();
    });

    it('should support reliability operations via global singleton runtime helpers', () => {
      const runtime = getEventRuntime();
      const provider = getEventProvider();

      provider.initialize();
      const evt = createFrontendEvent({ eventType: 'global.q', payload: {} });
      runtime.enqueue(evt);

      expect(runtime.queueSize()).toBe(1);
      expect(runtime.dequeue()?.event.eventType).toBe('global.q');
    });
  });
});
