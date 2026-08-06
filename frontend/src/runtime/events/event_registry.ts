/**
 * Event Registry Engine (Phase 16.4.2).
 *
 * Manages registered event type definitions, validates event names, prevents duplicate registrations,
 * and maintains telemetry on registrations, unregistrations, and duplicate rejections.
 */

import { EventRegistration } from './models';
import { EventProviderException } from './exceptions';
import { IEventRegistry } from './interfaces';

export class EventRegistry implements IEventRegistry {
  private readonly _registrations = new Map<string, EventRegistration>();

  private _registrationCount = 0;
  private _unregistrationCount = 0;
  private _duplicatesRejected = 0;

  public register(registration: EventRegistration): void {
    if (!registration) {
      throw new EventProviderException('Event registration cannot be null or undefined.');
    }
    const type = registration.eventType ? registration.eventType.trim() : '';
    if (!type) {
      throw new EventProviderException('Event type name cannot be empty.');
    }
    if (this._registrations.has(type)) {
      this._duplicatesRejected++;
      throw new EventProviderException(`Event type '${type}' is already registered.`);
    }

    this._registrations.set(type, registration);
    this._registrationCount++;
  }

  public unregister(eventType: string): boolean {
    const type = eventType ? eventType.trim() : '';
    const removed = this._registrations.delete(type);
    if (removed) {
      this._unregistrationCount++;
    }
    return removed;
  }

  public contains(eventType: string): boolean {
    return this._registrations.has(eventType.trim());
  }

  public get(eventType: string): EventRegistration | undefined {
    return this._registrations.get(eventType.trim());
  }

  public list(): ReadonlyArray<EventRegistration> {
    return Object.freeze(Array.from(this._registrations.values()));
  }

  public count(): number {
    return this._registrations.size;
  }

  public clear(): void {
    this._registrations.clear();
  }

  public telemetry(): { registrationCount: number; unregistrationCount: number; duplicatesRejected: number } {
    return Object.freeze({
      registrationCount: this._registrationCount,
      unregistrationCount: this._unregistrationCount,
      duplicatesRejected: this._duplicatesRejected,
    });
  }
}
