import { beforeEach, describe, expect, it } from 'vitest';
import {
  createDeadLetterRecord,
  createDispatchHealth,
  createDispatchPolicy,
  createDispatchRecord,
  createDispatchStatistics,
  createEventRegistration,
  createFrontendEvent,
  createRoutingDecision,
  createRoutingRule,
  DispatchManager,
  EventBus,
  EventPriority,
  EventProvider,
  EventProviderException,
  EventRegistry,
  EventRouter,
  EventRuntime,
  EventValidationException,
  getEventProvider,
  getEventRuntime,
  resetEventProvider,
  resetEventRuntime,
} from '../../src/runtime/events';

describe('Phase 16.4.4 — Frontend Event Routing, Priority Dispatch & Filtering Engine', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable RoutingRule model', () => {
      const rule = createRoutingRule({
        name: 'UserAuditRule',
        topicPattern: 'user.*',
        priority: EventPriority.HIGH,
      });

      expect(rule.name).toBe('UserAuditRule');
      expect(rule.topicPattern).toBe('user.*');
      expect(rule.priority).toBe(EventPriority.HIGH);
      expect(rule.enabled).toBe(true);
      expect(rule.ruleId).toBeDefined();
      expect(Object.isFrozen(rule)).toBe(true);
    });

    it('should create immutable RoutingRule model with custom parameters', () => {
      const pred = (e: any) => e.payload.v > 10;
      const rule = createRoutingRule({
        ruleId: 'r_custom_50',
        name: 'CustomPredRule',
        topicPattern: 'sensor.**',
        predicate: pred,
        priority: EventPriority.CRITICAL,
        enabled: false,
      });

      expect(rule.ruleId).toBe('r_custom_50');
      expect(rule.name).toBe('CustomPredRule');
      expect(rule.predicate).toBe(pred);
      expect(rule.priority).toBe(EventPriority.CRITICAL);
      expect(rule.enabled).toBe(false);
      expect(Object.isFrozen(rule)).toBe(true);
    });

    it('should create immutable RoutingDecision model', () => {
      const evt = createFrontendEvent({ eventType: 'user.login', payload: {} });
      const rule = createRoutingRule({ name: 'R1', topicPattern: 'user.*' });

      const decision = createRoutingDecision({
        event: evt,
        matchedRules: [rule],
      });

      expect(decision.event).toBe(evt);
      expect(decision.matched).toBe(true);
      expect(decision.matchedRules.length).toBe(1);
      expect(Object.isFrozen(decision)).toBe(true);
      expect(Object.isFrozen(decision.matchedRules)).toBe(true);
    });

    it('should create immutable RoutingDecision model for unmatched event', () => {
      const evt = createFrontendEvent({ eventType: 'unmatched.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      expect(decision.matched).toBe(false);
      expect(decision.matchedRules.length).toBe(0);
      expect(Object.isFrozen(decision)).toBe(true);
    });

    it('should create immutable DispatchPolicy and DispatchRecord models', () => {
      const policy = createDispatchPolicy({ name: 'CustomPolicy', deadLetterEnabled: false, stopOnFirstFailure: true });
      expect(policy.name).toBe('CustomPolicy');
      expect(policy.deadLetterEnabled).toBe(false);
      expect(policy.stopOnFirstFailure).toBe(true);
      expect(Object.isFrozen(policy)).toBe(true);

      const evt = createFrontendEvent({ eventType: 'e1', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });
      const record = createDispatchRecord({ decision, success: true, totalDurationMs: 1.2 });

      expect(record.decision).toBe(decision);
      expect(record.success).toBe(true);
      expect(record.totalDurationMs).toBe(1.2);
      expect(Object.isFrozen(record)).toBe(true);
      expect(Object.isFrozen(record.executions)).toBe(true);
    });

    it('should create immutable DispatchStatistics, DispatchHealth, and DeadLetterRecord models', () => {
      const stats = createDispatchStatistics({ totalDispatches: 10, deadLetterCount: 2, averageDispatchMs: 3.4 });
      expect(stats.totalDispatches).toBe(10);
      expect(stats.deadLetterCount).toBe(2);
      expect(stats.averageDispatchMs).toBe(3.4);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createDispatchHealth({ healthy: true, dispatchErrorRate: 0.05, activeRulesCount: 3 });
      expect(health.healthy).toBe(true);
      expect(health.dispatchErrorRate).toBe(0.05);
      expect(health.activeRulesCount).toBe(3);
      expect(Object.isFrozen(health)).toBe(true);

      const evt = createFrontendEvent({ eventType: 'err.evt', payload: {} });
      const deadLetter = createDeadLetterRecord({ event: evt, reason: 'Execution timeout', error: 'Err' });
      expect(deadLetter.event).toBe(evt);
      expect(deadLetter.reason).toBe('Execution timeout');
      expect(Object.isFrozen(deadLetter)).toBe(true);
    });
  });

  describe('2. EventRouter Engine', () => {
    it('should register routing rule and verify listRules() and getRule()', () => {
      const router = new EventRouter();
      const rule = createRoutingRule({ name: 'Rule1', topicPattern: 'file.upload' });

      router.registerRule(rule);
      expect(router.getRule(rule.ruleId)).toBe(rule);
      expect(router.listRules().length).toBe(1);
    });

    it('should return undefined when getRule() is called for non-existent ruleId', () => {
      const router = new EventRouter();
      expect(router.getRule('invalid_id')).toBeUndefined();
    });

    it('should reject null or empty rule parameters', () => {
      const router = new EventRouter();
      expect(() => router.registerRule(null as any)).toThrow(EventValidationException);
      expect(() => router.registerRule(createRoutingRule({ name: '   ', topicPattern: 't' }))).toThrow(
        EventValidationException,
      );
      expect(() => router.registerRule(createRoutingRule({ name: 'n', topicPattern: '  ' }))).toThrow(
        EventValidationException,
      );
    });

    it('should reject duplicate ruleId registration', () => {
      const router = new EventRouter();
      const r1 = createRoutingRule({ ruleId: 'r100', name: 'R1', topicPattern: 't1' });
      const r2 = createRoutingRule({ ruleId: 'r100', name: 'R2', topicPattern: 't2' });

      router.registerRule(r1);
      expect(() => router.registerRule(r2)).toThrow(EventProviderException);
    });

    it('should remove routing rule by ruleId', () => {
      const router = new EventRouter();
      const rule = createRoutingRule({ name: 'Temp', topicPattern: 'temp.*' });

      router.registerRule(rule);
      expect(router.removeRule(rule.ruleId)).toBe(true);
      expect(router.getRule(rule.ruleId)).toBeUndefined();
      expect(router.removeRule(rule.ruleId)).toBe(false);
    });

    it('should perform exact topic pattern matching', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'ExactRule', topicPattern: 'auth.login' }));

      const d1 = router.route(createFrontendEvent({ eventType: 'auth.login', payload: {} }));
      expect(d1.matched).toBe(true);
      expect(d1.matchedRules.length).toBe(1);

      const d2 = router.route(createFrontendEvent({ eventType: 'auth.logout', payload: {} }));
      expect(d2.matched).toBe(false);
      expect(d2.matchedRules.length).toBe(0);
    });

    it('should perform single-level wildcard (*) topic matching', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'WildcardRule', topicPattern: 'user.*' }));

      const d1 = router.route(createFrontendEvent({ eventType: 'user.created', payload: {} }));
      expect(d1.matched).toBe(true);

      const d2 = router.route(createFrontendEvent({ eventType: 'user.deleted', payload: {} }));
      expect(d2.matched).toBe(true);

      const d3 = router.route(createFrontendEvent({ eventType: 'user.profile.updated', payload: {} }));
      expect(d3.matched).toBe(false); // Single wildcard '*' does not match sub-namespaces
    });

    it('should perform multi-level wildcard (**) topic matching', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'MultiWildcard', topicPattern: 'system.**' }));

      const d1 = router.route(createFrontendEvent({ eventType: 'system.cpu', payload: {} }));
      expect(d1.matched).toBe(true);

      const d2 = router.route(createFrontendEvent({ eventType: 'system.memory.usage.alert', payload: {} }));
      expect(d2.matched).toBe(true);

      const d3 = router.route(createFrontendEvent({ eventType: 'network.ping', payload: {} }));
      expect(d3.matched).toBe(false);
    });

    it('should skip disabled routing rules during evaluation', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'DisabledRule', topicPattern: 'user.*', enabled: false }));

      const decision = router.route(createFrontendEvent({ eventType: 'user.login', payload: {} }));
      expect(decision.matched).toBe(false);
    });

    it('should evaluate predicate functions when routing events', () => {
      const router = new EventRouter();
      router.registerRule(
        createRoutingRule({
          name: 'HighPriorityOrders',
          topicPattern: 'order.placed',
          predicate: (evt) => (evt.payload as any).amount > 1000,
        }),
      );

      const d1 = router.route(createFrontendEvent({ eventType: 'order.placed', payload: { amount: 500 } }));
      expect(d1.matched).toBe(false);

      const d2 = router.route(createFrontendEvent({ eventType: 'order.placed', payload: { amount: 2000 } }));
      expect(d2.matched).toBe(true);
    });

    it('should sort matched rules by priority descending', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'LowRule', topicPattern: 't', priority: EventPriority.LOW }));
      router.registerRule(createRoutingRule({ name: 'CriticalRule', topicPattern: 't', priority: EventPriority.CRITICAL }));
      router.registerRule(createRoutingRule({ name: 'NormalRule', topicPattern: 't', priority: EventPriority.NORMAL }));

      const decision = router.route(createFrontendEvent({ eventType: 't', payload: {} }));
      expect(decision.matchedRules.map((r) => r.name)).toEqual(['CriticalRule', 'NormalRule', 'LowRule']);
    });

    it('should clear all routing rules', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'R1', topicPattern: 't1' }));
      router.registerRule(createRoutingRule({ name: 'R2', topicPattern: 't2' }));

      router.clearRules();
      expect(router.listRules().length).toBe(0);
    });

    it('should track evaluation telemetry (matches, misses, total evaluations)', () => {
      const router = new EventRouter();
      router.registerRule(createRoutingRule({ name: 'Match', topicPattern: 'm' }));

      router.route(createFrontendEvent({ eventType: 'm', payload: {} }));
      router.route(createFrontendEvent({ eventType: 'unknown', payload: {} }));

      const telem = router.telemetry();
      expect(telem.evaluations).toBe(2);
      expect(telem.matches).toBe(1);
      expect(telem.misses).toBe(1);
    });
  });

  describe('3. DispatchManager Engine & Dead Letters', () => {
    it('should dispatch routing decision to subscribers and return clean DispatchRecord', () => {
      const dispatchManager = new DispatchManager();
      const evt = createFrontendEvent({ eventType: 'disp.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      const record = dispatchManager.dispatch(decision, []);
      expect(record.success).toBe(true);
      expect(dispatchManager.statistics().totalDispatches).toBe(1);
    });

    it('should accept custom DispatchPolicy in DispatchManager constructor', () => {
      const policy = createDispatchPolicy({ deadLetterEnabled: false });
      const dispatchManager = new DispatchManager(undefined, policy);

      const evt = createFrontendEvent({ eventType: 'faulty.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      const failingSub = {
        subscriptionId: 'sub_fail',
        eventType: 'faulty.evt',
        handler: () => {
          throw new Error('boom');
        },
        priority: EventPriority.NORMAL,
        subscribedAt: new Date().toISOString(),
        active: true,
      };

      dispatchManager.dispatch(decision, [failingSub as any]);
      expect(dispatchManager.listDeadLetters().length).toBe(0); // Dead letter disabled by policy
    });

    it('should record dead-letter entry when a subscriber fails execution during dispatch', () => {
      const dispatchManager = new DispatchManager();
      const evt = createFrontendEvent({ eventType: 'faulty.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      const failingSub = {
        subscriptionId: 'sub_fail',
        eventType: 'faulty.evt',
        handler: () => {
          throw new Error('Subscriber execution boom!');
        },
        priority: EventPriority.NORMAL,
        subscribedAt: new Date().toISOString(),
        active: true,
      };

      const record = dispatchManager.dispatch(decision, [failingSub as any]);
      expect(record.success).toBe(false);
      expect(dispatchManager.statistics().deadLetterCount).toBe(1);

      const deadLetters = dispatchManager.listDeadLetters();
      expect(deadLetters.length).toBe(1);
      expect(deadLetters[0].error).toContain('Subscriber execution boom');
    });

    it('should clear dead-letter records', () => {
      const dispatchManager = new DispatchManager();
      const evt = createFrontendEvent({ eventType: 'faulty.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      const failingSub = {
        subscriptionId: 'sub_fail',
        eventType: 'faulty.evt',
        handler: () => {
          throw new Error('fail');
        },
        priority: EventPriority.NORMAL,
        subscribedAt: new Date().toISOString(),
        active: true,
      };

      dispatchManager.dispatch(decision, [failingSub as any]);
      expect(dispatchManager.listDeadLetters().length).toBe(1);

      dispatchManager.clearDeadLetters();
      expect(dispatchManager.listDeadLetters().length).toBe(0);
    });

    it('should report healthy state when dispatch error rate is 0', () => {
      const dispatchManager = new DispatchManager();
      const evt = createFrontendEvent({ eventType: 'good.evt', payload: {} });
      const decision = createRoutingDecision({ event: evt, matchedRules: [] });

      dispatchManager.dispatch(decision, []);
      const health = dispatchManager.health();

      expect(health.healthy).toBe(true);
      expect(health.dispatchErrorRate).toBe(0);
    });
  });

  describe('4. EventBus End-to-End Routing & Dispatch Integration', () => {
    it('should evaluate routing rules and dispatch events to subscribers upon publish', () => {
      const eventRegistry = new EventRegistry();
      eventRegistry.register(createEventRegistration({ eventType: 'order.completed' }));

      const bus = new EventBus(eventRegistry);
      let payloadReceived: any = null;

      bus.subscribe('order.completed', (evt) => {
        payloadReceived = evt.payload;
      });

      bus.publish('order.completed', { orderId: 'ord_123' });
      expect(payloadReceived).toEqual({ orderId: 'ord_123' });
    });
  });

  describe('5. Provider Integration & Runtime Delegation', () => {
    it('should delegate registerRoutingRule, removeRoutingRule, listRoutingRules, and route through EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();

      const rule = createRoutingRule({ name: 'ProvRule', topicPattern: 'prov.*' });
      provider.registerRoutingRule(rule);

      expect(provider.listRoutingRules().length).toBe(1);

      const decision = provider.route(createFrontendEvent({ eventType: 'prov.test', payload: {} }));
      expect(decision.matched).toBe(true);

      expect(provider.removeRoutingRule(rule.ruleId)).toBe(true);
      expect(provider.listRoutingRules().length).toBe(0);
    });

    it('should return false for removeRoutingRule on non-existent ruleId via EventProvider and EventRuntime', () => {
      const provider = new EventProvider();
      provider.initialize();
      const runtime = new EventRuntime(provider);

      expect(provider.removeRoutingRule('unknown')).toBe(false);
      expect(runtime.removeRoutingRule('unknown')).toBe(false);
    });

    it('should accept custom EventRouter and DispatchManager in EventProvider constructor', () => {
      const router = new EventRouter();
      const dispatchManager = new DispatchManager();

      const provider = new EventProvider(undefined, undefined, undefined, undefined, undefined, undefined, router, dispatchManager);
      provider.initialize();
      provider.registerRoutingRule(createRoutingRule({ name: 'CustomR', topicPattern: 'c.*' }));

      expect(provider.listRoutingRules().length).toBe(1);
    });

    it('should delegate routing APIs through EventRuntime coordinator', () => {
      const runtime = new EventRuntime();
      runtime.initialize();

      const rule = createRoutingRule({ name: 'RtRule', topicPattern: 'rt.*' });
      runtime.registerRoutingRule(rule);

      expect(runtime.listRoutingRules().length).toBe(1);

      const decision = runtime.route(createFrontendEvent({ eventType: 'rt.action', payload: {} }));
      expect(decision.matched).toBe(true);

      expect(runtime.dispatchStatistics()).toBeDefined();
      expect(runtime.dispatchHealth()).toBeDefined();
    });

    it('should include routing rules and dispatch statistics in provider diagnostics()', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'diag.route' }));
      provider.registerRoutingRule(createRoutingRule({ name: 'DiagRule', topicPattern: 'diag.*' }));

      provider.publish('diag.route', { x: 1 });

      const diag = provider.diagnostics();
      expect(diag.routingRules).toContain('DiagRule (diag.*)');
      expect(diag.dispatchStatistics).toBeDefined();
      expect(diag.dispatchHealth).toBeDefined();
      expect(diag.routingEvaluations).toBe(1);
    });

    it('should support routing via global singleton runtime helpers', () => {
      const runtime = getEventRuntime();
      const provider = getEventProvider();

      provider.initialize();
      runtime.registerRoutingRule(createRoutingRule({ name: 'GlobalRule', topicPattern: 'glob.*' }));

      const decision = runtime.route(createFrontendEvent({ eventType: 'glob.evt', payload: {} }));
      expect(decision.matched).toBe(true);
    });
  });
});
