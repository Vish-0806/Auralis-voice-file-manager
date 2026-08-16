export class ObservabilityCompositionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ObservabilityCompositionError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class ObservabilityCompositionStateError extends ObservabilityCompositionError {
  constructor(message: string) {
    super(message);
    this.name = 'ObservabilityCompositionStateError';
  }
}

export class ObservabilityCompositionInitializationError extends ObservabilityCompositionError {
  constructor(message: string) {
    super(message);
    this.name = 'ObservabilityCompositionInitializationError';
  }
}

export class ObservabilityCompositionShutdownError extends ObservabilityCompositionError {
  constructor(message: string) {
    super(message);
    this.name = 'ObservabilityCompositionShutdownError';
  }
}
