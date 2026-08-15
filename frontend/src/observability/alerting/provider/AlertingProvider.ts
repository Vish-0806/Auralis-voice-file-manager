import type { IAlertingProvider } from '../interfaces/alerting-provider';
import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import { AlertingRuntimeState, AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertEvaluationContext, RuleEvaluationResult } from '../models/evaluation';
import { AlertRegistry } from '../registry/AlertRegistry';
import { AlertEvaluator } from '../evaluator/AlertEvaluator';
import { AlertGenerator } from '../generator/AlertGenerator';
import { AlertingStateError, AlertGenerationError } from '../errors/AlertingErrors';
import { createAlertingStatistics, createAlertingDiagnostics } from '../factories/alertingFactories';

export class AlertingProvider implements IAlertingProvider {
  private _state: AlertingRuntimeStateValue = AlertingRuntimeState.UNINITIALIZED;
  private readonly _registry = new AlertRegistry();
  private readonly _evaluator = new AlertEvaluator();
  private readonly _generator = new AlertGenerator();

  // Evaluation counters
  private _totalEvaluations = 0;
  private _matchedEvaluations = 0;
  private _unmatchedEvaluations = 0;
  private _errorEvaluations = 0;
  private _skippedEvaluations = 0;
  private _totalEvaluationDuration = 0;

  // Generation counters
  private _totalAlertGenerations = 0;
  private _successfulAlertGenerations = 0;
  private _rejectedAlertGenerations = 0;
  private _generationErrors = 0;
  private _totalGenerationDuration = 0;

  private ensureReady(action: string): void {
    if (this._state !== AlertingRuntimeState.READY) {
      throw new AlertingStateError(`Cannot perform action '${action}' when state is ${this._state}. Provider must be READY.`);
    }
  }

  public async initialize(): Promise<void> {
    if (this._state === AlertingRuntimeState.READY) {
      return; // idempotent
    }
    if (this._state === AlertingRuntimeState.INITIALIZING || this._state === AlertingRuntimeState.STOPPING || this._state === AlertingRuntimeState.STOPPED) {
      throw new AlertingStateError(`Cannot initialize alerting provider from state: ${this._state}`);
    }

    this._state = AlertingRuntimeState.INITIALIZING;
    try {
      this._state = AlertingRuntimeState.READY;
    } catch (err: any) {
      this._state = AlertingRuntimeState.ERROR;
      throw err;
    }
  }

  public async shutdown(): Promise<void> {
    if (this._state === AlertingRuntimeState.STOPPED) {
      return; // idempotent
    }
    if (this._state === AlertingRuntimeState.UNINITIALIZED) {
      throw new AlertingStateError('Cannot shutdown alerting provider: it is not initialized.');
    }

    this._state = AlertingRuntimeState.STOPPING;
    try {
      this._registry.clear();
      this._registry.clearRules();
      this.clearEvaluationStats();
      this.clearGenerationStats();
    } finally {
      this._state = AlertingRuntimeState.STOPPED;
    }
  }

  public getRuntimeState(): AlertingRuntimeStateValue {
    return this._state;
  }

  public getState(): AlertingRuntimeStateValue {
    return this._state;
  }

  // --- Alert API ---
  public registerAlert(alert: AlertRecord): void {
    this.ensureReady('registerAlert');
    this._registry.registerAlert(alert);
  }

  public getAlert(alertId: string): AlertRecord | null {
    this.ensureReady('getAlert');
    return this._registry.getAlert(alertId);
  }

  public hasAlert(alertId: string): boolean {
    this.ensureReady('hasAlert');
    return this._registry.hasAlert(alertId);
  }

