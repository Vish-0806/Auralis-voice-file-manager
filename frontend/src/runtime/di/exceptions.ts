/**
 * Dependency Injection Exceptions (Phase 16.2.1).
 *
 * Enterprise exception hierarchy for Dependency Injection operations.
 */

export class DependencyInjectionException extends Error {
  public readonly cause?: unknown;

  constructor(message: string, cause?: unknown) {
    super(message);
    this.name = 'DependencyInjectionException';
    this.cause = cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ServiceRegistrationException extends DependencyInjectionException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'ServiceRegistrationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ServiceResolutionException extends DependencyInjectionException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'ServiceResolutionException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class CircularDependencyException extends DependencyInjectionException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'CircularDependencyException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ServiceValidationException extends DependencyInjectionException {
  constructor(message: string, cause?: unknown) {
    super(message, cause);
    this.name = 'ServiceValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
