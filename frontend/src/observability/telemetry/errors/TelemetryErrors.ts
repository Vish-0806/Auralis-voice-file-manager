export class TelemetryRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class TelemetryStateError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryStateError';
  }
}

export class TelemetryValidationError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryValidationError';
  }
}

export class TelemetryExporterError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryExporterError';
  }
}

export class TelemetryExporterAlreadyExistsError extends TelemetryExporterError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryExporterAlreadyExistsError';
  }
}

export class TelemetryExporterNotFoundError extends TelemetryExporterError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryExporterNotFoundError';
  }
}

export class TelemetryBufferError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryBufferError';
  }
}

export class TelemetryBatchError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryBatchError';
  }
}

export class TelemetrySamplingError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetrySamplingError';
  }
}

export class TelemetryFlushError extends TelemetryRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TelemetryFlushError';
  }
}
