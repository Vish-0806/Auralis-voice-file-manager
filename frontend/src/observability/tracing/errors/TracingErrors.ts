export class TracingRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TracingRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class TracingStateError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingStateError';
  }
}

export class TraceValidationError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TraceValidationError';
  }
}

export class TraceNotFoundError extends TracingRuntimeError {
  constructor(message: string, readonly traceId?: string) {
    super(message);
    this.name = 'TraceNotFoundError';
  }
}

export class SpanValidationError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'SpanValidationError';
  }
}

export class SpanNotFoundError extends TracingRuntimeError {
  constructor(message: string, readonly spanId?: string) {
    super(message);
    this.name = 'SpanNotFoundError';
  }
}

export class SpanStateError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'SpanStateError';
  }
}

export class TraceContextError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TraceContextError';
  }
}

export class TracingCapacityError extends TracingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'TracingCapacityError';
  }
}
