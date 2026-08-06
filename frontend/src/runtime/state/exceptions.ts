/**
 * State Management Runtime Exception Hierarchy (Phase 16.5).
 *
 * Provides strongly typed exception classes for state runtime operations,
 * initialization errors, provider failures, validation errors, dispatch errors,
 * reducer errors, middleware errors, selector errors, persistence errors,
 * synchronization errors, and certification failures.
 */

export class StateRuntimeException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'StateRuntimeException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class StateInitializationException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'StateInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class StateProviderException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'StateProviderException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class StateValidationException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'StateValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class StateDispatchException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'StateDispatchException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ReducerException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'ReducerException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class MiddlewareException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'MiddlewareException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class SelectorException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'SelectorException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PersistenceException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PersistenceException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class SynchronizationException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'SynchronizationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CertificationException extends StateRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'CertificationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
