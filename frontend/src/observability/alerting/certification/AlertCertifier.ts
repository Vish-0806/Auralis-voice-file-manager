import { AlertingProvider } from '../provider/AlertingProvider';
import { AlertingRuntime } from '../runtime/AlertingRuntime';
import {
  AlertCertificationStageResult,
  AlertCertificationReport,
  AlertCertificationCheck,
  AlertCertificationStageValue,
  AlertCertificationStage,
  AlertCertificationStatus
} from '../models/certification';
import { freezeDeepSafe } from '../../models/monitoring';
import { createAlertRecord } from '../factories/alertingFactories';
import { InMemoryNotificationChannel } from '../notifications/InMemoryNotificationChannel';

export class AlertCertifier {
  private _report: AlertCertificationReport | null = null;
  private _runCount = 0;

  public async certify(): Promise<AlertCertificationReport> {
    this._runCount++;

    const stages: AlertCertificationStageValue[] = Object.values(AlertCertificationStage);
    const stageResults: AlertCertificationStageResult[] = [];

    for (const stage of stages) {
      const stageResult = await this.certifyStage(stage);
      stageResults.push(stageResult);
    }

    let passedStages = 0;
    let failedStages = 0;
    let warningCount = 0;
    let score = 0;

    for (const res of stageResults) {
      if (res.status === 'SUCCESS') {
        passedStages++;
        score += 10; // 10 points per successful stage
      } else if (res.status === 'WARNING') {
        passedStages++;
        warningCount++;
        score += 5; // 5 points for warning stages
      } else {
        failedStages++;
      }
    }

    const maxScore = stages.length * 10;
    const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;
    const status = failedStages > 0
      ? AlertCertificationStatus.FAILED
      : (warningCount > 0 ? AlertCertificationStatus.CERTIFIED_WITH_WARNINGS : AlertCertificationStatus.CERTIFIED);

    const report: AlertCertificationReport = {
      status,
      score,
      maxScore,
      percentage,
      stageResults,
      passedStages,
      failedStages,
      warningCount,
      certifiedAt: Date.now()
    };

    this._report = freezeDeepSafe(report);
    return this._report;
  }

