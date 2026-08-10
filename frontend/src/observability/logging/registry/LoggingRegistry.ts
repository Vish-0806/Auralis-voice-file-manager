import type { ILogger } from '../interfaces/logger';
import type { ILoggingProvider } from '../interfaces/logging-provider';
import { Logger } from '../provider/Logger';
import type { LogLevelValue } from '../models/log';
import { LoggingRegistrationError, LoggingValidationError, LoggerNotFoundError } from '../errors/LoggingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class LoggingRegistry {
  private readonly loggers = new Map<string, ILogger>();
  private readonly loggerConfigs = new Map<string, { minLevel?: LogLevelValue }>();

  constructor(private readonly provider: ILoggingProvider) {}

  public registerLogger(name: string, config?: { minLevel?: LogLevelValue }): void {
    if (!name || !name.trim()) {
      throw new LoggingValidationError('Logger name cannot be empty.');
    }
    if (this.loggerConfigs.has(name) || this.loggers.has(name)) {
      throw new LoggingRegistrationError(`Logger with name '${name}' is already registered.`);
    }

    const finalConfig = config || {};
    this.loggerConfigs.set(name, finalConfig);
    
    const logger = new Logger(name, this.provider, finalConfig);
    this.loggers.set(name, logger);
  }

  public unregisterLogger(name: string): void {
    if (!this.loggerConfigs.has(name) && !this.loggers.has(name)) {
      throw new LoggerNotFoundError(`Logger with name '${name}' not found.`, name);
    }
    this.loggerConfigs.delete(name);
    this.loggers.delete(name);
  }

  public getLogger(name: string): ILogger {
    if (!name || !name.trim()) {
      throw new LoggingValidationError('Logger name cannot be empty.');
    }
    let logger = this.loggers.get(name);
    if (!logger) {
      const config = {};
      this.loggerConfigs.set(name, config);
      logger = new Logger(name, this.provider, config);
      this.loggers.set(name, logger);
    }
    return logger;
  }

  public hasLogger(name: string): boolean {
    return this.loggers.has(name);
  }

  public listLoggers(): ReadonlyArray<{ name: string; minLevel?: LogLevelValue }> {
    const list = Array.from(this.loggerConfigs.entries()).map(([name, config]) => ({
      name,
      minLevel: config.minLevel
    }));
    list.sort((a, b) => a.name.localeCompare(b.name));
    return freezeDeepSafe(list) as ReadonlyArray<{ name: string; minLevel?: LogLevelValue }>;
  }

  public clear(): void {
    this.loggers.clear();
    this.loggerConfigs.clear();
  }

  public getLoggerCount(): number {
    return this.loggers.size;
  }
}
