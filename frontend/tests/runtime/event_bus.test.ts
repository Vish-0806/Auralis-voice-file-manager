import { beforeEach, describe, expect, it } from 'vitest';
import {
  createEventBusHealth,
  createEventBusStatistics,
  createEventHistory,
  createEventRegistration,
  createFrontendEvent,
  createPublishedEvent,
  EventBus,
  EventPriority,
  EventProvider,
  EventProviderException,
  EventRegistry,
  EventRuntime,
  EventValidationException,
  getEventProvider,
  getEventRuntime,
  resetEventProvider,
  resetEventRuntime,
} from '../../src/runtime/events';

describe('Phase 16.4.2 — Frontend Event Bus & Publish Registration Engine', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable EventRegistration model', () => {
      const reg = createEventRegistration({
        eventType: 'file.uploaded',
        description: 'Triggered when file upload completes',
        priority: EventPriority.HIGH,
      });

      expect(reg.eventType).toBe('file.uploaded');
      expect(reg.description).toBe('Triggered when file upload completes');
      expect(reg.priority).toBe(EventPriority.HIGH);
      expect(Object.isFrozen(reg)).toBe(true);
    });

    it('should create immutable PublishedEvent model', () => {
      const evt = createFrontendEvent({ eventType: 'file.uploaded', payload: { id: 'f1' } });
      const published = createPublishedEvent({ event: evt, sequenceNumber: 1 });

      expect(published.event).toBe(evt);
      expect(published.sequenceNumber).toBe(1);
      expect(published.publishedAt).toBeDefined();
      expect(Object.isFrozen(published)).toBe(true);
    });

    it('should create immutable EventHistory model', () => {
      const history = createEventHistory({ totalPublished: 10 });
      expect(history.totalPublished).toBe(10);
      expect(Object.isFrozen(history)).toBe(true);
      expect(Object.isFrozen(history.events)).toBe(true);
    });

    it('should create immutable EventBusStatistics and EventBusHealth models', () => {
      const stats = createEventBusStatistics({ publishCount: 5, historyCount: 5, averagePayloadSize: 42 });
      expect(stats.publishCount).toBe(5);
      expect(stats.averagePayloadSize).toBe(42);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createEventBusHealth({ healthy: true, totalPublishedEvents: 10 });
      expect(health.healthy).toBe(true);
      expect(health.totalPublishedEvents).toBe(10);
      expect(Object.isFrozen(health)).toBe(true);
    });
  });

  describe('2. EventRegistry Engine', () => {
    it('should register event definition and verify existence via contains() and get()', () => {
      const registry = new EventRegistry();
      const reg = createEventRegistration({ eventType: 'user.login' });

      registry.register(reg);
      expect(registry.contains('user.login')).toBe(true);
      expect(registry.get('user.login')).toBe(reg);
      expect(registry.count()).toBe(1);
    });

    it('should trim event type names in register, contains, get, and unregister', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: '  trimmed.event  ' }));

      expect(registry.contains('trimmed.event')).toBe(true);
      expect(registry.get(' trimmed.event ')).toBeDefined();
      expect(registry.unregister('  trimmed.event ')).toBe(true);
    });

    it('should return undefined for unregistered event type in get()', () => {
      const registry = new EventRegistry();
      expect(registry.get('unregistered')).toBeUndefined();
    });

    it('should reject registration of duplicate event type', () => {
      const registry = new EventRegistry();
      const r1 = createEventRegistration({ eventType: 'user.login' });
      const r2 = createEventRegistration({ eventType: 'user.login' });

      registry.register(r1);
      expect(() => registry.register(r2)).toThrow(EventProviderException);
      expect(registry.telemetry().duplicatesRejected).toBe(1);
    });

    it('should reject null or empty event type registration', () => {
      const registry = new EventRegistry();
      expect(() => registry.register(null as any)).toThrow(EventProviderException);
      expect(() => registry.register(createEventRegistration({ eventType: '   ' }))).toThrow(
        EventProviderException,
      );
    });

    it('should unregister event type by name', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'temp.event' }));

      expect(registry.unregister('temp.event')).toBe(true);
      expect(registry.contains('temp.event')).toBe(false);
      expect(registry.telemetry().unregistrationCount).toBe(1);
    });

    it('should return false when unregistering non-existent event type', () => {
      const registry = new EventRegistry();
      expect(registry.unregister('nonexistent')).toBe(false);
    });

    it('should list all registered event definitions', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'e1' }));
      registry.register(createEventRegistration({ eventType: 'e2' }));

      const list = registry.list();
      expect(list.length).toBe(2);
      expect(list.map((r) => r.eventType)).toEqual(['e1', 'e2']);
    });

    it('should clear all registered event definitions', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'e1' }));
      registry.register(createEventRegistration({ eventType: 'e2' }));

      registry.clear();
      expect(registry.count()).toBe(0);
      expect(registry.list().length).toBe(0);
    });

    it('should return frozen telemetry object', () => {
      const registry = new EventRegistry();
      const telem = registry.telemetry();
      expect(telem.registrationCount).toBe(0);
      expect(Object.isFrozen(telem)).toBe(true);
    });
  });

  describe('3. EventBus Engine & Event Publishing', () => {
    it('should publish registered event with monotonically increasing sequence numbers', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'app.start' }));

      const bus = new EventBus(registry);
      const p1 = bus.publish('app.start', { v: 1 });
      const p2 = bus.publish('app.start', { v: 2 });

      expect(p1.sequenceNumber).toBe(1);
      expect(p2.sequenceNumber).toBe(2);
      expect(p1.event.eventType).toBe('app.start');
      expect(p1.event.payload).toEqual({ v: 1 });
    });

    it('should default published event priority to registration priority if options.priority is omitted', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'urgent.alert', priority: EventPriority.CRITICAL }));

      const bus = new EventBus(registry);
      const published = bus.publish('urgent.alert', { msg: 'alert' });
      expect(published.event.priority).toBe(EventPriority.CRITICAL);
    });

    it('should throw EventValidationException when publishing unregistered event type', () => {
      const registry = new EventRegistry();
      const bus = new EventBus(registry);

      expect(() => bus.publish('unregistered.event', {})).toThrow(EventValidationException);
      expect(bus.statistics().failedPublishes).toBe(1);
    });

    it('should preserve event source, correlationId, and custom priority in published event', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'job.processed', priority: EventPriority.NORMAL }));

      const bus = new EventBus(registry);
      const published = bus.publish('job.processed', { jobId: 'j123' }, {
        source: 'WorkerNode',
        correlationId: 'corr_55',
        priority: EventPriority.CRITICAL,
      });

      expect(published.event.source).toBe('WorkerNode');
      expect(published.event.correlationId).toBe('corr_55');
      expect(published.event.priority).toBe(EventPriority.CRITICAL);
    });

    it('should record published events in event history', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'msg.sent' }));

      const bus = new EventBus(registry);
      bus.publish('msg.sent', { text: 'hello' });

      const history = bus.history();
      expect(history.events.length).toBe(1);
      expect(history.events[0].event.eventType).toBe('msg.sent');
      expect(history.totalPublished).toBe(1);
    });

    it('should enforce bounded history limit and shift oldest events when capacity is exceeded', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'stream.data' }));

      const maxHistory = 5;
      const bus = new EventBus(registry, undefined, undefined, maxHistory);

      for (let i = 1; i <= 10; i++) {
        bus.publish('stream.data', { seq: i });
      }

      const history = bus.history();
      expect(history.events.length).toBe(5); // Bound capacity is 5
      expect(history.totalPublished).toBe(10); // Total published count remains 10
      expect((history.events[0].event.payload as any).seq).toBe(6); // Oldest 1..5 shifted out
      expect((history.events[4].event.payload as any).seq).toBe(10);
    });

    it('should clear event history', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'e1' }));

      const bus = new EventBus(registry);
      bus.publish('e1', 'payload');

      expect(bus.history().events.length).toBe(1);
      bus.clearHistory();
      expect(bus.history().events.length).toBe(0);
    });

    it('should clear event history safely when history is already empty', () => {
      const registry = new EventRegistry();
      const bus = new EventBus(registry);
      expect(() => bus.clearHistory()).not.toThrow();
      expect(bus.history().events.length).toBe(0);
    });

    it('should calculate statistics and average payload size', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'data.point' }));

      const bus = new EventBus(registry);
      bus.publish('data.point', { a: '1234567890' }); // ~16 bytes JSON

      const stats = bus.statistics();
      expect(stats.publishCount).toBe(1);
      expect(stats.historyCount).toBe(1);
      expect(stats.averagePayloadSize).toBeGreaterThan(0);
    });

    it('should return 0 average payload size when publishCount is 0', () => {
      const registry = new EventRegistry();
      const bus = new EventBus(registry);
      const stats = bus.statistics();
      expect(stats.publishCount).toBe(0);
      expect(stats.averagePayloadSize).toBe(0);
    });

    it('should handle payload size calculation for null and undefined payloads', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'null.payload' }));

      const bus = new EventBus(registry);
      bus.publish('null.payload', null);
      bus.publish('null.payload', undefined);

      const stats = bus.statistics();
      expect(stats.publishCount).toBe(2);
      expect(stats.averagePayloadSize).toBe(0);
    });

    it('should handle payload size calculation fallback for circular structures', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'circ.payload' }));

      const bus = new EventBus(registry);
      const circ: any = {};
      circ.self = circ;

      bus.publish('circ.payload', circ);
      const stats = bus.statistics();
      expect(stats.publishCount).toBe(1);
      expect(stats.averagePayloadSize).toBe(100);
    });

    it('should report health metadata', () => {
      const registry = new EventRegistry();
      registry.register(createEventRegistration({ eventType: 'h.event' }));

      const bus = new EventBus(registry);
      bus.publish('h.event', {});

      const health = bus.health();
      expect(health.healthy).toBe(true);
      expect(health.registeredEventTypes).toBe(1);
      expect(health.totalPublishedEvents).toBe(1);
    });
  });

  describe('4. Provider & Runtime Delegation Integration', () => {
    it('should delegate registerEvent, containsEvent, listEvents, and publish through EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();

      const reg = createEventRegistration({ eventType: 'provider.evt' });
      provider.registerEvent(reg);

      expect(provider.containsEvent('provider.evt')).toBe(true);
      expect(provider.listEvents().length).toBe(1);

      const published = provider.publish('provider.evt', { data: 'test' });
      expect(published.event.eventType).toBe('provider.evt');

      expect(provider.history().events.length).toBe(1);
      provider.clearHistory();
      expect(provider.history().events.length).toBe(0);
    });

    it('should return false for unregisterEvent and containsEvent on unregistered types via EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();

      expect(provider.containsEvent('unknown')).toBe(false);
      expect(provider.unregisterEvent('unknown')).toBe(false);
    });

    it('should delegate event methods through EventRuntime coordinator', () => {
      const runtime = new EventRuntime();
      runtime.initialize();

      runtime.registerEvent(createEventRegistration({ eventType: 'runtime.evt' }));
      expect(runtime.containsEvent('runtime.evt')).toBe(true);

      const published = runtime.publish('runtime.evt', { val: 42 });
      expect(published.sequenceNumber).toBe(1);

      expect(runtime.history().events.length).toBe(1);
      expect(runtime.unregisterEvent('runtime.evt')).toBe(true);
      expect(runtime.containsEvent('runtime.evt')).toBe(false);
    });

    it('should return false for unregisterEvent and containsEvent on unregistered types via EventRuntime', () => {
      const runtime = new EventRuntime();
      runtime.initialize();

      expect(runtime.containsEvent('unknown')).toBe(false);
      expect(runtime.unregisterEvent('unknown')).toBe(false);
    });

    it('should include registered and published event telemetry in provider diagnostics()', () => {
      const provider = new EventProvider();
      provider.initialize();

      provider.registerEvent(createEventRegistration({ eventType: 'diag.evt' }));
      provider.publish('diag.evt', { x: 1 });

      const diag = provider.diagnostics();
      expect(diag.registeredEvents).toContain('diag.evt');
      expect(diag.publishedEvents).toBe(1);
      expect(diag.eventHistorySize).toBe(1);
      expect(diag.busStatistics).toBeDefined();
    });

    it('should interact cleanly with singleton runtime helpers', () => {
      const runtime = getEventRuntime();
      const provider = getEventProvider();

      provider.initialize();
      runtime.registerEvent(createEventRegistration({ eventType: 'global.evt' }));

      const published = runtime.publish('global.evt', 'global_data');
      expect(published.event.payload).toBe('global_data');
    });
  });
});