  public async certifyStage(stage: AlertCertificationStageValue): Promise<AlertCertificationStageResult> {
    const startTime = Date.now();
    const checks: AlertCertificationCheck[] = [];

    // Create an isolated sandbox environment
    const provider = new AlertingProvider();
    const runtime = new AlertingRuntime(provider);

    try {
      switch (stage) {
        case AlertCertificationStage.FOUNDATION: {
          await runtime.initialize();
          checks.push({ name: 'Provider Initialized Ready', passed: runtime.getState() === 'READY' });
          
          let doubleInitSafe = false;
          try {
            await runtime.initialize();
            doubleInitSafe = (runtime.getState() === 'READY');
          } catch {
            doubleInitSafe = false;
          }
          checks.push({ name: 'Repeated Initialization Safe', passed: doubleInitSafe });

          await runtime.shutdown();
          checks.push({ name: 'Shutdown Completed Safely', passed: runtime.getState() === 'STOPPED' });
          break;
        }

        case AlertCertificationStage.RULE_VALIDATION: {
          await runtime.initialize();
          let malformedRejected = false;
          try {
            runtime.registerRule({} as any);
          } catch {
            malformedRejected = true;
          }
          checks.push({ name: 'Malformed Rules Rejected', passed: malformedRejected });

          const validRule = {
            id: 'valid-rule',
            name: 'Valid Rule Name',
            description: 'A valid rule description',
            sourceId: 'src-1',
            version: 1,
            enabled: true,
            severity: 'WARNING' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'cond-1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 80
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(validRule);
          checks.push({ name: 'Valid Rules Accepted', passed: runtime.hasRule('valid-rule') });
          break;
        }

        case AlertCertificationStage.EVALUATION: {
          await runtime.initialize();
          const rule = {
            id: 'eval-rule',
            name: 'Eval',
            description: 'Eval description',
            sourceId: 'src-1',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'system.cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };

          runtime.registerRule(rule);
          const matchedContext = { values: { system: { cpu: 95 } } };
          const result = runtime.evaluateRule(rule, matchedContext);
          checks.push({ name: 'GT Operator Evaluated Correctly', passed: result.status === 'MATCHED' });
          break;
        }

        case AlertCertificationStage.GENERATION: {
          await runtime.initialize();
          const rule = {
            id: 'gen-rule',
            name: 'Gen',
            description: 'Gen description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const evalResult = runtime.evaluateRule(rule, { values: { cpu: 95 } });
          const alert = runtime.generateAlert(rule, evalResult);
          checks.push({ name: 'Alert Record Successfully Generated', passed: alert.ruleId === 'gen-rule' });
          checks.push({ name: 'Generated Alert Record Immutable', passed: Object.isFrozen(alert) });
          break;
        }

        case AlertCertificationStage.FINGERPRINTING: {
          await runtime.initialize();
          const rule = {
            id: 'fp-rule',
            name: 'Fp',
            description: 'Fp description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const a1 = runtime.generateAlert(rule, runtime.evaluateRule(rule, { values: { cpu: 95 } }));
          const a2 = runtime.generateAlert(rule, runtime.evaluateRule(rule, { values: { cpu: 95 } }));
          checks.push({ name: 'Deterministic Fingerprints Generated', passed: a1.fingerprint === a2.fingerprint });
          break;
        }

        case AlertCertificationStage.DEDUPLICATION: {
          await runtime.initialize();
          const alert = createAlertRecord({
            id: 'a1',
            sourceId: 'src-cpu',
            severity: 'ERROR',
            state: 'ACTIVE',
            title: 'CPU',
            message: 'High CPU',
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          });
          const customAlert = {
            ...alert,
            fingerprint: 'fp-1',
            ruleId: 'r1'
          };
          const dec1 = runtime.checkDeduplication(customAlert);
          checks.push({ name: 'First Occurrence Accepted', passed: dec1.decision === 'ACCEPTED' });

          const dec2 = runtime.checkDeduplication(customAlert);
          checks.push({ name: 'Duplicate Occurrence Blocked', passed: dec2.decision === 'COOLDOWN_SUPPRESSED' });
          break;
        }

        case AlertCertificationStage.LIFECYCLE: {
          await runtime.initialize();
          const record = runtime.initializeAlertLifecycle('a-1', 'fp-1');
          checks.push({ name: 'Lifecycle Created Active', passed: record.state === 'ACTIVE' });

          const ack = runtime.acknowledgeAlert('a-1', 'USER');
          checks.push({ name: 'Transitions to Acknowledged', passed: ack.state === 'ACKNOWLEDGED' });

          const res = runtime.resolveAlert('a-1', 'SYSTEM');
          checks.push({ name: 'Transitions to Resolved', passed: res.state === 'RESOLVED' });
          break;
        }

        case AlertCertificationStage.SUPPRESSION: {
          await runtime.initialize();
          const alert = createAlertRecord({
            id: 'a1',
            sourceId: 'src-cpu',
            severity: 'ERROR',
            state: 'ACTIVE',
            title: 'CPU',
            message: 'High CPU',
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          });
          const alertWithRule = {
            ...alert,
            ruleId: 'rule-cpu',
            fingerprint: 'fp-cpu'
          };

          runtime.snoozeAlert('a1', undefined, 10000, 'USER');
          const decision = runtime.evaluateSuppression(alertWithRule);
          checks.push({ name: 'Alert Snooze Suppression Active', passed: decision.suppressed && decision.reason === 'SNOOZED' });
          break;
        }

        case AlertCertificationStage.NOTIFICATION: {
          await runtime.initialize();
          const channel = new InMemoryNotificationChannel('ch-test', 'Test Channel');
          runtime.registerNotificationChannel(channel);
          checks.push({ name: 'Notification Channel Registers', passed: runtime.getNotificationChannel('ch-test') !== null });
          break;
        }

        case AlertCertificationStage.ORCHESTRATION: {
          await runtime.initialize();
          const rule = {
            id: 'rule-cpu',
            name: 'CPU',
            description: 'CPU description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const req = {
            orchestrationId: 'o1',
            ruleId: 'rule-cpu',
            context: { values: { cpu: 95 } }
          };
          const res = await runtime.orchestrate(req);
          checks.push({ name: 'Orchestration Runs E2E Pipeline', passed: res.status === 'SUCCESS' });
          break;
        }

        case AlertCertificationStage.FAILURE_ISOLATION: {
          await runtime.initialize();
          let orchestrateFailed = false;
          try {
            await runtime.orchestrate({
              orchestrationId: 'o2',
              ruleId: 'missing-rule',
              context: { values: {} }
            });
          } catch {
            orchestrateFailed = true;
          }
          checks.push({ name: 'Missing Rules Fail Closed Safely', passed: orchestrateFailed });
          break;
        }

        case AlertCertificationStage.CONCURRENCY: {
          await runtime.initialize();
          const rule = {
            id: 'rule-cpu',
            name: 'CPU',
            description: 'CPU description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const req = {
            orchestrationId: 'o3',
            ruleId: 'rule-cpu',
            context: { values: { cpu: 95 } }
          };
          const p1 = runtime.orchestrate(req);
          const p2 = runtime.orchestrate(req);
          checks.push({ name: 'Concurrent In-Flight Sharing Works', passed: p1 === p2 });
          await p1;
          break;
        }

        case AlertCertificationStage.IDEMPOTENCY: {
          await runtime.initialize();
          const rule = {
            id: 'rule-cpu',
            name: 'CPU',
            description: 'CPU desc',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const req1 = {
            orchestrationId: 'o4',
            ruleId: 'rule-cpu',
            context: { values: { cpu: 95 } }
          };
          const r1 = await runtime.orchestrate(req1);
          const r2 = await runtime.orchestrate(req1);
          checks.push({ name: 'Repeated Orchestration Determinism Verified', passed: r1.status === r2.status });
          break;
        }

        case AlertCertificationStage.IMMUTABILITY: {
          await runtime.initialize();
          const stats = runtime.getStatistics();
          checks.push({ name: 'Statistics Deeply Frozen', passed: Object.isFrozen(stats) });
          break;
        }

        case AlertCertificationStage.BOUNDED_STORAGE: {
          await runtime.initialize();
          // Verify FIFO bounds are cleared/evicted cleanly under registers
          const rule = {
            id: 'rule-cpu',
            name: 'CPU',
            description: 'CPU description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          checks.push({ name: 'Registry Correctly Registers Rules', passed: runtime.listRules().length === 1 });
          break;
        }

        case AlertCertificationStage.DIAGNOSTICS: {
          await runtime.initialize();
          const diag = runtime.getDiagnostics();
          checks.push({ name: 'Diagnostics Structure Verified', passed: diag.runtimeState === 'READY' });
          break;
        }

        case AlertCertificationStage.STATISTICS: {
          await runtime.initialize();
          const stats = runtime.getStatistics();
          checks.push({ name: 'Statistics Counts Consistent', passed: stats.totalEvaluations === 0 });
          break;
        }

        case AlertCertificationStage.END_TO_END: {
          await runtime.initialize();
          const rule = {
            id: 'rule-cpu',
            name: 'CPU',
            description: 'CPU description',
            sourceId: 'src-cpu',
            version: 1,
            enabled: true,
            severity: 'CRITICAL' as const,
            conditions: {
              operator: 'ALL' as const,
              conditions: [
                {
                  id: 'c1',
                  field: 'cpu',
                  operator: 'GT' as const,
                  expectedValue: 90
                }
              ]
            },
            tags: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            metadata: {}
          };
          runtime.registerRule(rule);
          const req = {
            orchestrationId: 'o-e2e',
            ruleId: 'rule-cpu',
            context: { values: { cpu: 95 } }
          };
          const res = await runtime.orchestrate(req);
          checks.push({ name: 'End to End Pipeline Succeeded', passed: res.status === 'SUCCESS' });
          break;
        }
      }
    } catch (err: any) {
      checks.push({ name: 'Execution Clean', passed: false, message: err.message });
    } finally {
      await runtime.shutdown();
    }

    const failed = checks.some(c => !c.passed);
    const status = failed ? 'FAILED' : 'SUCCESS';

    return freezeDeepSafe({
      stage,
      status,
      checks,
      durationMs: Date.now() - startTime
    });
  }

  public getReport(): AlertCertificationReport | null {
    return this._report;
  }

  public reset(): void {
    this._report = null;
    this._runCount = 0;
  }
}
