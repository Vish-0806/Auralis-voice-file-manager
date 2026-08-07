/**
 * Command Runtime Exception Hierarchy (Phase 16.6.1).
 *
 * Defines custom exceptions for command runtime initialization, provider errors,
 * execution failures, and command validation errors.
 */

export class CommandRuntimeException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CommandRuntimeException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CommandInitializationException extends CommandRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'CommandInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CommandProviderException extends CommandRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'CommandProviderException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CommandExecutionException extends CommandRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'CommandExecutionException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CommandValidationException extends CommandRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'CommandValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
