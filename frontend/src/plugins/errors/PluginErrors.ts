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
