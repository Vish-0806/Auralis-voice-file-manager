export class PluginRuntimeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PluginRuntimeError';
    Object.setPrototypeOf(this, new.target.prototype);

    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, new.target);
    }
  }
}

export class PluginInitializationError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginInitializationError';
  }
}

export class PluginRegistrationError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginRegistrationError';
  }
}

export class PluginValidationError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginValidationError';
  }
}

export class PluginStateError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginStateError';
  }
}
