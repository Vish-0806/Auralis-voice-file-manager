export class DiagnosticsTelemetryError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class DiagnosticsTelemetryPolicyError extends DiagnosticsTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryPolicyError';
  }
}

export class DiagnosticsTelemetryValidationError extends DiagnosticsTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryValidationError';
  }
}

export class DiagnosticsTelemetryIntegrationError extends DiagnosticsTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryIntegrationError';
  }
}

export class DiagnosticsTelemetryDispatchError extends DiagnosticsTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryDispatchError';
  }
}

export class DiagnosticsTelemetryStateError extends DiagnosticsTelemetryError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsTelemetryStateError';
  }
}
