export class LoggingRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class LoggingInitializationError extends LoggingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingInitializationError';
  }
}

export class LoggingRegistrationError extends LoggingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingRegistrationError';
  }
}

export class LoggingValidationError extends LoggingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingValidationError';
  }
}

export class LoggingStateError extends LoggingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingStateError';
  }
}

export class LoggerNotFoundError extends LoggingRuntimeError {
  constructor(message: string, readonly loggerName?: string) {
    super(message);
    this.name = 'LoggerNotFoundError';
  }
}

export class LogSinkNotFoundError extends LoggingRuntimeError {
  constructor(message: string, readonly sinkId?: string) {
    super(message);
    this.name = 'LogSinkNotFoundError';
  }
}

export class LogSinkWriteError extends LoggingRuntimeError {
  constructor(message: string, readonly sinkId?: string, readonly originalError?: Error) {
    super(message);
    this.name = 'LogSinkWriteError';
  }
}

export class LoggingConfigurationError extends LoggingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingConfigurationError';
  }
}
