/**
 * Command Validator Implementation (Phase 16.6.5).
 *
 * Implements ICommandValidator managing custom validation rules, command existence
 * checks, enabled state verification, parameter schema & type validation, deprecation warnings,
 * validation telemetry statistics, and health reporting.
 */

import {
  CommandDefinition,
  CommandExecutionRequest,
  ValidationDiagnostics,
  ValidationHealth,
  ValidationIssue,
  ValidationResult,
  ValidationRule,
  ValidationStatistics,
  createValidationDiagnostics,
  createValidationHealth,
  createValidationIssue,
  createValidationResult,
  createValidationRule,
  createValidationStatistics,
} from './models';
import { CommandValidationException } from './exceptions';
import { ICommandRegistry, ICommandValidator } from './interfaces';
import { CommandRegistry } from './command_registry';

export class CommandValidator implements ICommandValidator {
  private readonly _registry: ICommandRegistry;
  private readonly _rules = new Map<string, ValidationRule>();

  private _totalValidations = 0;
  private _successfulValidations = 0;
  private _failedValidations = 0;
  private _warningCount = 0;
  private _validationTimes: number[] = [];

  constructor(registry?: ICommandRegistry) {
    this._registry = registry ?? new CommandRegistry();
  }

  public registerValidationRule(
    rule: Partial<ValidationRule> & {
      name: string;
      validate: ValidationRule['validate'];
    },
  ): ValidationRule {
    if (!rule) {
      throw new CommandValidationException('Validation rule cannot be null or undefined.');
    }
    if (!rule.name || !rule.name.trim()) {
      throw new CommandValidationException('Validation rule name cannot be empty.');
    }
    if (!rule.validate) {
      throw new CommandValidationException('Validation rule validate function cannot be null or undefined.');
    }

    const frozen = createValidationRule({
      ruleId: rule.ruleId,
      name: rule.name.trim(),
      description: rule.description,
      validate: rule.validate,
    });

    this._rules.set(frozen.ruleId, frozen);
    return frozen;
  }

  public removeValidationRule(ruleId: string): boolean {
    if (!ruleId || !ruleId.trim()) {
      return false;
    }
    return this._rules.delete(ruleId.trim());
  }

  public listValidationRules(): ReadonlyArray<ValidationRule> {
    return Object.freeze(Array.from(this._rules.values()));
  }

