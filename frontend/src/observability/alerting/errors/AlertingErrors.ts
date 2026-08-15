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

export class AlertNotFoundError extends AlertingRuntimeError {
  constructor(message: string, readonly alertId?: string) {
    super(message);
    this.name = 'AlertNotFoundError';
  }
}

export class AlertRuleValidationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertRuleValidationError';
  }
}

export class AlertRuleAlreadyExistsError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertRuleAlreadyExistsError';
  }
}

export class AlertRuleNotFoundError extends AlertingRuntimeError {
  constructor(message: string, readonly ruleId?: string) {
    super(message);
    this.name = 'AlertRuleNotFoundError';
  }
}

export class AlertEvaluationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertEvaluationError';
  }
}

export class AlertGenerationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertGenerationError';
  }
}

export class AlertDeduplicationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertDeduplicationError';
  }
}

export class AlertLifecycleError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertLifecycleError';
  }
}

export class AlertLifecycleStateError extends AlertLifecycleError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertLifecycleStateError';
  }
}

export class AlertLifecycleTransitionError extends AlertLifecycleError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertLifecycleTransitionError';
  }
}

export class AlertLifecycleNotFoundError extends AlertLifecycleError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertLifecycleNotFoundError';
  }
}




