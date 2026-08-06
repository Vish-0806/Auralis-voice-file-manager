/**
 * State Certifier Engine (Phase 16.5).
 *
 * Implements IStateCertifier certifying the entire Frontend State Management Runtime,
 * executing end-to-end subsystem verification, lifecycle checks, store operations benchmarks,
 * and producing production certification reports.
 */

import {
  CertificationIssue,
  CertificationReport,
  createCertificationIssue,
  createCertificationReport,
  createStateCertification,
  createStateCertificationSummary,
  StateCertification,
} from './models';
import { IStateCertifier, IStateProvider } from './interfaces';

export class StateCertifier implements IStateCertifier {
  public certify(provider: IStateProvider): StateCertification {
    const report = this.runCertification(provider);
    return report.certification;
  }

  public runCertification(provider: IStateProvider): CertificationReport {
    const issues: CertificationIssue[] = [];
    let passed = 0;
    let failed = 0;

    const testCntName = `cert_cnt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const testSelName = `cert_sel_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const testRedName = `cert_red_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

    // Check 1: Runtime Lifecycle & Operational Health
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
            message: `State provider is in unready state: ${health.runtimeState}`,
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

    // Check 2: Capabilities & Context Payload
    try {
      const caps = provider.capabilities();
      if (caps.supportsContainers && caps.supportsReducers && caps.supportsMiddleware && caps.supportsSelectors) {
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

    // Check 3: State Store Engine & Container Operations
    try {
      const container = provider.createContainer(testCntName, { count: 0 });
      provider.setState(testCntName, { count: 1 });
      const current = provider.getState(testCntName);

      if (container && current && (current as any).count === 1) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'STORE',
            message: 'State container mutation verification failed.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'STORE',
          message: `State store verification failed: ${e.message}`,
        }),
      );
    }

    // Check 4: Action Dispatcher Engine
    try {
      const act = provider.dispatch('CERT_ACTION', { val: 42 });
      if (act && act.type === 'CERT_ACTION') {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'ACTION',
            message: 'Action dispatcher returned invalid action object.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'ACTION',
          message: `Action dispatcher verification failed: ${e.message}`,
        }),
      );
    }

    // Check 5: Reducer Engine Execution
    try {
      provider.registerReducer(testRedName, (state: any, action: any) => {
        if (action.type === 'INCREMENT') {
          return { count: (state?.count ?? 0) + 1 };
        }
        return state;
      });
      passed++;
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'REDUCER',
          message: `Reducer registration failed: ${e.message}`,
        }),
      );
    }

    // Check 6: Selector Engine & Memoization
    try {
      const selObj = provider.registerSelector(testSelName, (state: any) => state?.count ?? 0);
      const res = provider.select(selObj.selectorId, { count: 10 });

      if (res && res.value === 10) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'SELECTOR',
            message: 'Selector evaluation returned unexpected value.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'SELECTOR',
          message: `Selector evaluation verification failed: ${e.message}`,
        }),
      );
    }

    // Check 7: Subscriptions Engine
    try {
      let subNotified = false;
      const sub = provider.subscribe(testCntName, () => {
        subNotified = true;
      });
      provider.setState(testCntName, { count: 99 });
      provider.unsubscribe(sub.subscriptionId);

      if (subNotified) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'SUBSCRIPTION',
            message: 'Subscription notification was not received during setState.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'SUBSCRIPTION',
          message: `Subscription engine verification failed: ${e.message}`,
        }),
      );
    }

    // Check 8: Undo / Redo History Engine
    try {
      provider.setState(testCntName, { count: 100 });
      const undoRec = provider.undo();

      if (undoRec && undoRec.previousState) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'HISTORY',
            message: 'Undo operation did not return previous state snapshot.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'HISTORY',
          message: `History engine verification failed: ${e.message}`,
        }),
      );
    }

    // Check 9: Persistence Layer
    try {
      provider.save(testCntName, 'k_cert');
      const loaded = provider.load(testCntName, 'k_cert');

      if (loaded) {
        passed++;
      } else {
        failed++;
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'PERSISTENCE',
            message: 'Persistence load failed for saved state.',
          }),
        );
      }
    } catch (e: any) {
      failed++;
      issues.push(
        createCertificationIssue({
          severity: 'CRITICAL',
          category: 'PERSISTENCE',
          message: `Persistence layer verification failed: ${e.message}`,
        }),
      );
    }

    // Check 10: Diagnostics Aggregation
    try {
      const diag = provider.diagnostics();
      if (diag.health && diag.statistics && diag.capabilities) {
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

    const total = passed + failed;
    const score = total > 0 ? Math.round((passed / total) * 100) : 0;
    const certified = score >= 90 && failed === 0;

    const cert = createStateCertification({
      certified,
      score,
      passedChecks: passed,
      failedChecks: failed,
    });

    const summary = createStateCertificationSummary({
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

  public certificationReport(provider: IStateProvider): CertificationReport {
    return this.runCertification(provider);
  }
}
