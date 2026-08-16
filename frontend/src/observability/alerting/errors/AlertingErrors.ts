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

export class AlertSuppressionError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertSuppressionError';
  }
}

export class AlertSuppressionPolicyError extends AlertSuppressionError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertSuppressionPolicyError';
  }
}

export class AlertMaintenanceWindowError extends AlertSuppressionError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertMaintenanceWindowError';
  }
}

export class AlertSnoozeError extends AlertSuppressionError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertSnoozeError';
  }
}

export class AlertSuppressionEvaluationError extends AlertSuppressionError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertSuppressionEvaluationError';
  }
}

export class AlertNotificationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertNotificationError';
  }
}

export class NotificationValidationError extends AlertNotificationError {
  constructor(message: string) {
    super(message);
    this.name = 'NotificationValidationError';
  }
}

export class NotificationChannelError extends AlertNotificationError {
  constructor(message: string) {
    super(message);
    this.name = 'NotificationChannelError';
  }
}

export class NotificationDispatchError extends AlertNotificationError {
  constructor(message: string) {
    super(message);
    this.name = 'NotificationDispatchError';
  }
}

export class NotificationDeliveryError extends AlertNotificationError {
  constructor(message: string) {
    super(message);
    this.name = 'NotificationDeliveryError';
  }
}

export class NotificationChannelNotFoundError extends AlertNotificationError {
  constructor(message: string) {
    super(message);
    this.name = 'NotificationChannelNotFoundError';
  }
}

export class AlertOrchestrationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertOrchestrationError';
  }
}

export class AlertOrchestrationStateError extends AlertOrchestrationError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertOrchestrationStateError';
  }
}

export class AlertOrchestrationStageError extends AlertOrchestrationError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertOrchestrationStageError';
  }
}

export class AlertOrchestrationFailureError extends AlertOrchestrationError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertOrchestrationFailureError';
  }
}

export class AlertCertificationError extends AlertingRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertCertificationError';
  }
}

export class AlertCertificationStageError extends AlertCertificationError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertCertificationStageError';
  }
}

export class AlertCertificationFailureError extends AlertCertificationError {
  constructor(message: string) {
    super(message);
    this.name = 'AlertCertificationFailureError';
  }
}







