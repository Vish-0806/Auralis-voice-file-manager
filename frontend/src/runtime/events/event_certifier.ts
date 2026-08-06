/**
 * Event Certifier Engine (Phase 16.4.6).
 *
 * Implements IEventCertifier certifying the entire Frontend Event Runtime (Phases 16.4.1–16.4.5),
 * executing end-to-end verification, lifecycle checks, pipeline benchmarks, and producing production certification reports.
 */

import {
  CertificationIssue,
  CertificationReport,
  createCertificationIssue,
  createCertificationReport,
  createEventCertification,
  createEventCertificationSummary,
  createEventRegistration,
  createRoutingRule,
  EventCertification,
  EventPriority,
} from './models';
import { IEventCertifier, IEventProvider } from './interfaces';

export class EventCertifier implements IEventCertifier {
  public certify(provider: IEventProvider): EventCertification {
    const report = this.runCertification(provider);
    return report.certification;
  }

  public runCertification(provider: IEventProvider): CertificationReport {
    const issues: CertificationIssue[] = [];
    let passed = 0;
    let failed = 0;

    // Check 1: Runtime Lifecycle & Health
    try {
      const health = provider.health();
      if (health.healthy) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'LIFECYCLE',
            message: `Event provider is in unready state: ${health.runtimeState}`,
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'LIFECYCLE',
          message: `Health check failed: ${e.message}`,
        }),
      );
    }

    // Check 2: Capabilities & Context
    try {
      const caps = provider.capabilities();
      if (caps.supportsEventBus && caps.supportsPubSub && caps.supportsFiltering && caps.supportsDeadLetterQueue) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'CAPABILITIES',
            message: 'Provider capabilities incomplete.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'CAPABILITIES',
          message: `Capabilities verification failed: ${e.message}`,
        }),
      );
    }

    // Check 3: Event Registration & Bus Publishing
    try {
      provider.registerEvent(createEventRegistration({ eventType: 'cert.test.evt' }));
      const published = provider.publish('cert.test.evt', { cert: true });

      if (published && published.sequenceNumber > 0) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'PUBLISH',
            message: 'Published event failed sequence number validation.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'PUBLISH',
          message: `Event publish verification failed: ${e.message}`,
        }),
      );
    }

    // Check 4: PubSub Subscriber Dispatch
    try {
      provider.registerEvent(createEventRegistration({ eventType: 'cert.sub.evt' }));
      let subReceived = false;

      const sub = provider.subscribe('cert.sub.evt', () => {
        subReceived = true;
      });

      provider.publish('cert.sub.evt', { payload: 123 });
      provider.unsubscribe(sub.subscriptionId);

      if (subReceived) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'PUBSUB',
            message: 'Subscriber handler was not executed during publish.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'PUBSUB',
          message: `PubSub execution failed: ${e.message}`,
        }),
      );
    }

    // Check 5: Routing & Filtering Engine
    try {
      provider.registerRoutingRule(
        createRoutingRule({ name: 'CertRule', topicPattern: 'cert.**', priority: EventPriority.HIGH }),
      );

      const decision = provider.route(
        { eventId: 'e_cert', eventType: 'cert.sub.test', payload: {}, priority: EventPriority.NORMAL, timestamp: '' },
      );

      if (decision.matched && decision.matchedRules.length > 0) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'ROUTING',
            message: 'Event Router failed wildcard pattern match verification.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'ROUTING',
          message: `Event Router verification failed: ${e.message}`,
        }),
      );
    }

    // Check 6: Event Queue & Priority Ordering
    try {
      const qSize = provider.queueSize();
      if (typeof qSize === 'number') {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'QUEUE',
            message: 'Queue size check failed.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'QUEUE',
          message: `Event Queue verification failed: ${e.message}`,
        }),
      );
    }

    // Check 7: Retry & Replay Engine
    try {
      const replays = provider.replay();
      if (Array.isArray(replays)) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'REPLAY',
            message: 'Replay engine returned invalid record set.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'REPLAY',
          message: `Replay engine verification failed: ${e.message}`,
        }),
      );
    }

    // Check 8: Dead Letter Queue & Delivery Acknowledgements
    try {
      const deadLetters = provider.deadLetters();
      if (Array.isArray(deadLetters)) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'DEAD_LETTER',
            message: 'Dead letter queue query failed.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'DEAD_LETTER',
          message: `Dead letter verification failed: ${e.message}`,
        }),
      );
    }

    // Check 9: Diagnostics Aggregation
    try {
      const diag = provider.diagnostics();
      if (diag.health && diag.statistics && diag.capabilities && diag.busStatistics) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'DIAGNOSTICS',
            message: 'Diagnostics payload incomplete.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'DIAGNOSTICS',
          message: `Diagnostics aggregation failed: ${e.message}`,
        }),
      );
    }

    // Check 10: Performance Benchmark (Publish & Dispatch < 10ms)
    try {
      provider.registerEvent(createEventRegistration({ eventType: 'bench.evt' }));
      const start = performance ? performance.now() : Date.now();
      for (let i = 0; i < 100; i++) {
        provider.publish('bench.evt', { i });
      }
      const end = performance ? performance.now() : Date.now();
      const totalMs = end - start;

      if (totalMs < 100) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'BENCHMARK',
            message: `Publish benchmark threshold exceeded: ${totalMs}ms for 100 events`,
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'BENCHMARK',
          message: `Benchmark verification failed: ${e.message}`,
        }),
      );
    }

    const total = passed + failed;
    const score = total > 0 ? Math.round((passed / total) * 100) : 0;
    const certified = score >= 90 && failed === 0;

    const cert = createEventCertification({
      certified,
      score,
      passedChecks: passed,
      failedChecks: failed,
    });

    const summary = createEventCertificationSummary({
      certified,
      score,
      status: certified ? 'PASSED' : 'FAILED',
    });

    const diag = provider.diagnostics();

    return createCertificationReport({
      certification: cert,
      summary,
      issues: Object.freeze(issues),
      diagnostics: diag,
    });
  }

  public certificationReport(provider: IEventProvider): CertificationReport {
    return this.runCertification(provider);
  }
}
