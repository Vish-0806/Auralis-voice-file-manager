import {
  AlertLifecycleStateValue,
  AlertLifecycleActorValue,
  AlertLifecycleHistoryEntry,
  AlertLifecycleRecord
} from '../models/lifecycle';
import {
  AlertLifecycleNotFoundError,
  AlertLifecycleTransitionError,
  AlertLifecycleStateError
} from '../errors/AlertingErrors';
import {
  createAlertLifecycleRecord,
  createAlertLifecycleHistoryEntry
} from '../factories/alertingFactories';

export class AlertLifecycleManager {
  private readonly _records = new Map<string, AlertLifecycleRecord>();
  private readonly _insertionOrder: string[] = [];
  private readonly _maxCapacity: number;

  private _lifecycleTransitions = 0;
  private _acknowledgements = 0;
  private _resolutions = 0;
  private _closures = 0;
  private _invalidTransitions = 0;

  constructor(maxCapacity = 1000) {
    this._maxCapacity = maxCapacity;
  }

  public initializeRecord(alertId: string, fingerprint?: string, now?: number): AlertLifecycleRecord {
    if (!alertId) {
      throw new AlertLifecycleStateError('alertId is required to initialize lifecycle');
    }

    const existing = this._records.get(alertId);
    if (existing) {
      return existing;
    }

    const timestamp = now !== undefined ? now : Date.now();

    const initialHistory = createAlertLifecycleHistoryEntry({
      alertId,
      fingerprint,
      previousState: null,
      nextState: 'ACTIVE',
      timestamp,
      actor: 'SYSTEM',
      operation: 'INITIALIZE',
      reason: 'Alert lifecycle initialized'
    });

    const record = createAlertLifecycleRecord({
      alertId,
      fingerprint,
      state: 'ACTIVE',
      createdAt: timestamp,
      updatedAt: timestamp,
      history: [initialHistory]
    });

    this.saveRecord(alertId, record);
    return record;
  }

  public transition(
    alertId: string,
    nextState: AlertLifecycleStateValue,
    actor: AlertLifecycleActorValue,
    operation: string,
    reason?: string,
    metadata?: Record<string, unknown>,
    now?: number
  ): AlertLifecycleRecord {
    const record = this._records.get(alertId);
    if (!record) {
      throw new AlertLifecycleNotFoundError(`Alert lifecycle record not found for ID: ${alertId}`);
    }

    const timestamp = now !== undefined ? now : Date.now();
    const currentState = record.state;

    if (!this.isValidTransition(currentState, nextState)) {
      this._invalidTransitions++;
      throw new AlertLifecycleTransitionError(
        `Invalid lifecycle transition from ${currentState} to ${nextState} for alert ID: ${alertId}`
      );
    }

    const entry = createAlertLifecycleHistoryEntry({
      alertId,
      fingerprint: record.fingerprint,
      previousState: currentState,
      nextState,
      timestamp,
      actor,
      operation,
      reason,
      metadata
    });

    const updatedRecord = createAlertLifecycleRecord({
      alertId,
      fingerprint: record.fingerprint,
      state: nextState,
      createdAt: record.createdAt,
      updatedAt: timestamp,
      history: [...record.history, entry],
      metadata: metadata ? JSON.parse(JSON.stringify(metadata)) : record.metadata
    });

    this._lifecycleTransitions++;
    if (nextState === 'ACKNOWLEDGED') {
      this._acknowledgements++;
    } else if (nextState === 'RESOLVED') {
      this._resolutions++;
    } else if (nextState === 'CLOSED') {
      this._closures++;
    }

    this.saveRecord(alertId, updatedRecord);
    return updatedRecord;
  }

  public getRecord(alertId: string): AlertLifecycleRecord | null {
    return this._records.get(alertId) || null;
  }

  public getHistory(alertId: string): ReadonlyArray<AlertLifecycleHistoryEntry> {
    const record = this._records.get(alertId);
    if (!record) {
      throw new AlertLifecycleNotFoundError(`Alert lifecycle record not found for ID: ${alertId}`);
    }
    return record.history;
  }

  public clear(alertId: string): void {
    if (this._records.has(alertId)) {
      this._records.delete(alertId);
      const index = this._insertionOrder.indexOf(alertId);
      if (index !== -1) {
        this._insertionOrder.splice(index, 1);
      }
    }
  }

  public clearAll(): void {
    this._records.clear();
    this._insertionOrder.length = 0;
    this._lifecycleTransitions = 0;
    this._acknowledgements = 0;
    this._resolutions = 0;
    this._closures = 0;
    this._invalidTransitions = 0;
  }

  public getTransitionStats() {
    let activeAlerts = 0;
    let acknowledgedAlerts = 0;
    let resolvedAlerts = 0;
    let closedAlerts = 0;

    for (const record of this._records.values()) {
      if (record.state === 'ACTIVE') {
        activeAlerts++;
      } else if (record.state === 'ACKNOWLEDGED') {
        acknowledgedAlerts++;
      } else if (record.state === 'RESOLVED') {
        resolvedAlerts++;
      } else if (record.state === 'CLOSED') {
        closedAlerts++;
      }
    }

    return {
      lifecycleTransitions: this._lifecycleTransitions,
      acknowledgements: this._acknowledgements,
      resolutions: this._resolutions,
      closures: this._closures,
      invalidTransitions: this._invalidTransitions,
      activeAlerts,
      acknowledgedAlerts,
      resolvedAlerts,
      closedAlerts
    };
  }

  public getDiagnostics() {
    let lastTransitionTimestamp = 0;
    let totalHistoryEntries = 0;

    for (const record of this._records.values()) {
      totalHistoryEntries += record.history.length;
      for (const entry of record.history) {
        if (entry.timestamp > lastTransitionTimestamp) {
          lastTransitionTimestamp = entry.timestamp;
        }
      }
    }

    const stateCounts = this.getTransitionStats();

    return {
      activeCount: stateCounts.activeAlerts,
      acknowledgedCount: stateCounts.acknowledgedAlerts,
      resolvedCount: stateCounts.resolvedAlerts,
      closedCount: stateCounts.closedAlerts,
      transitionCount: stateCounts.lifecycleTransitions,
      historySize: totalHistoryEntries,
      lastTransitionTimestamp
    };
  }

  private isValidTransition(from: AlertLifecycleStateValue, to: AlertLifecycleStateValue): boolean {
    if (from === 'CLOSED') {
      return false;
    }
    if (from === 'ACTIVE') {
      return to === 'ACKNOWLEDGED' || to === 'RESOLVED' || to === 'CLOSED';
    }
    if (from === 'ACKNOWLEDGED') {
      return to === 'RESOLVED' || to === 'ACTIVE' || to === 'CLOSED';
    }
    if (from === 'RESOLVED') {
      return to === 'ACTIVE' || to === 'CLOSED';
    }
    return false;
  }

  private saveRecord(alertId: string, record: AlertLifecycleRecord): void {
    if (!this._records.has(alertId)) {
      this._insertionOrder.push(alertId);
    }
    this._records.set(alertId, record);

    if (this._records.size > this._maxCapacity) {
      const oldestId = this._insertionOrder.shift();
      if (oldestId !== undefined) {
        this._records.delete(oldestId);
      }
    }
  }
}
