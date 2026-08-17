export class AlertingTelemetryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class AlertingTelemetryValidationError extends AlertingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryValidationError';
  }
}

export class AlertingTelemetryPolicyError extends AlertingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryPolicyError';
  }
}

export class AlertingTelemetryStateError extends AlertingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryStateError';
  }
}

export class AlertingTelemetryConversionError extends AlertingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryConversionError';
  }
}

export class AlertingTelemetryDispatchError extends AlertingTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingTelemetryDispatchError';
  }
}
