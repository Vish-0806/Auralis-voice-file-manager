/**
 * Plugin Runtime Exception Hierarchy (Phase 16.7).
 *
 * Defines custom exceptions for plugin runtime initialization, registration,
 * validation, dependencies, permissions, sandboxing, lifecycles, and execution.
 */

export class PluginRuntimeException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'PluginRuntimeException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginInitializationException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginRegistrationException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginRegistrationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginValidationException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginDependencyException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginDependencyException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginPermissionException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginPermissionException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginSandboxException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginSandboxException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginLifecycleException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginLifecycleException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginActivationException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginActivationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginExecutionException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginExecutionException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginCompatibilityException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginCompatibilityException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class PluginCertificationException extends PluginRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'PluginCertificationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