  public async validate(request: CommandExecutionRequest): Promise<ValidationResult> {
    this._totalValidations++;
    const start = performance ? performance.now() : Date.now();
    const issues: ValidationIssue[] = [];

    if (!request) {
      this._failedValidations++;
      const end = performance ? performance.now() : Date.now();
      this.recordTiming(Math.max(0, Math.round((end - start) * 100) / 100));

      return createValidationResult({
        commandId: 'unknown',
        valid: false,
        issues: [
          createValidationIssue({
            severity: 'error',
            code: 'INVALID_REQUEST',
            message: 'Execution request cannot be null or undefined.',
          }),
        ],
      });
    }

    if (!request.commandId || !request.commandId.trim()) {
      this._failedValidations++;
      const end = performance ? performance.now() : Date.now();
      this.recordTiming(Math.max(0, Math.round((end - start) * 100) / 100));

      return createValidationResult({
        commandId: 'unknown',
        valid: false,
        issues: [
          createValidationIssue({
            severity: 'error',
            code: 'MISSING_COMMAND_ID',
            message: 'Command ID in execution request cannot be empty.',
          }),
        ],
      });
    }

    const commandId = request.commandId.trim();

    // 1. Registry Lookup
    let definition: CommandDefinition | undefined = this._registry.findCommand(commandId);
    if (!definition) {
      definition = this._registry.findByAlias(commandId);
    }

    if (!definition) {
      issues.push(
        createValidationIssue({
          severity: 'error',
          code: 'UNKNOWN_COMMAND',
          message: `Command '${commandId}' is not registered.`,
        }),
      );
    } else {
      // 2. Check enabled state
      if (!definition.enabled) {
        issues.push(
          createValidationIssue({
            severity: 'error',
            code: 'COMMAND_DISABLED',
            message: `Command '${definition.id}' is disabled.`,
          }),
        );
      }

      // 3. Check deprecated state
      if (definition.deprecated) {
        issues.push(
          createValidationIssue({
            severity: 'warning',
            code: 'COMMAND_DEPRECATED',
            message: `Command '${definition.id}' is deprecated.`,
          }),
        );
      }

      // 4. Parameter schema validation
      if (definition.parameters && definition.parameters.length > 0) {
        const args = request.args ?? {};

        for (const param of definition.parameters) {
          const val = args[param.name];

          if (param.required && (val === undefined || val === null)) {
            issues.push(
              createValidationIssue({
                severity: 'error',
                code: 'MISSING_REQUIRED_PARAMETER',
                message: `Required parameter '${param.name}' is missing for command '${definition.id}'.`,
                field: param.name,
              }),
            );
          }

          if (val !== undefined && val !== null && param.type !== 'any') {
            let validParamType = true;
            switch (param.type) {
              case 'string':
                validParamType = typeof val === 'string';
                break;
              case 'number':
                validParamType = typeof val === 'number' && !isNaN(val);
                break;
              case 'boolean':
                validParamType = typeof val === 'boolean';
                break;
              case 'object':
                validParamType = typeof val === 'object' && !Array.isArray(val);
                break;
              case 'array':
                validParamType = Array.isArray(val);
                break;
            }

            if (!validParamType) {
              issues.push(
                createValidationIssue({
                  severity: 'error',
                  code: 'INVALID_PARAMETER_TYPE',
                  message: `Parameter '${param.name}' must be of type '${param.type}', received '${typeof val}'.`,
                  field: param.name,
                }),
              );
            }
          }
        }
      }
    }

    // 5. Custom Validation Rules
    for (const rule of this._rules.values()) {
      try {
        const issue = await rule.validate(request, definition);
        if (issue) {
          issues.push(issue);
        }
      } catch (err: any) {
        issues.push(
          createValidationIssue({
            severity: 'error',
            code: 'VALIDATION_RULE_EXCEPTION',
            message: `Validation rule '${rule.name}' threw an error: ${err?.message ?? 'Unknown error'}.`,
          }),
        );
      }
    }

    const end = performance ? performance.now() : Date.now();
    const durationMs = Math.max(0, Math.round((end - start) * 100) / 100);
    this.recordTiming(durationMs);

    const hasErrors = issues.some((i) => i.severity === 'error');
    const warningCount = issues.filter((i) => i.severity === 'warning').length;
    this._warningCount += warningCount;

    if (hasErrors) {
      this._failedValidations++;
    } else {
      this._successfulValidations++;
    }

    return createValidationResult({
      commandId,
      valid: !hasErrors,
      issues,
    });
  }

  public statistics(): ValidationStatistics {
    const totalMs = this._validationTimes.reduce((a, b) => a + b, 0);
    const avgMs =
      this._validationTimes.length > 0 ? totalMs / this._validationTimes.length : 0;

    return createValidationStatistics({
      totalValidations: this._totalValidations,
      successfulValidations: this._successfulValidations,
      failedValidations: this._failedValidations,
      warningCount: this._warningCount,
      averageValidationMs: Math.round(avgMs * 100) / 100,
    });
  }

  public health(): ValidationHealth {
    const failureRate =
      this._totalValidations > 0
        ? Math.round((this._failedValidations / this._totalValidations) * 100)
        : 0;
    const healthy = failureRate <= 20;

    return createValidationHealth({
      healthy,
      failureRate,
      averageValidationMs: this.statistics().averageValidationMs,
      message: healthy
        ? 'Command validator is operational.'
        : `Command validator elevated failure rate (${failureRate}%).`,
    });
  }

  public diagnostics(): ValidationDiagnostics {
    return createValidationDiagnostics({
      statistics: this.statistics(),
      health: this.health(),
      ruleCount: this._rules.size,
    });
  }

  public clear(): void {
    this._rules.clear();
    this._totalValidations = 0;
    this._successfulValidations = 0;
    this._failedValidations = 0;
    this._warningCount = 0;
    this._validationTimes.length = 0;
  }

  private recordTiming(durationMs: number): void {
    this._validationTimes.push(durationMs);
    if (this._validationTimes.length > 1000) {
      this._validationTimes.shift();
    }
  }
}
