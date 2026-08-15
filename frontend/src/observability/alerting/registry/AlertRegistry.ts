import { AlertRecord } from '../models/alert';
import { AlertRule } from '../models/alert-rule';
import {
  AlertValidationError,
  AlertNotFoundError,
  AlertRuleAlreadyExistsError,
  AlertRuleNotFoundError,
  AlertRuleValidationError
} from '../errors/AlertingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class AlertRegistry {
  private readonly _alerts = new Map<string, AlertRecord>();
  private readonly _order: string[] = [];

  private readonly _rules = new Map<string, AlertRule>();
  private readonly _ruleOrder: string[] = [];

  // --- Alert Operations ---
  public registerAlert(alert: AlertRecord): void {
    if (!alert || !alert.id) {
      throw new AlertValidationError('Invalid alert: alert ID is required.');
    }
    if (this._alerts.has(alert.id)) {
      throw new AlertValidationError(`Alert with ID '${alert.id}' is already registered.`);
    }

    this._alerts.set(alert.id, freezeDeepSafe(alert));
    this._order.push(alert.id);
  }

  public getAlert(alertId: string): AlertRecord | null {
    if (!alertId) {
      throw new AlertValidationError('Alert ID is required.');
    }
    const alert = this._alerts.get(alertId);
    return alert ? freezeDeepSafe(alert) : null;
  }

  public hasAlert(alertId: string): boolean {
    if (!alertId) {
      return false;
    }
    return this._alerts.has(alertId);
  }

  public removeAlert(alertId: string): void {
    if (!alertId) {
      throw new AlertValidationError('Alert ID is required.');
    }
    if (!this._alerts.has(alertId)) {
      throw new AlertNotFoundError(`Alert with ID '${alertId}' not found.`, alertId);
    }
    this._alerts.delete(alertId);
    const index = this._order.indexOf(alertId);
    if (index !== -1) {
      this._order.splice(index, 1);
    }
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    const list = this._order.map((id) => this._alerts.get(id)!);
    return freezeDeepSafe(list);
  }

  public clear(): void {
    this._alerts.clear();
    this._order.length = 0;
  }

  // --- Rule Operations ---
  public registerRule(rule: AlertRule): void {
    if (!rule || !rule.id) {
      throw new AlertRuleValidationError('Invalid rule: rule ID is required.');
    }
    if (this._rules.has(rule.id)) {
      throw new AlertRuleAlreadyExistsError(`Alert rule with ID '${rule.id}' is already registered.`);
    }

    this._rules.set(rule.id, freezeDeepSafe(rule));
    this._ruleOrder.push(rule.id);
  }

  public unregisterRule(ruleId: string): void {
    if (!ruleId) {
      throw new AlertRuleValidationError('Rule ID is required.');
    }
    if (!this._rules.has(ruleId)) {
      throw new AlertRuleNotFoundError(`Alert rule with ID '${ruleId}' not found.`, ruleId);
    }
    this._rules.delete(ruleId);
    const index = this._ruleOrder.indexOf(ruleId);
    if (index !== -1) {
      this._ruleOrder.splice(index, 1);
    }
  }

  public getRule(ruleId: string): AlertRule | null {
    if (!ruleId) {
      throw new AlertRuleValidationError('Rule ID is required.');
    }
    const rule = this._rules.get(ruleId);
    return rule ? freezeDeepSafe(rule) : null;
  }

  public hasRule(ruleId: string): boolean {
    if (!ruleId) {
      return false;
    }
    return this._rules.has(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    const list = this._ruleOrder.map((id) => this._rules.get(id)!);
    return freezeDeepSafe(list);
  }

  public updateRule(rule: AlertRule): void {
    if (!rule || !rule.id) {
      throw new AlertRuleValidationError('Invalid rule: rule ID is required.');
    }
    if (!this._rules.has(rule.id)) {
      throw new AlertRuleNotFoundError(`Alert rule with ID '${rule.id}' not found.`, rule.id);
    }
    this._rules.set(rule.id, freezeDeepSafe(rule));
  }

  public clearRules(): void {
    this._rules.clear();
    this._ruleOrder.length = 0;
  }
}
