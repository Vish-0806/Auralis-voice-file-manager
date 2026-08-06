import { beforeEach, describe, expect, it } from 'vitest';
import {
  createCertificationHealth,
  createCertificationIssue,
  createCertificationReport,
  createCertificationStatistics,
  createEventCertification,
  createEventCertificationSummary,
  createEventRegistration,
  createFrontendEvent,
  createRoutingRule,
  DeliveryStatus,
  EventCertifier,
  EventPriority,
  EventProvider,
  EventRuntime,
  getEventProvider,
  getEventRuntime,
  resetEventProvider,
  resetEventRuntime,
} from '../../src/runtime/events';

describe('Phase 16.4.6 — Frontend Event Runtime Production Certification & End-to-End Verification', () => {
  beforeEach(() => {
    resetEventRuntime();
    resetEventProvider();
  });

  describe('1. Certification Models & Factory Functions', () => {
    it('should create immutable CertificationIssue model', () => {
      const issue = createCertificationIssue({
        severity: 'WARNING',
        category: 'QUEUE',
        message: 'Queue depth approaching threshold',
      });

      expect(issue.severity).toBe('WARNING');
      expect(issue.category).toBe('QUEUE');
      expect(issue.message).toBe('Queue depth approaching threshold');
      expect(Object.isFrozen(issue)).toBe(true);
    });

    it('should create immutable EventCertification model', () => {
      const cert = createEventCertification({ certified: true, score: 100, passedChecks: 10, failedChecks: 0 });

      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
      expect(cert.passedChecks).toBe(10);
      expect(Object.isFrozen(cert)).toBe(true);
    });

    it('should create immutable EventCertificationSummary model', () => {
      const summary = createEventCertificationSummary({ certified: true, score: 95, status: 'PASSED' });
      expect(summary.certified).toBe(true);
      expect(summary.score).toBe(95);
      expect(summary.status).toBe('PASSED');
      expect(Object.isFrozen(summary)).toBe(true);
    });

    it('should create immutable CertificationStatistics and CertificationHealth models', () => {
      const stats = createCertificationStatistics({ totalCertifications: 5, passedCertifications: 5, averageScore: 100 });
      expect(stats.totalCertifications).toBe(5);
      expect(stats.passedCertifications).toBe(5);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createCertificationHealth({ healthy: true, certified: true, score: 100 });
      expect(health.healthy).toBe(true);
      expect(health.score).toBe(100);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable CertificationReport model', () => {
      const provider = new EventProvider();
      provider.initialize();
      const diag = provider.diagnostics();

      const report = createCertificationReport({ diagnostics: diag });
      expect(report.certification.certified).toBe(true);
      expect(report.summary.status).toBe('PASSED');
      expect(Object.isFrozen(report)).toBe(true);
      expect(Object.isFrozen(report.issues)).toBe(true);
    });
  });

  describe('2. EventCertifier Engine & Verification Checks', () => {
    it('should run certification on operational EventProvider and return score of 100', () => {
      const provider = new EventProvider();
      provider.initialize();

      const certifier = new EventCertifier();
      const report = certifier.runCertification(provider);

      expect(report.certification.certified).toBe(true);
      expect(report.certification.score).toBe(100);
      expect(report.certification.passedChecks).toBe(10);
      expect(report.certification.failedChecks).toBe(0);
      expect(report.issues.length).toBe(0);
    });

    it('should return EventCertification snapshot via certify() method', () => {
      const provider = new EventProvider();
      provider.initialize();

      const certifier = new EventCertifier();
      const cert = certifier.certify(provider);

      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
    });

    it('should return CertificationReport via certificationReport() method', () => {
      const provider = new EventProvider();
      provider.initialize();

      const certifier = new EventCertifier();
      const report = certifier.certificationReport(provider);

      expect(report.summary.certified).toBe(true);
      expect(report.diagnostics).toBeDefined();
    });

    it('should log issue and record failed check when provider health check fails on uninitialized provider', () => {
      const provider = new EventProvider(); // Uninitialized
      const certifier = new EventCertifier();

      const report = certifier.runCertification(provider);
      expect(report.certification.certified).toBe(false);
      expect(report.certification.failedChecks).toBeGreaterThan(0);
      expect(report.issues.some((i) => i.category === 'LIFECYCLE')).toBe(true);
    });
  });

  describe('3. End-to-End Subsystem Verifications', () => {
    it('1. Lifecycle: initialize -> operational -> shutdown -> restart', () => {
      const provider = new EventProvider();
      expect(provider.health().healthy).toBe(false);

      provider.initialize();
      expect(provider.health().healthy).toBe(true);

      provider.shutdown();
      expect(provider.health().healthy).toBe(false);

      provider.restart();
      expect(provider.health().healthy).toBe(true);
    });

    it('2. Event Registration & Sequence Numbering', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'seq.evt' }));

      const p1 = provider.publish('seq.evt', { n: 1 });
      const p2 = provider.publish('seq.evt', { n: 2 });

      expect(p1.sequenceNumber).toBe(1);
      expect(p2.sequenceNumber).toBe(2);
    });

    it('3. PubSub Handler Execution & Priority Ordering', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'ps.evt' }));

      const callOrder: string[] = [];
      provider.subscribe('ps.evt', () => { callOrder.push('low'); }, EventPriority.LOW);
      provider.subscribe('ps.evt', () => { callOrder.push('critical'); }, EventPriority.CRITICAL);
      provider.subscribe('ps.evt', () => { callOrder.push('normal'); }, EventPriority.NORMAL);

      provider.publish('ps.evt', {});
      expect(callOrder).toEqual(['critical', 'normal', 'low']);
    });

    it('4. Exception Isolation during dispatch', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'err.evt' }));

      let secondExecuted = false;
      provider.subscribe(
        'err.evt',
        () => {
          throw new Error('Boom');
        },
        EventPriority.HIGH,
      );
      provider.subscribe(
        'err.evt',
        () => {
          secondExecuted = true;
        },
        EventPriority.NORMAL,
      );

      provider.publish('err.evt', {});
      expect(secondExecuted).toBe(true);
    });

    it('5. Event Router Wildcard & Predicate Matching', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerRoutingRule(
        createRoutingRule({
          name: 'HighValOrders',
          topicPattern: 'orders.**',
          predicate: (e) => (e.payload as any).amount > 500,
        }),
      );

      const d1 = provider.route(createFrontendEvent({ eventType: 'orders.uk.placed', payload: { amount: 100 } }));
      expect(d1.matched).toBe(false);

      const d2 = provider.route(createFrontendEvent({ eventType: 'orders.uk.placed', payload: { amount: 1000 } }));
      expect(d2.matched).toBe(true);
    });

    it('6. Priority Event Queueing & Dequeueing', () => {
      const provider = new EventProvider();
      provider.initialize();

      provider.enqueue(createFrontendEvent({ eventType: 'q.low', payload: {}, priority: EventPriority.LOW }));
      provider.enqueue(createFrontendEvent({ eventType: 'q.critical', payload: {}, priority: EventPriority.CRITICAL }));

      expect(provider.queueSize()).toBe(2);
      expect(provider.dequeue()?.event.eventType).toBe('q.critical');
      expect(provider.dequeue()?.event.eventType).toBe('q.low');
    });

    it('7. Delivery Acknowledgements & Retry Operations', () => {
      const provider = new EventProvider();
      provider.initialize();

      const ack = provider.acknowledge('q99', DeliveryStatus.DELIVERED);
      expect(ack.queueId).toBe('q99');

      expect(provider.retry('q99')).toBe(true);
    });

    it('8. Event History Replay Engine', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'replay.evt' }));

      provider.publish('replay.evt', { v: 1 });
      provider.publish('replay.evt', { v: 2 });

      const replays = provider.replay();
      expect(replays.length).toBe(2);
    });

    it('9. Dead Letter Queue Listing & Clearing', () => {
      const provider = new EventProvider();
      provider.initialize();

      expect(provider.deadLetters()).toBeDefined();
      provider.clearDeadLetters();
      expect(provider.deadLetters().length).toBe(0);
    });

    it('10. Diagnostics Aggregation Payload', () => {
      const provider = new EventProvider();
      provider.initialize();
      provider.registerEvent(createEventRegistration({ eventType: 'diag.evt' }));

      provider.publish('diag.evt', {});

      const diag = provider.diagnostics();
      expect(diag.health.healthy).toBe(true);
      expect(diag.busStatistics?.publishCount).toBe(1);
      expect(diag.certification?.certified).toBe(true);
      expect(diag.certificationSummary?.status).toBe('PASSED');
    });
  });

  describe('4. Provider Integration & Runtime Coordinator Delegation', () => {
    it('should delegate certify(), runCertification(), and certificationReport() through EventProvider', () => {
      const provider = new EventProvider();
      provider.initialize();

      const cert = provider.certify();
      expect(cert.certified).toBe(true);

      const report = provider.runCertification();
      expect(report.summary.certified).toBe(true);

      const report2 = provider.certificationReport();
      expect(report2.certification.score).toBe(100);
    });

    it('should accept custom EventCertifier in EventProvider constructor', () => {
      const certifier = new EventCertifier();
      const provider = new EventProvider(
        undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined, undefined,
        certifier,
      );
      provider.initialize();

      expect(provider.certify().certified).toBe(true);
    });

    it('should delegate certification APIs through EventRuntime coordinator', () => {
      const runtime = new EventRuntime();
      runtime.initialize();

      const cert = runtime.certify();
      expect(cert.certified).toBe(true);

      const report = runtime.runCertification();
      expect(report.summary.certified).toBe(true);

      const report2 = runtime.certificationReport();
      expect(report2.certification.score).toBe(100);
    });

    it('should support certification operations via global singleton runtime helpers', () => {
      const runtime = getEventRuntime();
      const provider = getEventProvider();

      provider.initialize();
      const cert = runtime.certify();

      expect(cert.certified).toBe(true);
      expect(cert.score).toBe(100);
    });
  });
});
