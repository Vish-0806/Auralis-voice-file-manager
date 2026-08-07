/**
 * Command Certifier Engine Implementation (Phase 16.6.7).
 *
 * Implements ICommandCertifier certifying the entire Frontend Command Runtime,
 * executing end-to-end subsystem verification stages (Lifecycle, Registry, Execution,
 * Pipeline, Validator, Permissions, Policy, Scheduler, Queue, Background task,
 * Diagnostics consistency, and Performance Benchmarks), scoring the system,
 * collecting certification statistics, and producing immutable certification reports.
 */

import {
  CertificationCheck,
  CertificationDiagnostics,
  CertificationHealth,
  CertificationIssue,
  CertificationReport,
  CertificationStage,
  CertificationStatistics,
  CommandCertification,
  CommandExecutionRequest,
  CommandExecutionStatus,
  createCertificationCheck,
  createCertificationHealth,
  createCertificationIssue,
  createCertificationReport,
  createCertificationStage,
  createCertificationStatistics,
  createCommandCertification,
  createCommandCertificationSummary,
  createCertificationDiagnostics,
  createPolicyDecision,
} from './models';
import { ICommandCertifier, ICommandProvider } from './interfaces';

export class CommandCertifier implements ICommandCertifier {
  private _totalCertifications = 0;
  private _passedCertifications = 0;
  private _failedCertifications = 0;
  private readonly _scores: number[] = [];
  private _lastReport: CertificationReport | null = null;
  private _stageResults: CertificationStage[] = [];

  public async certify(provider: ICommandProvider): Promise<CommandCertification> {
    const report = await this.runCertification(provider);
    return report.certification;
  }

  public async runCertification(provider: ICommandProvider): Promise<CertificationReport> {
    this._totalCertifications++;
    const issues: CertificationIssue[] = [];
    const stages: CertificationStage[] = [];

    const now = new Date();
    const testId = `cert_${now.getTime()}_${Math.random().toString(36).substring(2, 7)}`;

    // Define verification stages
    // Stage 1: Lifecycle & Health Checks
    stages.push(this.verifyLifecycle(provider, issues));

    // Stage 2: Registry Operations Checks
    stages.push(this.verifyRegistry(provider, issues, testId));

    // Stage 3: Execution Engine Verification
    stages.push(await this.verifyExecution(provider, issues, testId));

    // Stage 4: Pipeline Operations Verification
    stages.push(await this.verifyPipeline(provider, issues, testId));

    // Stage 5: Validation Engine Constraints
    stages.push(await this.verifyValidation(provider, issues, testId));

    // Stage 6: Permission Manager RBAC Rules
    stages.push(this.verifyPermissions(provider, issues, testId));

    // Stage 7: Policy Manager Constraints
    stages.push(await this.verifyPolicies(provider, issues, testId));

    // Stage 8: Scheduling Engine Check
    stages.push(await this.verifyScheduling(provider, issues));

    // Stage 9: Queue Engine Operations
    stages.push(await this.verifyQueue(provider, issues));

    // Stage 10: Background Task Lifecycles
    stages.push(await this.verifyBackground(provider, issues));

    // Stage 11: Diagnostics payload structure
    stages.push(this.verifyDiagnosticsPayload(provider, issues));

    // Stage 12: Performance Benchmarks
    stages.push(await this.verifyPerformanceBenchmarks(provider, issues, testId));

    // Analyze results
    const totalChecks = stages.reduce((acc, stage) => acc + stage.checks.length, 0);
    const failedChecks = stages.reduce(
      (acc, stage) => acc + stage.checks.filter((c) => c.status === 'FAILED').length,
      0
    );
    const passedChecks = totalChecks - failedChecks;

    const score = totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;
    const certified = score >= 90 && failedChecks === 0;

    if (certified) {
      this._passedCertifications++;
    } else {
      this._failedCertifications++;
    }
    this._scores.push(score);

    const certification = createCommandCertification({
      certified,
      score,
      passedChecks,
      failedChecks,
      certifiedAt: now.toISOString(),
    });

    const summary = createCommandCertificationSummary({
      certified,
      score,
      status: certified ? 'PASSED' : 'FAILED',
      certifiedAt: now.toISOString(),
    });

    const providerDiagnostics = provider.diagnostics();

    // Attach to updated diagnostics object
    const finalDiagnostics = {
      ...providerDiagnostics,
      certification,
      certificationSummary: summary,
      certificationStatistics: this.certificationStatistics(),
      certificationHealth: this.certificationHealth(),
    };

    const report = createCertificationReport({
      certification,
      summary,
      issues: Object.freeze(issues),
      diagnostics: finalDiagnostics,
      generatedAt: now.toISOString(),
    });

    this._lastReport = report;
    this._stageResults = stages;

    return report;
  }

