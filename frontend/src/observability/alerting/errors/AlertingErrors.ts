export class AlertingRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class AlertingStateError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertingStateError';
  }
}

export class AlertValidationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertValidationError';
  }
}

export class AlertRuleError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertRuleError';
  }
}

export class AlertRuleAlreadyExistsError extends AlertRuleError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertRuleAlreadyExistsError';
  }
}

export class AlertRuleNotFoundError extends AlertRuleError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertRuleNotFoundError';
  }
}

export class AlertError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertError';
  }
}

export class AlertNotFoundError extends AlertError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertNotFoundError';
  }
}

export class AlertStateError extends AlertError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertStateError';
  }
}

export class AlertEvaluationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertEvaluationError';
  }
}

export class AlertSuppressionError extends AlertError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertSuppressionError';
  }
}

export class AlertAcknowledgementError extends AlertError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertAcknowledgementError';
  }
}

export class AlertResolutionError extends AlertError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertResolutionError';
  }
}

export class AlertFingerprintError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertFingerprintError';
  }
}
