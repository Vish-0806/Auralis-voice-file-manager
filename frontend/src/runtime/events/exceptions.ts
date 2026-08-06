/**
 * Event Runtime Exception Hierarchy (Phase 16.4.1).
 *
 * Defines custom exceptions for event runtime initialization, provider errors,
 * dispatch failures, and event validation errors.
 */

export class EventRuntimeException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EventRuntimeException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class EventInitializationException extends EventRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'EventInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class EventProviderException extends EventRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'EventProviderException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class EventDispatchException extends EventRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'EventDispatchException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class EventValidationException extends EventRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'EventValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
