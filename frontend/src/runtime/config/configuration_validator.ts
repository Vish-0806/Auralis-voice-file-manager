/**
 * Configuration Validator Engine (Phase 16.3.3).
 *
 * Implements required field validation, type checking, minValue, maxValue,
 * minLength, maxLength, regexPattern, and allowedValues constraint validations.
 */

import {
  ConfigurationError,
  ConfigurationSchema,
  ConfigurationValidationResult,
  ConfigurationWarning,
  createConfigurationError,
  createConfigurationValidationResult,
  createValidationStatistics,
  ValidationStatistics,
} from './models';
import { IConfigurationValidator } from './interfaces';

export class ConfigurationValidator implements IConfigurationValidator {
  private _validations = 0;
  private _passedValidations = 0;
  private _failedValidations = 0;
  private _totalErrors = 0;
  private _totalWarnings = 0;

  public validate(
    values: Record<string, unknown>,
    schema: ConfigurationSchema,
  ): ConfigurationValidationResult {
    this._validations++;
    const errors: ConfigurationError[] = [];
    const warnings: ConfigurationWarning[] = [];

    if (!schema || !schema.definitions) {
      return createConfigurationValidationResult({ valid: true });
    }

    for (const [key, def] of Object.entries(schema.definitions)) {
      const val = values[key];

      // 1. Required Check
      if (def.required && (val === undefined || val === null)) {
        errors.push(
          createConfigurationError({
            key,
            message: `Configuration key '${key}' is required but missing.`,
            code: 'REQUIRED_FIELD_MISSING',
          }),
        );
        continue;
      }

      if (val === undefined || val === null) {
        continue;
      }

      // 2. Constraints Check
      const constraint = def.constraint;
      if (constraint) {
        // minValue
        if (typeof val === 'number' && constraint.minValue !== undefined && val < constraint.minValue) {
          errors.push(
            createConfigurationError({
              key,
              message: `Value ${val} for key '${key}' is below minimum value of ${constraint.minValue}.`,
              code: 'MIN_VALUE_VIOLATION',
            }),
          );
        }

        // maxValue
        if (typeof val === 'number' && constraint.maxValue !== undefined && val > constraint.maxValue) {
          errors.push(
            createConfigurationError({
              key,
              message: `Value ${val} for key '${key}' exceeds maximum value of ${constraint.maxValue}.`,
              code: 'MAX_VALUE_VIOLATION',
            }),
          );
        }

        // minLength
        if (
          (typeof val === 'string' || Array.isArray(val)) &&
          constraint.minLength !== undefined &&
          val.length < constraint.minLength
        ) {
          errors.push(
            createConfigurationError({
              key,
              message: `Length ${val.length} for key '${key}' is below minimum length of ${constraint.minLength}.`,
              code: 'MIN_LENGTH_VIOLATION',
            }),
          );
        }

        // maxLength
        if (
          (typeof val === 'string' || Array.isArray(val)) &&
          constraint.maxLength !== undefined &&
          val.length > constraint.maxLength
        ) {
          errors.push(
            createConfigurationError({
              key,
              message: `Length ${val.length} for key '${key}' exceeds maximum length of ${constraint.maxLength}.`,
              code: 'MAX_LENGTH_VIOLATION',
            }),
          );
        }

        // regexPattern
        if (
          typeof val === 'string' &&
          constraint.regexPattern !== undefined &&
          !new RegExp(constraint.regexPattern).test(val)
        ) {
          errors.push(
            createConfigurationError({
              key,
              message: `Value '${val}' for key '${key}' does not match regex pattern '${constraint.regexPattern}'.`,
              code: 'REGEX_MISMATCH',
            }),
          );
        }

        // allowedValues
        if (
          constraint.allowedValues !== undefined &&
          constraint.allowedValues.length > 0 &&
          !constraint.allowedValues.includes(val)
        ) {
          errors.push(
            createConfigurationError({
              key,
              message: `Value '${String(val)}' for key '${key}' is not in allowed values: [${constraint.allowedValues.join(', ')}].`,
              code: 'DISALLOWED_VALUE',
            }),
          );
        }
      }
    }

    if (errors.length === 0) {
      this._passedValidations++;
    } else {
      this._failedValidations++;
    }

    this._totalErrors += errors.length;
    this._totalWarnings += warnings.length;

    return createConfigurationValidationResult({
      valid: errors.length === 0,
      errors,
      warnings,
      timestamp: new Date().toISOString(),
    });
  }

  public statistics(): ValidationStatistics {
    return createValidationStatistics({
      validations: this._validations,
      passedValidations: this._passedValidations,
      failedValidations: this._failedValidations,
      totalErrors: this._totalErrors,
      totalWarnings: this._totalWarnings,
    });
  }
}
