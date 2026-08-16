export class CorrelationRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class CorrelationStateError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationStateError';
  }
}

export class CorrelationValidationError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationValidationError';
  }
}

export class CorrelationContextError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationContextError';
  }
}

export class CorrelationEventError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationEventError';
  }
}

export class CorrelationQueryError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationQueryError';
  }
}

export class CorrelationLinkError extends CorrelationRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'CorrelationLinkError';
  }
}
