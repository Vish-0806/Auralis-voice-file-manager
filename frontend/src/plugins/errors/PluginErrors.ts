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

export class PluginManifestError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginManifestError';
  }
}

export class PluginDiscoveryError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginDiscoveryError';
  }
}

export class PluginDuplicateError extends PluginRuntimeError {
  constructor(message: string) {
    super(message);
    this.name = 'PluginDuplicateError';
  }
}

export class PluginLoadError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string, readonly entryPoint?: string) {
    super(message);
    this.name = 'PluginLoadError';
  }
}

export class PluginModuleValidationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginModuleValidationError';
  }
}

export class PluginDuplicateLoadError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginDuplicateLoadError';
  }
}

export class PluginUnloadError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginUnloadError';
  }
}

export class PluginLifecycleError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string, readonly operation?: string) {
    super(message);
    this.name = 'PluginLifecycleError';
  }
}

export class PluginActivationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginActivationError';
  }
}

export class PluginDeactivationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginDeactivationError';
  }
}

export class PluginDisposalError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginDisposalError';
  }
}

export class PluginLifecycleTransitionError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string, readonly fromState?: string, readonly toState?: string) {
    super(message);
    this.name = 'PluginLifecycleTransitionError';
  }
}

export class PluginCapabilityError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginCapabilityError';
  }
}

export class PluginCapabilityRegistrationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginCapabilityRegistrationError';
  }
}

export class PluginCapabilityConflictError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginCapabilityConflictError';
  }
}

export class PluginExtensionError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginExtensionError';
  }
}

export class PluginExtensionRegistrationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginExtensionRegistrationError';
  }
}

export class PluginExtensionConflictError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginExtensionConflictError';
  }
}

export class PluginSecurityError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginSecurityError';
  }
}

export class PluginPermissionError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginPermissionError';
  }
}

export class PluginPolicyError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginPolicyError';
  }
}

export class PluginSandboxError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginSandboxError';
  }
}

export class PluginSecurityViolationError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginSecurityViolationError';
  }
}

export class PluginSecurityProfileError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginSecurityProfileError';
  }
}

export class PluginResourceLimitError extends PluginRuntimeError {
  constructor(message: string, readonly pluginId?: string) {
    super(message);
    this.name = 'PluginResourceLimitError';
  }
}
