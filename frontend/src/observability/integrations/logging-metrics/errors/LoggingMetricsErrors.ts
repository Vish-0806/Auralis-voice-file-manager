export class LoggingMetricsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class LoggingMetricsPolicyError extends LoggingMetricsError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsPolicyError';
  }
}

export class LoggingMetricsValidationError extends LoggingMetricsError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsValidationError';
  }
}

export class LoggingMetricsIntegrationError extends LoggingMetricsError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsIntegrationError';
  }
}

export class LoggingMetricsDispatchError extends LoggingMetricsError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsDispatchError';
  }
}

export class LoggingMetricsStateError extends LoggingMetricsError {
  constructor(message: string) {
    super(message);
    this.name = 'LoggingMetricsStateError';
  }
}

