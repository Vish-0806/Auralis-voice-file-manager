/**
 * Frontend Runtime Exception Hierarchy (Phase 16.1).
 *
 * Enterprise custom exception hierarchy for frontend runtime operations.
 */

export class FrontendRuntimeException extends Error {
  public readonly cause?: unknown;

  constructor(message: string, cause?: unknown) {
    super(message);
    this.name = 'FrontendRuntimeException';
    this.cause = cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class FrontendInitializationException extends FrontendRuntimeException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'FrontendInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class FrontendConfigurationException extends FrontendRuntimeException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'FrontendConfigurationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class FrontendProviderException extends FrontendRuntimeException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'FrontendProviderException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class FrontendValidationException extends FrontendRuntimeException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'FrontendValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