  public removeAlert(alertId: string): void {
    this.ensureReady('removeAlert');
    return this._registry.removeAlert(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    this.ensureReady('listAlerts');
    return this._registry.listAlerts();
  }

  public clearAlerts(): void {
    this.ensureReady('clearAlerts');
    this._registry.clear();
  }

  // --- Rule API ---
  public registerRule(rule: AlertRule): void {
    this.ensureReady('registerRule');
    this._registry.registerRule(rule);
  }

  public unregisterRule(ruleId: string): void {
    this.ensureReady('unregisterRule');
    this._registry.unregisterRule(ruleId);
  }

  public getRule(ruleId: string): AlertRule | null {
    this.ensureReady('getRule');
    return this._registry.getRule(ruleId);
  }

  public hasRule(ruleId: string): boolean {
    this.ensureReady('hasRule');
    return this._registry.hasRule(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    this.ensureReady('listRules');
    return this._registry.listRules();
  }

  public updateRule(rule: AlertRule): void {
    this.ensureReady('updateRule');
    this._registry.updateRule(rule);
  }

  public clearRules(): void {
    this.ensureReady('clearRules');
    this._registry.clearRules();
  }

  // --- Evaluation API ---
  public evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult {
    this.ensureReady('evaluateRule');
    const result = this._evaluator.evaluateRule(rule, context);

    // Track stats
    this._totalEvaluations++;
    this._totalEvaluationDuration += result.durationMs;

    if (result.status === 'SKIPPED') {
      this._skippedEvaluations++;
    } else if (result.status === 'ERROR') {
      this._errorEvaluations++;
    } else if (result.status === 'MATCHED') {
      this._matchedEvaluations++;
    } else if (result.status === 'NOT_MATCHED') {
      this._unmatchedEvaluations++;
    }

    return result;
  }

  // --- Generation API ---
  public generateAlert(rule: AlertRule, evaluationResult: RuleEvaluationResult): AlertRecord {
    this.ensureReady('generateAlert');
    const startTime = performance.now();
    this._totalAlertGenerations++;

    try {
      const alert = this._generator.generate(rule, evaluationResult);

      // Store in registry
      this._registry.registerAlert(alert);

      this._successfulAlertGenerations++;
      const duration = performance.now() - startTime;
      this._totalGenerationDuration += duration;
      return alert;
    } catch (err: any) {
      const duration = performance.now() - startTime;
      this._totalGenerationDuration += duration;

      if (err instanceof AlertGenerationError) {
        this._rejectedAlertGenerations++;
      } else {
        this._generationErrors++;
      }
      throw err;
    }
  }

  private clearEvaluationStats(): void {
    this._totalEvaluations = 0;
    this._matchedEvaluations = 0;
    this._unmatchedEvaluations = 0;
    this._errorEvaluations = 0;
    this._skippedEvaluations = 0;
    this._totalEvaluationDuration = 0;
  }

  private clearGenerationStats(): void {
    this._totalAlertGenerations = 0;
    this._successfulAlertGenerations = 0;
    this._rejectedAlertGenerations = 0;
    this._generationErrors = 0;
    this._totalGenerationDuration = 0;
  }

  // --- Statistics & Diagnostics ---
  public getStatistics(): AlertingStatistics {
    this.ensureReady('getStatistics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;
    const averageEvaluationDuration = this._totalEvaluations > 0 ? this._totalEvaluationDuration / this._totalEvaluations : 0;
    const averageGenerationDuration = this._totalAlertGenerations > 0 ? this._totalGenerationDuration / this._totalAlertGenerations : 0;

    return createAlertingStatistics({
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount,
      totalEvaluations: this._totalEvaluations,
      matchedEvaluations: this._matchedEvaluations,
      unmatchedEvaluations: this._unmatchedEvaluations,
      errorEvaluations: this._errorEvaluations,
      skippedEvaluations: this._skippedEvaluations,
      totalEvaluationDuration: this._totalEvaluationDuration,
      averageEvaluationDuration,
      totalAlertGenerations: this._totalAlertGenerations,
      successfulAlertGenerations: this._successfulAlertGenerations,
      rejectedAlertGenerations: this._rejectedAlertGenerations,
      generationErrors: this._generationErrors,
      totalGenerationDuration: this._totalGenerationDuration,
      averageGenerationDuration
    });
  }

  public getDiagnostics(): AlertingDiagnostics {
    this.ensureReady('getDiagnostics');
    const alertCount = this._registry.listAlerts().length;
    const rules = this._registry.listRules();
    const ruleCount = rules.length;
    const enabledRuleCount = rules.filter(r => r.enabled).length;
    const disabledRuleCount = ruleCount - enabledRuleCount;
    const averageEvaluationDuration = this._totalEvaluations > 0 ? this._totalEvaluationDuration / this._totalEvaluations : 0;
    const averageGenerationDuration = this._totalAlertGenerations > 0 ? this._totalGenerationDuration / this._totalAlertGenerations : 0;

    return createAlertingDiagnostics({
      runtimeState: this._state,
      registeredAlertCount: alertCount,
      registeredRuleCount: ruleCount,
      enabledRuleCount,
      disabledRuleCount,
      totalEvaluations: this._totalEvaluations,
      matchedEvaluations: this._matchedEvaluations,
      unmatchedEvaluations: this._unmatchedEvaluations,
      errorEvaluations: this._errorEvaluations,
      skippedEvaluations: this._skippedEvaluations,
      totalEvaluationDuration: this._totalEvaluationDuration,
      averageEvaluationDuration,
      totalAlertGenerations: this._totalAlertGenerations,
      successfulAlertGenerations: this._successfulAlertGenerations,
      rejectedAlertGenerations: this._rejectedAlertGenerations,
      generationErrors: this._generationErrors,
      totalGenerationDuration: this._totalGenerationDuration,
      averageGenerationDuration,
      generatedAt: Date.now()
    });
  }
}
