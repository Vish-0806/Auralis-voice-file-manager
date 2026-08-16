export class MonitoringAlertingIntegrationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringAlertingIntegrationError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class MonitoringAlertingStateError extends MonitoringAlertingIntegrationError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringAlertingStateError';
  }
}

export class MonitoringAlertingPolicyError extends MonitoringAlertingIntegrationError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringAlertingPolicyError';
  }
}

export class MonitoringAlertingTriggerError extends MonitoringAlertingIntegrationError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringAlertingTriggerError';
  }
}

export class MonitoringAlertingDispatchError extends MonitoringAlertingIntegrationError {
  constructor(message: string) {
    super(message);
    this.name = 'MonitoringAlertingDispatchError';
  }
}
