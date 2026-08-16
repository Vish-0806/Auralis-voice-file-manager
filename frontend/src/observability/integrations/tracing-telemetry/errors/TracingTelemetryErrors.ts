export class TracingTelemetryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class TracingTelemetryPolicyError extends TracingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryPolicyError';
  }
}

export class TracingTelemetryValidationError extends TracingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryValidationError';
  }
}

export class TracingTelemetryIntegrationError extends TracingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryIntegrationError';
  }
}

export class TracingTelemetryDispatchError extends TracingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryDispatchError';
  }
}

export class TracingTelemetryStateError extends TracingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingTelemetryStateError';
  }
}
