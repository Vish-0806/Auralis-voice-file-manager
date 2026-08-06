import { beforeEach, describe, expect, it } from 'vitest';
import {
  createEventRegistration,
  createEventSubscription,
  createSubscriberHealth,
  createSubscriberRegistration,
  createSubscriberStatistics,
  createSubscriptionExecution,
  createSubscriptionResult,
  EventBus,
  EventPriority,
  EventProvider,
  EventRegistry,
  EventRuntime,
  EventValidationException,
  getEventProvider,
  getEventRuntime,
  resetEventProvider,
  resetEventRuntime,
  SubscriberRegistry,
  SubscriptionManager,
} from '../../src/runtime/events';

describe('Phase 16.4.3 — Frontend Publish / Subscribe Engine', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable EventSubscription model', () => {
      const sub = createEventSubscription({
        eventType: 'user.created',
        priority: EventPriority.HIGH,
      });

      expect(sub.eventType).toBe('user.created');
      expect(sub.priority).toBe(EventPriority.HIGH);
      expect(sub.active).toBe(true);
      expect(sub.subscriptionId).toBeDefined();
      expect(Object.isFrozen(sub)).toBe(true);
    });

    it('should create immutable EventSubscription model with custom parameters', () => {
      const ts = new Date().toISOString();
      const sub = createEventSubscription({
        subscriptionId: 'sub_custom_100',
        eventType: 'order.shipped',
        priority: EventPriority.CRITICAL,
        subscribedAt: ts,
        active: false,
      });

      expect(sub.subscriptionId).toBe('sub_custom_100');
      expect(sub.eventType).toBe('order.shipped');
      expect(sub.priority).toBe(EventPriority.CRITICAL);
      expect(sub.subscribedAt).toBe(ts);
      expect(sub.active).toBe(false);
      expect(Object.isFrozen(sub)).toBe(true);
    });

    it('should create immutable SubscriberRegistration model', () => {
      const handler = () => {};
      const reg = createSubscriberRegistration({
        eventType: 'user.created',
        handler,
        priority: EventPriority.CRITICAL,
      });

      expect(reg.eventType).toBe('user.created');
      expect(reg.handler).toBe(handler);
      expect(reg.priority).toBe(EventPriority.CRITICAL);
      expect(Object.isFrozen(reg)).toBe(true);
    });

    it('should create immutable SubscriptionExecution model', () => {
      const exec = createSubscriptionExecution({
        subscriptionId: 'sub_1',
        eventId: 'evt_1',
        eventType: 'user.created',
        success: true,
        durationMs: 1.5,
      });

      expect(exec.subscriptionId).toBe('sub_1');
      expect(exec.eventId).toBe('evt_1');
      expect(exec.durationMs).toBe(1.5);
      expect(Object.isFrozen(exec)).toBe(true);
    });

    it('should create immutable SubscriptionExecution failure model', () => {
      const exec = createSubscriptionExecution({
        subscriptionId: 'sub_err',
        eventId: 'evt_2',
        eventType: 'order.failed',
        success: false,
        durationMs: 3.2,
        error: 'Database connection timeout',
      });

      expect(exec.success).toBe(false);
      expect(exec.error).toBe('Database connection timeout');
      expect(Object.isFrozen(exec)).toBe(true);
    });

    it('should create immutable SubscriptionResult model', () => {
      const pubEvt = { event: { eventId: 'e1', eventType: 't1', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      const res = createSubscriptionResult({
        publishedEvent: pubEvt as any,
        executions: [],
      });

      expect(res.publishedEvent).toBe(pubEvt);
      expect(res.totalExecutions).toBe(0);
      expect(Object.isFrozen(res)).toBe(true);
      expect(Object.isFrozen(res.executions)).toBe(true);
    });

    it('should create immutable SubscriberStatistics and SubscriberHealth models', () => {
      const stats = createSubscriberStatistics({ totalExecutions: 10, successfulExecutions: 9, failedExecutions: 1, averageExecutionMs: 2.5 });
      expect(stats.totalExecutions).toBe(10);
      expect(stats.failedExecutions).toBe(1);
      expect(stats.averageExecutionMs).toBe(2.5);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createSubscriberHealth({ healthy: true, errorRate: 0.05, activeSubscriptionsCount: 5, totalExecutionsCount: 100 });
      expect(health.healthy).toBe(true);
      expect(health.errorRate).toBe(0.05);
      expect(health.activeSubscriptionsCount).toBe(5);
      expect(Object.isFrozen(health)).toBe(true);
    });
  });

  describe('2. SubscriberRegistry Engine', () => {
    it('should subscribe handler and return active EventSubscription', () => {
      const registry = new SubscriberRegistry();
      const sub = registry.subscribe('order.placed', () => {}, EventPriority.NORMAL);

      expect(sub.eventType).toBe('order.placed');
      expect(sub.priority).toBe(EventPriority.NORMAL);
      expect(registry.count('order.placed')).toBe(1);
      expect(registry.count()).toBe(1);
    });

    it('should trim event type names in subscribe and lookup methods', () => {
      const registry = new SubscriberRegistry();
      const sub = registry.subscribe('  trimmed.topic  ', () => {});

      expect(registry.count('trimmed.topic')).toBe(1);
      expect(registry.getSubscriber(sub.subscriptionId)).toBeDefined();
    });

    it('should return undefined for non-existent subscriptionId in getSubscriber()', () => {
      const registry = new SubscriberRegistry();
      expect(registry.getSubscriber('invalid_id')).toBeUndefined();
    });

    it('should throw EventValidationException when subscribing with empty eventType or invalid handler', () => {
      const registry = new SubscriberRegistry();
      expect(() => registry.subscribe('  ', () => {})).toThrow(EventValidationException);
      expect(() => registry.subscribe('order.placed', null as any)).toThrow(EventValidationException);
    });

    it('should unsubscribe subscriber by subscriptionId', () => {
      const registry = new SubscriberRegistry();
      const sub = registry.subscribe('order.placed', () => {});

      expect(registry.unsubscribe(sub.subscriptionId)).toBe(true);
      expect(registry.count('order.placed')).toBe(0);
      expect(registry.unsubscribe(sub.subscriptionId)).toBe(false);
    });

    it('should unsubscribeAll subscribers globally or by eventType', () => {
      const registry = new SubscriberRegistry();
      registry.subscribe('t1', () => {});
      registry.subscribe('t1', () => {});
      registry.subscribe('t2', () => {});

      expect(registry.unsubscribeAll('t1')).toBe(2);
      expect(registry.count('t1')).toBe(0);
      expect(registry.count('t2')).toBe(1);

      expect(registry.unsubscribeAll()).toBe(1);
      expect(registry.count()).toBe(0);
    });

    it('should sort subscribers descending by priority (CRITICAL > HIGH > NORMAL > LOW)', () => {
      const registry = new SubscriberRegistry();
      registry.subscribe('prioritized.event', () => {}, EventPriority.NORMAL);
      registry.subscribe('prioritized.event', () => {}, EventPriority.CRITICAL);
      registry.subscribe('prioritized.event', () => {}, EventPriority.LOW);
      registry.subscribe('prioritized.event', () => {}, EventPriority.HIGH);

      const subscribers = registry.getSubscribers('prioritized.event');
      expect(subscribers.length).toBe(4);
      expect(subscribers[0].priority).toBe(EventPriority.CRITICAL);
      expect(subscribers[1].priority).toBe(EventPriority.HIGH);
      expect(subscribers[2].priority).toBe(EventPriority.NORMAL);
      expect(subscribers[3].priority).toBe(EventPriority.LOW);
    });

    it('should return empty frozen array when getSubscribers() is called for unregistered eventType', () => {
      const registry = new SubscriberRegistry();
      const subs = registry.getSubscribers('nonexistent');
      expect(subs.length).toBe(0);
      expect(Object.isFrozen(subs)).toBe(true);
    });

    it('should list all active subscriptions', () => {
      const registry = new SubscriberRegistry();
      registry.subscribe('e1', () => {});
      registry.subscribe('e2', () => {});

      const list = registry.listSubscriptions();
      expect(list.length).toBe(2);
      expect(list.map((s) => s.eventType)).toEqual(['e1', 'e2']);
    });

    it('should list subscribers filtered by eventType or globally', () => {
      const registry = new SubscriberRegistry();
      registry.subscribe('e1', () => {});
      registry.subscribe('e2', () => {});

      expect(registry.listSubscribers().length).toBe(2);
      expect(registry.listSubscribers('e1').length).toBe(1);
    });

    it('should clear all subscriber registrations', () => {
      const registry = new SubscriberRegistry();
      registry.subscribe('e1', () => {});
      registry.subscribe('e2', () => {});

      registry.clear();
      expect(registry.count()).toBe(0);
      expect(registry.listSubscriptions().length).toBe(0);
    });
  });

  describe('3. SubscriptionManager Engine & Exception Isolation', () => {
    it('should execute subscribers and record execution results', () => {
      const manager = new SubscriptionManager();
      let executed = false;

      const sub = createSubscriberRegistration({
        eventType: 'test.evt',
        handler: () => {
          executed = true;
        },
      });

      const pubEvt = { event: { eventId: 'evt_1', eventType: 'test.evt', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      const res = manager.executeSubscribers(pubEvt as any, [sub]);

      expect(executed).toBe(true);
      expect(res.totalExecutions).toBe(1);
      expect(res.successfulExecutions).toBe(1);
      expect(res.failedExecutions).toBe(0);
      expect(res.executions[0].success).toBe(true);
    });

    it('should handle execution with empty subscribers array cleanly', () => {
      const manager = new SubscriptionManager();
      const pubEvt = { event: { eventId: 'evt_1', eventType: 'test.evt', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      const res = manager.executeSubscribers(pubEvt as any, []);

      expect(res.totalExecutions).toBe(0);
      expect(res.successfulExecutions).toBe(0);
      expect(res.failedExecutions).toBe(0);
    });

    it('should isolate subscriber exceptions and continue executing remaining subscribers', () => {
      const manager = new SubscriptionManager();
      const executionOrder: string[] = [];

      const sub1 = createSubscriberRegistration({
        eventType: 'test.evt',
        handler: () => {
          executionOrder.push('sub1');
          throw new Error('Subscriber 1 failed!');
        },
      });

      const sub2 = createSubscriberRegistration({
        eventType: 'test.evt',
        handler: () => {
          executionOrder.push('sub2');
        },
      });

      const pubEvt = { event: { eventId: 'evt_1', eventType: 'test.evt', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      const res = manager.executeSubscribers(pubEvt as any, [sub1, sub2]);

      expect(executionOrder).toEqual(['sub1', 'sub2']);
      expect(res.totalExecutions).toBe(2);
      expect(res.successfulExecutions).toBe(1);
      expect(res.failedExecutions).toBe(1);
      expect(res.executions[0].success).toBe(false);
      expect(res.executions[0].error).toContain('Subscriber 1 failed');
      expect(res.executions[1].success).toBe(true);
    });

    it('should track execution telemetry statistics and health', () => {
      const manager = new SubscriptionManager();

      const subGood = createSubscriberRegistration({ eventType: 't', handler: () => {} });
      const subBad = createSubscriberRegistration({
        eventType: 't',
        handler: () => {
          throw new Error('fail');
        },
      });

      const pubEvt = { event: { eventId: 'e1', eventType: 't', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };
      manager.executeSubscribers(pubEvt as any, [subGood, subBad]);

      const stats = manager.statistics();
      expect(stats.totalExecutions).toBe(2);
      expect(stats.successfulExecutions).toBe(1);
      expect(stats.failedExecutions).toBe(1);

      const health = manager.health();
      expect(health.totalExecutionsCount).toBe(2);
      expect(health.errorRate).toBe(0.5); // 50% error rate
      expect(health.healthy).toBe(false); // Unhealthy if errorRate > 0.1
    });

    it('should report healthy state when error rate is 0', () => {
      const manager = new SubscriptionManager();
      const sub = createSubscriberRegistration({ eventType: 't', handler: () => {} });
      const pubEvt = { event: { eventId: 'e1', eventType: 't', payload: {}, priority: EventPriority.NORMAL, timestamp: '' }, publishedAt: '', sequenceNumber: 1 };

      manager.executeSubscribers(pubEvt as any, [sub]);
      const health = manager.health();

      expect(health.healthy).toBe(true);
      expect(health.errorRate).toBe(0);
    });
  });

  describe('4. EventBus PubSub Integration', () => {
    it('should execute registered subscribers automatically when an event is published', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'user.signup' }));

      const bus = new EventBus(eventRegistry);
      let receivedPayload: any = null;

      bus.subscribe('user.signup', (evt) => {
        receivedPayload = evt.payload;
      });

      bus.publish('user.signup', { userId: 'u999' });
      expect(receivedPayload).toEqual({ userId: 'u999' });
    });

    it('should execute multiple subscribers in priority order upon publish', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'payment.completed' }));

      const bus = new EventBus(eventRegistry);
      const executionOrder: string[] = [];

      bus.subscribe('payment.completed', () => {
        executionOrder.push('normal');
      }, EventPriority.NORMAL);

      bus.subscribe('payment.completed', () => {
        executionOrder.push('critical');
      }, EventPriority.CRITICAL);

      bus.subscribe('payment.completed', () => {
        executionOrder.push('high');
      }, EventPriority.HIGH);

      bus.publish('payment.completed', { amount: 100 });
      expect(executionOrder).toEqual(['critical', 'high', 'normal']);
    });

    it('should delegate unsubscribe and subscriberCount through EventBus', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'item.added' }));

      const bus = new EventBus(eventRegistry);
      const sub = bus.subscribe('item.added', () => {});

      expect(bus.subscriberCount('item.added')).toBe(1);
      expect(bus.listSubscribers('item.added').length).toBe(1);
      expect(bus.listSubscriptions().length).toBe(1);

      expect(bus.unsubscribe(sub.subscriptionId)).toBe(true);
      expect(bus.subscriberCount('item.added')).toBe(0);
    });
  });

  describe('5. Provider Integration & Runtime Delegation', () => {
    it('should delegate subscribe, unsubscribe, listSubscribers, and subscriberCount through EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'prov.evt' }));

      let called = false;
      const sub = provider.subscribe('prov.evt', () => {
        called = true;
      });

      expect(provider.subscriberCount('prov.evt')).toBe(1);
      expect(provider.listSubscriptions().length).toBe(1);

      provider.publish('prov.evt', { a: 1 });
      expect(called).toBe(true);

      expect(provider.unsubscribe(sub.subscriptionId)).toBe(true);
      expect(provider.subscriberCount('prov.evt')).toBe(0);
    });

    it('should delegate subscriber APIs through EventRuntime coordinator', () => {
      const runtime = new EventRuntime();
      runtime.initialize();
      runtime.registerEvent(createEventRegistration({ eventType: 'rt.evt' }));

      let count = 0;
      runtime.subscribe('rt.evt', () => {
        count++;
      });

      expect(runtime.subscriberCount('rt.evt')).toBe(1);
      runtime.publish('rt.evt', {});
      expect(count).toBe(1);

      expect(runtime.unsubscribeAll('rt.evt')).toBe(1);
      expect(runtime.subscriberCount('rt.evt')).toBe(0);
    });

    it('should accept custom SubscriberRegistry and SubscriptionManager in EventProvider constructor', () => {
      const sReg = new SubscriberRegistry();
      const sMgr = new SubscriptionManager();

      const provider = new EventProvider(undefined, undefined, undefined, undefined, sReg, sMgr);
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'custom.sub' }));
      provider.subscribe('custom.sub', () => {});

      expect(provider.subscriberCount('custom.sub')).toBe(1);
    });

    it('should include subscriber telemetry in provider diagnostics()', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'diag.sub' }));
      provider.subscribe('diag.sub', () => {});
      provider.publish('diag.sub', {});

      const diag = provider.diagnostics();
      expect(diag.subscriberCount).toBe(1);
      expect(diag.subscriptionCount).toBe(1);
      expect(diag.subscriberStatistics).toBeDefined();
      expect(diag.subscriberHealth).toBeDefined();
    });

    it('should support PubSub flow via global singleton runtime helpers', () => {
      const runtime = getEventRuntime();
      const provider = getEventProvider();

      provider.initialize();
      runtime.registerEvent(createEventRegistration({ eventType: 'global.pubsub' }));

      let received = false;
      runtime.subscribe('global.pubsub', () => {
        received = true;
      });

      runtime.publish('global.pubsub', 'data');
      expect(received).toBe(true);
    });
  });
});
