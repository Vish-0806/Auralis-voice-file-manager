import type { IAlertingRuntime } from '../interfaces/alerting-runtime';
import type { IAlertingProvider } from '../interfaces/alerting-provider';
import { AlertingProvider } from '../provider/AlertingProvider';
import type { AlertRecord } from '../models/alert';
import type { AlertRule } from '../models/alert-rule';
import type { AlertingStatistics, AlertingDiagnostics } from '../models/statistics';
import type { AlertingRuntimeStateValue } from '../models/runtime';
import type { AlertEvaluationContext, RuleEvaluationResult } from '../models/evaluation';

export class AlertingRuntime implements IAlertingRuntime {
  private readonly _provider: IAlertingProvider;

  constructor(provider?: IAlertingProvider) {
    this._provider = provider || new AlertingProvider();
  }

  public provider(): IAlertingProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getRuntimeState(): AlertingRuntimeStateValue {
    return this._provider.getRuntimeState();
  }

  public getState(): AlertingRuntimeStateValue {
    return this._provider.getState();
  }

  // --- Alert API ---
  public registerAlert(alert: AlertRecord): void {
    this._provider.registerAlert(alert);
  }

  public getAlert(alertId: string): AlertRecord | null {
    return this._provider.getAlert(alertId);
  }

  public hasAlert(alertId: string): boolean {
    return this._provider.hasAlert(alertId);
  }

  public removeAlert(alertId: string): void {
    this._provider.removeAlert(alertId);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    return this._provider.listAlerts();
  }

  public clearAlerts(): void {
    this._provider.clearAlerts();
  }

  // --- Rule API ---
  public registerRule(rule: AlertRule): void {
    this._provider.registerRule(rule);
  }

  public unregisterRule(ruleId: string): void {
    this._provider.unregisterRule(ruleId);
  }

  public getRule(ruleId: string): AlertRule | null {
    return this._provider.getRule(ruleId);
  }

  public hasRule(ruleId: string): boolean {
    return this._provider.hasRule(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    return this._provider.listRules();
  }

  public updateRule(rule: AlertRule): void {
    this._provider.updateRule(rule);
  }

  public clearRules(): void {
    this._provider.clearRules();
  }

  // --- Evaluation API ---
  public evaluateRule(rule: AlertRule, context: AlertEvaluationContext): RuleEvaluationResult {
    return this._provider.evaluateRule(rule, context);
  }

  // --- Generation API ---
  public generateAlert(rule: AlertRule, evaluationResult: RuleEvaluationResult): AlertRecord {
    return this._provider.generateAlert(rule, evaluationResult);
  }

  // --- Stats & Diags ---
  public getStatistics(): AlertingStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): AlertingDiagnostics {
    return this._provider.getDiagnostics();
  }
}
