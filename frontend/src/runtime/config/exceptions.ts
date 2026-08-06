/**
 * Configuration Runtime Exception Hierarchy (Phase 16.3.1).
 *
 * Provides strongly-typed exception classes for configuration runtime errors,
 * initialization failures, provider errors, validation failures, and configuration errors.
 */

export class ConfigurationRuntimeException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationRuntimeException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConfigurationInitializationException extends ConfigurationRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationInitializationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConfigurationProviderException extends ConfigurationRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationProviderException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConfigurationValidationException extends ConfigurationRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationValidationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ConfigurationConfigurationException extends ConfigurationRuntimeException {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationConfigurationException';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}
