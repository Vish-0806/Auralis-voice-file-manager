export class MonitoringRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class MonitoringInitializationError extends MonitoringRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringInitializationError';
  }
}

export class MonitoringRegistrationError extends MonitoringRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringRegistrationError';
  }
}

export class MonitoringValidationError extends MonitoringRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringValidationError';
  }
}

export class MonitoringStateError extends MonitoringRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringStateError';
  }
}

export class MonitoringComponentNotFoundError extends MonitoringRuntimeError {
  constructor(message: string, readonly componentId?: string) {
    super(message);
    this.name = 'MonitoringComponentNotFoundError';
  }
}

export class MonitoringCheckNotFoundError extends MonitoringRuntimeError {
  constructor(message: string, readonly checkId?: string) {
    super(message);
    this.name = 'MonitoringCheckNotFoundError';
  }
}

export class MonitoringCheckExecutionError extends MonitoringRuntimeError {
  constructor(message: string, readonly checkId?: string, readonly originalError?: Error) {
    super(message);
    this.name = 'MonitoringCheckExecutionError';
  }
}
