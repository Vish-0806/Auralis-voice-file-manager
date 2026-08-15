import { AlertRecord } from '../models/alert';
import { AlertValidationError, AlertNotFoundError } from '../errors/AlertingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class AlertRegistry {
  private readonly _alerts = new Map<string, AlertRecord>();
  private readonly _order: string[] = [];

  public registerAlert(alert: AlertRecord): void {
    if (!alert || !alert.id) {
      throw new AlertValidationError('Invalid alert: alert ID is required.');
    }
    if (this._alerts.has(alert.id)) {
      throw new AlertValidationError(`Alert with ID '${alert.id}' is already registered.`);
    }

    // Store a deep-frozen defensive copy
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
}
