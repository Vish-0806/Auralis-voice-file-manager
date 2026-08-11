import { AlertRule } from '../models/rule';
import { AlertRecord, AlertState } from '../models/alert';
import {
  AlertRuleAlreadyExistsError,
  AlertRuleNotFoundError,
  AlertError,
  AlertNotFoundError
} from '../errors/AlertingErrors';

export class AlertRegistry {
  private readonly rules = new Map<string, AlertRule>();
  private readonly ruleIds: string[] = [];

  private readonly alerts = new Map<string, AlertRecord>();
  private readonly alertIds: string[] = [];
  private readonly activeAlertsByFingerprint = new Map<string, AlertRecord>();

  public registerRule(rule: AlertRule): void {
    if (this.rules.has(rule.id)) {
      throw new AlertRuleAlreadyExistsError(`Alert rule with ID '${rule.id}' is already registered.`);
    }
    this.rules.set(rule.id, rule);
    this.ruleIds.push(rule.id);
  }

  public unregisterRule(ruleId: string): void {
    if (!this.rules.has(ruleId)) {
      throw new AlertRuleNotFoundError(`Alert rule with ID '${ruleId}' not found.`);
    }
    this.rules.delete(ruleId);
    const idx = this.ruleIds.indexOf(ruleId);
    if (idx !== -1) {
      this.ruleIds.splice(idx, 1);
    }
  }

  public getRule(ruleId: string): AlertRule | null {
    return this.rules.get(ruleId) || null;
  }

  public hasRule(ruleId: string): boolean {
    return this.rules.has(ruleId);
  }

  public listRules(): ReadonlyArray<AlertRule> {
    const list = this.ruleIds.map((id) => this.rules.get(id)!).filter(Boolean);
    return Object.freeze(list);
  }

  public registerAlert(alert: AlertRecord): void {
    if (this.alerts.has(alert.id)) {
      throw new AlertError(`Alert record with ID '${alert.id}' is already registered.`);
    }
    const isActive = alert.state !== AlertState.RESOLVED && alert.state !== AlertState.EXPIRED;
    if (isActive && this.activeAlertsByFingerprint.has(alert.fingerprint)) {
      throw new AlertError(`An active alert with fingerprint '${alert.fingerprint}' already exists.`);
    }

    this.alerts.set(alert.id, alert);
    this.alertIds.push(alert.id);
    if (isActive) {
      this.activeAlertsByFingerprint.set(alert.fingerprint, alert);
    }
  }

  public getAlert(alertId: string): AlertRecord | null {
    return this.alerts.get(alertId) || null;
  }

  public updateAlert(alert: AlertRecord): void {
    if (!this.alerts.has(alert.id)) {
      throw new AlertNotFoundError(`Alert record with ID '${alert.id}' not found.`);
    }

    const oldAlert = this.alerts.get(alert.id)!;

    // Clean up active fingerprint map
    if (oldAlert.fingerprint !== alert.fingerprint) {
      this.activeAlertsByFingerprint.delete(oldAlert.fingerprint);
    }

    this.alerts.set(alert.id, alert);

    const isActive = alert.state !== AlertState.RESOLVED && alert.state !== AlertState.EXPIRED;

    // Manage active alerts fingerprint map
    if (isActive) {
      // Ensure we don't conflict with another alert's active fingerprint
      const existing = this.activeAlertsByFingerprint.get(alert.fingerprint);
      if (existing && existing.id !== alert.id) {
        throw new AlertError(`An active alert with fingerprint '${alert.fingerprint}' already exists.`);
      }
      this.activeAlertsByFingerprint.set(alert.fingerprint, alert);
    } else {
      // If it became resolved or expired, remove it from active map
      const existing = this.activeAlertsByFingerprint.get(alert.fingerprint);
      if (existing && existing.id === alert.id) {
        this.activeAlertsByFingerprint.delete(alert.fingerprint);
      }
    }
  }

  public removeAlert(alertId: string): void {
    if (!this.alerts.has(alertId)) {
      throw new AlertNotFoundError(`Alert record with ID '${alertId}' not found.`);
    }
    const alert = this.alerts.get(alertId)!;
    this.alerts.delete(alertId);

    const idx = this.alertIds.indexOf(alertId);
    if (idx !== -1) {
      this.alertIds.splice(idx, 1);
    }

    const existing = this.activeAlertsByFingerprint.get(alert.fingerprint);
    if (existing && existing.id === alertId) {
      this.activeAlertsByFingerprint.delete(alert.fingerprint);
    }
  }

  public listActiveAlerts(): ReadonlyArray<AlertRecord> {
    const list = this.alertIds
      .map((id) => this.alerts.get(id)!)
      .filter((alert) => alert && alert.state !== AlertState.RESOLVED && alert.state !== AlertState.EXPIRED);
    return Object.freeze(list);
  }

  public listAlerts(): ReadonlyArray<AlertRecord> {
    const list = this.alertIds.map((id) => this.alerts.get(id)!).filter(Boolean);
    return Object.freeze(list);
  }

  public findByFingerprint(fingerprint: string): AlertRecord | null {
    return this.activeAlertsByFingerprint.get(fingerprint) || null;
  }
}
