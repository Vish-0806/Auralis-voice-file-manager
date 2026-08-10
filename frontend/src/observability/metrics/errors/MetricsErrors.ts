export class MetricsRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MetricsRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class MetricsInitializationError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricsInitializationError';
  }
}

export class MetricsRegistrationError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricsRegistrationError';
  }
}

export class MetricsValidationError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricsValidationError';
  }
}

export class MetricsStateError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricsStateError';
  }
}

export class MetricNotFoundError extends MetricsRuntimeError {
  constructor(message: string, readonly metricName?: string) {
    super(message);
    this.name = 'MetricNotFoundError';
  }
}

export class MetricAlreadyExistsError extends MetricsRuntimeError {
  constructor(message: string, readonly metricName?: string) {
    super(message);
    this.name = 'MetricAlreadyExistsError';
  }
}

export class MetricSeriesError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricSeriesError';
  }
}

export class MetricRecordingError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricRecordingError';
  }
}

export class MetricConfigurationError extends MetricsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'MetricConfigurationError';
  }
}
