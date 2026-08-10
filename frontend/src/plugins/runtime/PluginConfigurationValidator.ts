import type {
  PluginConfigurationSchema,
  PluginConfigurationValidationResult,
  PluginConfigurationValidationIssue
} from '../models/configuration';
import { createPluginConfigurationValidationResult } from '../models/configuration';

export class PluginConfigurationValidator {
  public static validate(
    schema: PluginConfigurationSchema,
    values: Record<string, any>,
    previousValues?: Record<string, any>,
    options?: { skipRequired?: boolean }
  ): PluginConfigurationValidationResult {
    const issues: PluginConfigurationValidationIssue[] = [];

    // 1. Check for unexpected keys in strict mode
    if (schema.strict) {
      const allowedKeys = new Set(schema.fields.map(f => f.key));
      for (const key of Object.keys(values)) {
        if (!allowedKeys.has(key)) {
          issues.push({
            key,
            code: 'UNKNOWN_KEY',
            message: `Key '${key}' is not defined in strict schema.`,
            severity: 'ERROR',
            actual: typeof values[key]
          });
        }
      }
    }

    // 2. Validate declared fields
    for (const field of schema.fields) {
      const key = field.key;
      const value = values[key];
      const hasValue = key in values;

      // Required check
      if (field.required && !hasValue && !options?.skipRequired) {
        issues.push({
          key,
          code: 'REQUIRED_FIELD_MISSING',
          message: `Required configuration field '${key}' is missing.`,
          severity: 'ERROR'
        });
        continue;
      }

      // If value is not present, skip subsequent checks
      if (!hasValue) {
        continue;
      }

      // Null check
      if (value === null) {
        if (!field.nullable) {
          issues.push({
            key,
            code: 'NULL_NOT_ALLOWED',
            message: `Field '${key}' cannot be null.`,
            severity: 'ERROR'
          });
        }
        continue; // Null satisfies type check when nullable
      }

      // Read-only check
      if (field.readOnly && previousValues && key in previousValues) {
        if (value !== previousValues[key]) {
          issues.push({
            key,
            code: 'READ_ONLY_FIELD',
            message: `Field '${key}' is read-only and cannot be modified.`,
            severity: 'ERROR',
            expected: String(previousValues[key]),
            actual: String(value)
          });
          continue;
        }
      }

      // Type check
      let typeValid = false;
      const t = field.type;
      if (t === 'string') {
        typeValid = typeof value === 'string';
      } else if (t === 'number') {
        typeValid = typeof value === 'number' && !isNaN(value);
      } else if (t === 'boolean') {
        typeValid = typeof value === 'boolean';
      } else if (t === 'object') {
        typeValid = typeof value === 'object' && value !== null && !Array.isArray(value);
      } else if (t === 'array') {
        typeValid = Array.isArray(value);
      } else if (t === 'null') {
        typeValid = value === null;
      }

      if (!typeValid) {
        issues.push({
          key,
          code: 'INVALID_TYPE',
          message: `Field '${key}' expects type '${t}', got '${typeof value}'.`,
          severity: 'ERROR',
          expected: t,
          actual: typeof value
        });
        continue;
      }

      // Constraints: String
      if (t === 'string' && typeof value === 'string') {
        if (field.minLength !== undefined && value.length < field.minLength) {
          issues.push({
            key,
            code: 'MIN_LENGTH_VIOLATION',
            message: `String field '${key}' length is under minimum of ${field.minLength} characters.`,
            expected: `>= ${field.minLength}`,
            actual: `${value.length}`,
            severity: 'ERROR'
          });
        }
        if (field.maxLength !== undefined && value.length > field.maxLength) {
          issues.push({
            key,
            code: 'MAX_LENGTH_VIOLATION',
            message: `String field '${key}' length is over maximum of ${field.maxLength} characters.`,
            expected: `<= ${field.maxLength}`,
            actual: `${value.length}`,
            severity: 'ERROR'
          });
        }
        if (field.pattern) {
          try {
            const rx = new RegExp(field.pattern);
            if (!rx.test(value)) {
              issues.push({
                key,
                code: 'PATTERN_VIOLATION',
                message: `String field '${key}' does not match pattern '${field.pattern}'.`,
                expected: field.pattern,
                actual: value,
                severity: 'ERROR'
              });
            }
          } catch {}
        }
      }

      // Constraints: Number
      if (t === 'number' && typeof value === 'number') {
        if (field.minimum !== undefined && value < field.minimum) {
          issues.push({
            key,
            code: 'MINIMUM_VIOLATION',
            message: `Number field '${key}' is under minimum value of ${field.minimum}.`,
            expected: `>= ${field.minimum}`,
            actual: String(value),
            severity: 'ERROR'
          });
        }
        if (field.maximum !== undefined && value > field.maximum) {
          issues.push({
            key,
            code: 'MAXIMUM_VIOLATION',
            message: `Number field '${key}' is over maximum value of ${field.maximum}.`,
            expected: `<= ${field.maximum}`,
            actual: String(value),
            severity: 'ERROR'
          });
        }
      }

      // Constraint: allowedValues
      if (field.allowedValues) {
        if (!field.allowedValues.includes(value)) {
          issues.push({
            key,
            code: 'ALLOWED_VALUES_VIOLATION',
            message: `Field '${key}' has invalid value. Allowed values are: ${field.allowedValues.join(', ')}.`,
            expected: field.allowedValues.join('|'),
            actual: String(value),
            severity: 'ERROR'
          });
        }
      }
    }

    return createPluginConfigurationValidationResult({
      valid: issues.filter(i => i.severity === 'ERROR').length === 0,
      issues,
      validatedAt: Date.now()
    });
  }

  public static validateCompatibility(
    oldSchema: PluginConfigurationSchema,
    newSchema: PluginConfigurationSchema
  ): PluginConfigurationValidationResult {
    const issues: PluginConfigurationValidationIssue[] = [];

    // 1. Detect incompatible type changes
    for (const newField of newSchema.fields) {
      const oldField = oldSchema.fields.find(f => f.key === newField.key);
      if (oldField) {
        if (oldField.type !== newField.type) {
          issues.push({
            key: newField.key,
            code: 'INCOMPATIBLE_TYPE_CHANGE',
            message: `Field '${newField.key}' type changed from '${oldField.type}' to '${newField.type}'.`,
            severity: 'ERROR',
            expected: oldField.type,
            actual: newField.type
          });
        }
      }
    }

    // 2. Detect removed required fields
    for (const oldField of oldSchema.fields) {
      if (oldField.required) {
        const newField = newSchema.fields.find(f => f.key === oldField.key);
        if (!newField) {
          issues.push({
            key: oldField.key,
            code: 'REMOVED_REQUIRED_FIELD',
            message: `Required field '${oldField.key}' was removed.`,
            severity: 'ERROR'
          });
        }
      }
    }

    // 3. Detect invalid default changes
    for (const newField of newSchema.fields) {
      if (newField.defaultValue !== undefined) {
        const tempSchema = {
          ...newSchema,
          fields: [newField]
        };
        const val = this.validate(tempSchema, { [newField.key]: newField.defaultValue }, undefined, { skipRequired: true });
        if (!val.valid) {
          issues.push({
            key: newField.key,
            code: 'INVALID_DEFAULT_CHANGE',
            message: `Default value for field '${newField.key}' is invalid.`,
            severity: 'ERROR'
          });
        }
      }
    }

    return createPluginConfigurationValidationResult({
      valid: issues.filter(i => i.severity === 'ERROR').length === 0,
      issues,
      validatedAt: Date.now()
    });
  }
}