  public async certificationReport(provider: ICommandProvider): Promise<CertificationReport> {
    if (this._lastReport) return this._lastReport;
    return this.runCertification(provider);
  }

  public certificationStatistics(): CertificationStatistics {
    const avgScore =
      this._scores.length > 0
        ? this._scores.reduce((a, b) => a + b, 0) / this._scores.length
        : 100;

    return createCertificationStatistics({
      totalCertifications: this._totalCertifications,
      passedCertifications: this._passedCertifications,
      failedCertifications: this._failedCertifications,
      averageScore: Math.round(avgScore * 100) / 100,
    });
  }

  public certificationHealth(): CertificationHealth {
    const stats = this.certificationStatistics();
    const healthy = stats.failedCertifications === 0;
    const score = this._scores.length > 0 ? this._scores[this._scores.length - 1] : 100;

    return createCertificationHealth({
      healthy,
      certified: healthy && score >= 90,
      score,
    });
  }

  public diagnostics(): CertificationDiagnostics {
    return createCertificationDiagnostics({
      lastReport: this._lastReport,
      statistics: this.certificationStatistics(),
      health: this.certificationHealth(),
      stageResults: this._stageResults,
    });
  }

  // --- Stage Implementation Helpers ---

  private verifyLifecycle(provider: ICommandProvider, issues: CertificationIssue[]): CertificationStage {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    try {
      const state = provider.state();
      const checkState = createCertificationCheck({
        name: 'Runtime lifecycle initial state is READY',
        status: state.initialized ? 'PASSED' : 'FAILED',
      });
      checks.push(checkState);
      if (!state.initialized) {
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'LIFECYCLE',
            message: `Lifecycle state initialized check failed: ${state.runtimeState}`,
          })
        );
      }
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Runtime lifecycle status', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'LIFECYCLE', message: e.message }));
    }

    try {
      const caps = provider.capabilities();
      const checkCaps = createCertificationCheck({
        name: 'Runtime capabilities contain essential command features',
        status: caps.supportsCommandExecution && caps.supportsCommandValidation ? 'PASSED' : 'FAILED',
      });
      checks.push(checkCaps);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Runtime capabilities validation', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'CAPABILITIES', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '1. Runtime Lifecycle & Operational Health',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private verifyRegistry(provider: ICommandProvider, issues: CertificationIssue[], testId: string): CertificationStage {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const cmdId = `cert_reg_cmd_${testId}`;
    try {
      provider.registerCommand({
        id: cmdId,
        displayName: 'Cert Registry Command',
        category: 'Certification',
        aliases: [`alias_${cmdId}`],
      });

      const found = provider.findCommand(cmdId);
      const byAlias = provider.findByAlias(`alias_${cmdId}`);

      const success = found !== undefined && byAlias !== undefined && found.id === cmdId;
      checks.push(
        createCertificationCheck({
          name: 'Registry supports command registration, aliases, and search lookup',
          status: success ? 'PASSED' : 'FAILED',
        })
      );
      if (!success) {
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'REGISTRY',
            message: 'Command registration lookup by ID or Alias failed.',
          })
        );
      }
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Registry operations', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'REGISTRY', message: e.message }));
    }

    // Clean up
    try {
      provider.removeCommand(cmdId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '2. Command Registry Operations',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyExecution(provider: ICommandProvider, issues: CertificationIssue[], testId: string): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const cmdId = `cert_exec_cmd_${testId}`;
    try {
      provider.registerCommand({ id: cmdId, displayName: 'Cert Exec Command' });
      provider.registerHandler(cmdId, (args: any) => args.input ?? 'fallback');

      // Sync Execution
      const resultSync = provider.execute({ commandId: cmdId, args: { input: 'sync' } });
      const syncOk = resultSync.status === CommandExecutionStatus.COMPLETED && resultSync.value === 'sync';
      checks.push(createCertificationCheck({ name: 'Synchronous command execution engine', status: syncOk ? 'PASSED' : 'FAILED' }));

      // Async Execution
      const resultAsync = await provider.executeAsync({ commandId: cmdId, args: { input: 'async' } });
      const asyncOk = resultAsync.status === CommandExecutionStatus.COMPLETED && resultAsync.value === 'async';
      checks.push(createCertificationCheck({ name: 'Asynchronous promise execution engine', status: asyncOk ? 'PASSED' : 'FAILED' }));

      if (!syncOk || !asyncOk) {
        issues.push(
          createCertificationIssue({
            severity: 'CRITICAL',
            category: 'EXECUTION',
            message: 'Execution returned unexpected result or status.',
          })
        );
      }
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Execution engine checks', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'EXECUTION', message: e.message }));
    }

    try {
      provider.removeCommand(cmdId);
      provider.unregisterHandler(cmdId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '3. Command Execution Engine',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyPipeline(provider: ICommandProvider, issues: CertificationIssue[], testId: string): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const cmdId = `cert_pipe_cmd_${testId}`;
    try {
      provider.registerCommand({ id: cmdId, displayName: 'Cert Pipe Command' });
      provider.registerHandler(cmdId, () => 'pipeline_result');

      let mwExec = false;
      const mw = provider.registerMiddleware({
        name: `cert_mw_${testId}`,
        execute: () => {
          mwExec = true;
        },
      });

      let intExec = false;
      const interceptor = provider.registerInterceptor({
        name: `cert_int_${testId}`,
        intercept: async (_ctx, next) => {
          intExec = true;
          return next();
        },
      });

      const res = await provider.executePipeline({ commandId: cmdId });
      const completed =
        res.executionResult.status === CommandExecutionStatus.COMPLETED &&
        res.executionResult.value === 'pipeline_result';

      checks.push(
        createCertificationCheck({
          name: 'Command Pipeline supports middleware hooks & interceptor chain',
          status: completed && mwExec && intExec ? 'PASSED' : 'FAILED',
        })
      );

      // Clean up
      provider.removeMiddleware(mw.middlewareId);
      provider.removeInterceptor(interceptor.interceptorId);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Pipeline execution chain', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'PIPELINE', message: e.message }));
    }

    try {
      provider.removeCommand(cmdId);
      provider.unregisterHandler(cmdId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '4. Pipeline & Middleware Engine',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyValidation(provider: ICommandProvider, issues: CertificationIssue[], testId: string): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const cmdId = `cert_val_cmd_${testId}`;
    try {
      provider.registerCommand({
        id: cmdId,
        displayName: 'Cert Val Command',
        parameters: [
          { name: 'req_param', required: true, type: 'string' },
        ],
      });

      // Missing required parameter validation
      const missingReport = await provider.validate({ commandId: cmdId, args: {} });
      checks.push(
        createCertificationCheck({
          name: 'Validator enforces missing required parameter constraints',
          status: !missingReport.valid && missingReport.issues.length > 0 ? 'PASSED' : 'FAILED',
        })
      );

      // Custom rule validation
      const rule = provider.registerValidationRule({
        name: `cert_rule_${testId}`,
        validate: async (req) => {
          if (req.args?.req_param === 'invalid_val') {
            return {
              severity: 'error',
              code: 'CUSTOM_ERR',
              message: 'Value is invalid.',
            };
          }
          return null;
        },
      });

      const badValReport = await provider.validate({ commandId: cmdId, args: { req_param: 'invalid_val' } });
      checks.push(
        createCertificationCheck({
          name: 'Validator enforces registered custom validation rules',
          status: !badValReport.valid && badValReport.issues.some((i) => i.code === 'CUSTOM_ERR') ? 'PASSED' : 'FAILED',
        })
      );

      provider.removeValidationRule(rule.ruleId);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Validator rules checks', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'VALIDATOR', message: e.message }));
    }

    try {
      provider.removeCommand(cmdId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '5. Validation Engine',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private verifyPermissions(provider: ICommandProvider, issues: CertificationIssue[], testId: string): CertificationStage {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const permId = `cert_perm_${testId}`;
    try {
      provider.registerPermission({ name: permId, description: 'Cert Permission' });
      provider.grantPermission('user_cert', permId);

      const checkGrant = provider.hasPermission('user_cert', permId);
      checks.push(
        createCertificationCheck({
          name: 'Permission manager grants permissions to subjects',
          status: checkGrant.granted ? 'PASSED' : 'FAILED',
        })
      );

      provider.revokePermission('user_cert', permId);
      const checkRevoke = provider.hasPermission('user_cert', permId);
      checks.push(
        createCertificationCheck({
          name: 'Permission manager revokes permissions from subjects',
          status: !checkRevoke.granted ? 'PASSED' : 'FAILED',
        })
      );
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Permissions checks', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'PERMISSIONS', message: e.message }));
    }

    try {
      provider.removePermission(permId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '6. Permission Manager',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyPolicies(provider: ICommandProvider, issues: CertificationIssue[], testId: string): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const policyId = `cert_policy_${testId}`;
    try {
      const policy = provider.registerPolicy({
        name: policyId,
        evaluate: async (req) => {
          if (req.args?.forbidden) {
            return createPolicyDecision({ allowed: false, reason: 'Forbidden arg.' });
          }
          return createPolicyDecision({ allowed: true });
        },
      });

      const allowedDecision = await provider.evaluatePolicy({ commandId: 'c', args: {} });
      const deniedDecision = await provider.evaluatePolicy({ commandId: 'c', args: { forbidden: true } });

      const passed = allowedDecision.allowed && !deniedDecision.allowed;
      checks.push(
        createCertificationCheck({
          name: 'Policy Manager registers and evaluates custom security predicates',
          status: passed ? 'PASSED' : 'FAILED',
        })
      );

      provider.removePolicy(policy.policyId);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Policy evaluation checks', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'POLICIES', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '7. Policy Manager',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyScheduling(provider: ICommandProvider, issues: CertificationIssue[]): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    try {
      const req: CommandExecutionRequest = { commandId: 'test_cmd', args: { val: 'sched' } };

      // Delayed Schedule
      const s = await provider.scheduleDelayed(req, 5000);
      const isPending = s.scheduleId !== undefined && s.status === 'pending';
      checks.push(
        createCertificationCheck({
          name: 'Command Scheduler supports delayed schedule registration',
          status: isPending ? 'PASSED' : 'FAILED',
        })
      );

      // Clean up
      provider.cancelScheduled(s.scheduleId);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Scheduling operations', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'SCHEDULER', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '8. Scheduling Engine',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyQueue(provider: ICommandProvider, issues: CertificationIssue[]): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    try {
      const req1: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 1 } };
      const req2: CommandExecutionRequest = { commandId: 'test_cmd', args: { id: 2 } };

      const sizeBefore = provider.queueSize();
      await provider.queue(req1, 5);
      await provider.queue(req2, 10);

      const sizeAfter = provider.queueSize();
      checks.push(
        createCertificationCheck({
          name: 'Command Queue manages capacity size and enqueues tasks',
          status: sizeAfter === sizeBefore + 2 ? 'PASSED' : 'FAILED',
        })
      );

      // Dequeue priority ordering check
      const first = await provider.dequeue();
      const priorityOk = first?.priority === 10;
      checks.push(
        createCertificationCheck({
          name: 'Command Queue processes tasks in descending priority order',
          status: priorityOk ? 'PASSED' : 'FAILED',
        })
      );

      await provider.dequeue(); // Empty second item
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Queue operations', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'QUEUE', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '9. Queue Engine',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyBackground(provider: ICommandProvider, issues: CertificationIssue[]): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    try {
      const req: CommandExecutionRequest = { commandId: 'test_cmd' };
      const t = await provider.submitBackgroundTask(req);

      checks.push(
        createCertificationCheck({
          name: 'Background Execution Manager submits tasks asynchronously',
          status: t.taskId !== undefined && t.status === 'pending' ? 'PASSED' : 'FAILED',
        })
      );

      provider.cancelBackgroundTask(t.taskId);
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Background manager operations', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'BACKGROUND', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '10. Background Execution',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private verifyDiagnosticsPayload(provider: ICommandProvider, issues: CertificationIssue[]): CertificationStage {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    try {
      const diag = provider.diagnostics();
      const ok =
        diag.health !== undefined &&
        diag.statistics !== undefined &&
        diag.capabilities !== undefined &&
        diag.registryStatistics !== undefined &&
        diag.schedulingDiagnostics !== undefined &&
        diag.queueDiagnostics !== undefined &&
        diag.backgroundDiagnostics !== undefined;

      checks.push(
        createCertificationCheck({
          name: 'Runtime aggregates diagnostics and sub-engine telemetry snapshots',
          status: ok ? 'PASSED' : 'FAILED',
        })
      );

      if (!ok) {
        issues.push(
          createCertificationIssue({
            severity: 'WARNING',
            category: 'DIAGNOSTICS',
            message: 'Provider diagnostics returned incomplete sub-engine snapshots.',
          })
        );
      }
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Diagnostics validation', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'DIAGNOSTICS', message: e.message }));
    }

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '11. Diagnostics & Telemetry',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }

  private async verifyPerformanceBenchmarks(provider: ICommandProvider, issues: CertificationIssue[], testId: string): Promise<CertificationStage> {
    const start = performance ? performance.now() : Date.now();
    const checks: CertificationCheck[] = [];

    const cmdId = `cert_perf_cmd_${testId}`;
    try {
      provider.registerCommand({
        id: cmdId,
        displayName: 'Cert Perf Command',
        parameters: [{ name: 'val', required: true, type: 'string' }],
      });
      provider.registerHandler(cmdId, () => 'ok');

      // 1. Registry lookup benchmark (< 5ms)
      const lookupStart = performance ? performance.now() : Date.now();
      for (let i = 0; i < 100; i++) {
        provider.findCommand(cmdId);
      }
      const lookupEnd = performance ? performance.now() : Date.now();
      const avgLookup = (lookupEnd - lookupStart) / 100;
      checks.push(
        createCertificationCheck({
          name: `Registry lookup latency benchmark (avg: ${avgLookup.toFixed(3)}ms, limit: 5ms)`,
          status: avgLookup < 5 ? 'PASSED' : 'FAILED',
        })
      );

      // 2. Validation latency benchmark (< 10ms)
      const valStart = performance ? performance.now() : Date.now();
      for (let i = 0; i < 50; i++) {
        await provider.validate({ commandId: cmdId, args: { val: 'test' } });
      }
      const valEnd = performance ? performance.now() : Date.now();
      const avgVal = (valEnd - valStart) / 50;
      checks.push(
        createCertificationCheck({
          name: `Validation latency benchmark (avg: ${avgVal.toFixed(3)}ms, limit: 10ms)`,
          status: avgVal < 10 ? 'PASSED' : 'FAILED',
        })
      );

      // 3. Pipeline execution latency benchmark (< 25ms)
      const pipeStart = performance ? performance.now() : Date.now();
      for (let i = 0; i < 20; i++) {
        await provider.executePipeline({ commandId: cmdId, args: { val: 'test' } });
      }
      const pipeEnd = performance ? performance.now() : Date.now();
      const avgPipe = (pipeEnd - pipeStart) / 20;
      checks.push(
        createCertificationCheck({
          name: `Pipeline execution latency benchmark (avg: ${avgPipe.toFixed(3)}ms, limit: 25ms)`,
          status: avgPipe < 25 ? 'PASSED' : 'FAILED',
        })
      );
    } catch (e: any) {
      checks.push(createCertificationCheck({ name: 'Performance latency checks', status: 'FAILED', error: e.message }));
      issues.push(createCertificationIssue({ severity: 'CRITICAL', category: 'PERFORMANCE', message: e.message }));
    }

    try {
      provider.removeCommand(cmdId);
      provider.unregisterHandler(cmdId);
    } catch {}

    const end = performance ? performance.now() : Date.now();
    return createCertificationStage({
      name: '12. Performance Latency Benchmarks',
      status: checks.some((c) => c.status === 'FAILED') ? 'FAILED' : 'PASSED',
      durationMs: Math.round((end - start) * 100) / 100,
      checks,
    });
  }
}
