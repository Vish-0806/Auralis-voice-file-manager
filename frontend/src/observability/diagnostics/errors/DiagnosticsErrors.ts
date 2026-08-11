export class DiagnosticsRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class DiagnosticsStateError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticsStateError';
  }
}

export class DiagnosticValidationError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticValidationError';
  }
}

export class DiagnosticSourceError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticSourceError';
  }
}

export class DiagnosticSourceAlreadyExistsError extends DiagnosticSourceError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticSourceAlreadyExistsError';
  }
}

export class DiagnosticSourceNotFoundError extends DiagnosticSourceError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticSourceNotFoundError';
  }
}

export class DiagnosticCheckError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticCheckError';
  }
}

export class DiagnosticCheckAlreadyExistsError extends DiagnosticCheckError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticCheckAlreadyExistsError';
  }
}

export class DiagnosticCheckNotFoundError extends DiagnosticCheckError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticCheckNotFoundError';
  }
}

export class DiagnosticExecutionError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticExecutionError';
  }
}

export class DiagnosticTimeoutError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticTimeoutError';
  }
}

export class DiagnosticReportError extends DiagnosticsRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'DiagnosticReportError';
  }
}
