import { PluginManifestError } from '../errors/PluginErrors';
import type {
  PluginManifest,
  PluginManifestValidationResult,
  PluginManifestValidationIssue,
  PluginDependencyDeclaration,
  PluginCapabilityDeclaration
} from '../models/manifest';
import { SemVerValidator } from './SemVerValidator';

export class PluginManifestValidator {
  
  private static performValidation(input: unknown): { manifest: PluginManifest | null; issues: PluginManifestValidationIssue[] } {
    const issues: PluginManifestValidationIssue[] = [];
    
    if (input === null || input === undefined) {
      issues.push({
        code: 'INVALID_INPUT',
        path: '',
        severity: 'error',
        message: 'Manifest input cannot be null or undefined'
      });
      return { manifest: null, issues };
    }

    let parsedObj: any = input;
    if (typeof input === 'string') {
      try {
        parsedObj = JSON.parse(input);
      } catch (err: any) {
        issues.push({
          code: 'MALFORMED_JSON',
          path: '',
          severity: 'error',
          message: `Failed to parse JSON: ${err.message}`
        });
        return { manifest: null, issues };
      }
    }

    if (typeof parsedObj !== 'object' || parsedObj === null) {
      issues.push({
        code: 'INVALID_TYPE',
        path: '',
        severity: 'error',
        message: 'Manifest must be an object'
      });
      return { manifest: null, issues };
    }

    // 1. Validate ID
    if (parsedObj.id === undefined || parsedObj.id === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'id',
        severity: 'error',
        message: "Required field 'id' is missing"
      });
    } else if (typeof parsedObj.id !== 'string') {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'id',
        severity: 'error',
        message: "'id' must be a string"
      });
    } else {
      const trimmedId = parsedObj.id.trim();
      if (trimmedId.length === 0) {
        issues.push({
          code: 'EMPTY_FIELD',
          path: 'id',
          severity: 'error',
          message: "'id' cannot be empty"
        });
      } else if (trimmedId.includes(' ')) {
        issues.push({
          code: 'INVALID_FORMAT',
          path: 'id',
          severity: 'error',
          message: "'id' cannot contain spaces"
        });
      } else if (!/^[a-zA-Z0-9._-]+$/.test(trimmedId)) {
        issues.push({
          code: 'INVALID_FORMAT',
          path: 'id',
          severity: 'error',
          message: "'id' must be alphanumeric, dots, hyphens, or underscores only"
        });
      }
    }

    // 2. Validate Name
    if (parsedObj.name === undefined || parsedObj.name === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'name',
        severity: 'error',
        message: "Required field 'name' is missing"
      });
    } else if (typeof parsedObj.name !== 'string') {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'name',
        severity: 'error',
        message: "'name' must be a string"
      });
    } else if (parsedObj.name.trim().length === 0) {
      issues.push({
        code: 'EMPTY_FIELD',
        path: 'name',
        severity: 'error',
        message: "'name' cannot be empty"
      });
    }

    // 3. Validate Version
    if (parsedObj.version === undefined || parsedObj.version === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'version',
        severity: 'error',
        message: "Required field 'version' is missing"
      });
    } else if (typeof parsedObj.version !== 'string') {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'version',
        severity: 'error',
        message: "'version' must be a string"
      });
    } else {
      const trimmedVersion = parsedObj.version.trim();
      if (trimmedVersion.length === 0) {
        issues.push({
          code: 'EMPTY_FIELD',
          path: 'version',
          severity: 'error',
          message: "'version' cannot be empty"
        });
      } else if (!SemVerValidator.isValid(trimmedVersion)) {
        issues.push({
          code: 'INVALID_SEMVER',
          path: 'version',
          severity: 'error',
          message: `'version' must be a valid SemVer syntax (found: ${trimmedVersion})`
        });
      }
    }

    // 4. Validate Description
    if (parsedObj.description !== undefined && parsedObj.description !== null) {
      if (typeof parsedObj.description !== 'string') {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'description',
          severity: 'error',
          message: "'description' must be a string"
        });
      }
    }

    // 5. Validate Author
    if (parsedObj.author === undefined || parsedObj.author === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'author',
        severity: 'error',
        message: "Required field 'author' is missing"
      });
    } else if (typeof parsedObj.author === 'string') {
      if (parsedObj.author.trim().length === 0) {
        issues.push({
          code: 'EMPTY_FIELD',
          path: 'author',
          severity: 'error',
          message: "'author' string cannot be empty"
        });
      }
    } else if (typeof parsedObj.author === 'object') {
      const authorObj = parsedObj.author as Record<string, unknown>;
      if (!authorObj.name || typeof authorObj.name !== 'string' || authorObj.name.trim().length === 0) {
        issues.push({
          code: 'INVALID_AUTHOR',
          path: 'author.name',
          severity: 'error',
          message: "Author object must have a non-empty 'name' string"
        });
      }
      if (authorObj.email !== undefined && typeof authorObj.email !== 'string') {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'author.email',
          severity: 'error',
          message: "Author 'email' must be a string"
        });
      }
      if (authorObj.url !== undefined && typeof authorObj.url !== 'string') {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'author.url',
          severity: 'error',
          message: "Author 'url' must be a string"
        });
      }
    } else {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'author',
        severity: 'error',
        message: "'author' must be a string or a PluginAuthor object"
      });
    }

    // 6. Validate SchemaVersion
    if (parsedObj.schemaVersion === undefined || parsedObj.schemaVersion === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'schemaVersion',
        severity: 'error',
        message: "Required field 'schemaVersion' is missing"
      });
    } else if (typeof parsedObj.schemaVersion !== 'string') {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'schemaVersion',
        severity: 'error',
        message: "'schemaVersion' must be a string"
      });
    } else if (parsedObj.schemaVersion.trim().length === 0) {
      issues.push({
        code: 'EMPTY_FIELD',
        path: 'schemaVersion',
        severity: 'error',
        message: "'schemaVersion' cannot be empty"
      });
    }

    // 7. Validate EntryPoint
    if (parsedObj.entryPoint === undefined || parsedObj.entryPoint === null) {
      issues.push({
        code: 'MISSING_FIELD',
        path: 'entryPoint',
        severity: 'error',
        message: "Required field 'entryPoint' is missing"
      });
    } else if (typeof parsedObj.entryPoint !== 'string') {
      issues.push({
        code: 'INVALID_TYPE',
        path: 'entryPoint',
        severity: 'error',
        message: "'entryPoint' must be a string"
      });
    } else if (parsedObj.entryPoint.trim().length === 0) {
      issues.push({
        code: 'EMPTY_FIELD',
        path: 'entryPoint',
        severity: 'error',
        message: "'entryPoint' cannot be empty"
      });
    }

    // 8. Validate Dependencies
    const dependencies: PluginDependencyDeclaration[] = [];
    if (parsedObj.dependencies !== undefined && parsedObj.dependencies !== null) {
      if (!Array.isArray(parsedObj.dependencies)) {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'dependencies',
          severity: 'error',
          message: "'dependencies' must be an array"
        });
      } else {
        const seenDepIds = new Set<string>();
        parsedObj.dependencies.forEach((dep: any, index: number) => {
          if (typeof dep !== 'object' || dep === null) {
            issues.push({
              code: 'INVALID_TYPE',
              path: `dependencies[${index}]`,
              severity: 'error',
              message: `Dependency at index ${index} must be an object`
            });
            return;
          }
          
          let validDep = true;
          if (!dep.id || typeof dep.id !== 'string' || dep.id.trim().length === 0) {
            issues.push({
              code: 'INVALID_DEPENDENCY',
              path: `dependencies[${index}].id`,
              severity: 'error',
              message: "Dependency must have a non-empty 'id' string"
            });
            validDep = false;
          } else if (dep.id.includes(' ')) {
            issues.push({
              code: 'INVALID_DEPENDENCY',
              path: `dependencies[${index}].id`,
              severity: 'error',
              message: "Dependency 'id' cannot contain spaces"
            });
            validDep = false;
          }
          
          if (!dep.versionRange || typeof dep.versionRange !== 'string' || dep.versionRange.trim().length === 0) {
            issues.push({
              code: 'INVALID_DEPENDENCY',
              path: `dependencies[${index}].versionRange`,
              severity: 'error',
              message: "Dependency must have a non-empty 'versionRange' string"
            });
            validDep = false;
          } else if (!SemVerValidator.isValidRange(dep.versionRange)) {
            issues.push({
              code: 'INVALID_VERSION_RANGE',
              path: `dependencies[${index}].versionRange`,
              severity: 'error',
              message: `Dependency version range syntax is invalid (found: ${dep.versionRange})`
            });
            validDep = false;
          }

          if (dep.optional !== undefined && typeof dep.optional !== 'boolean') {
            issues.push({
              code: 'INVALID_TYPE',
              path: `dependencies[${index}].optional`,
              severity: 'error',
              message: "Dependency 'optional' must be a boolean"
            });
            validDep = false;
          }

          if (validDep) {
            if (seenDepIds.has(dep.id)) {
              issues.push({
                code: 'DUPLICATE_DEPENDENCY',
                path: `dependencies[${index}].id`,
                severity: 'error',
                message: `Duplicate dependency declaration for plugin '${dep.id}'`
              });
            }
            seenDepIds.add(dep.id);
            dependencies.push({
              id: dep.id,
              versionRange: dep.versionRange,
              optional: dep.optional
            });
          }
        });
      }
    }

    // 9. Validate Capabilities
    const capabilities: PluginCapabilityDeclaration[] = [];
    if (parsedObj.capabilities !== undefined && parsedObj.capabilities !== null) {
      if (!Array.isArray(parsedObj.capabilities)) {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'capabilities',
          severity: 'error',
          message: "'capabilities' must be an array"
        });
      } else {
        const seenCapTypes = new Set<string>();
        parsedObj.capabilities.forEach((cap: any, index: number) => {
          if (typeof cap !== 'object' || cap === null) {
            issues.push({
              code: 'INVALID_TYPE',
              path: `capabilities[${index}]`,
              severity: 'error',
              message: `Capability at index ${index} must be an object`
            });
            return;
          }

          let validCap = true;
          if (!cap.type || typeof cap.type !== 'string' || cap.type.trim().length === 0) {
            issues.push({
              code: 'INVALID_CAPABILITY',
              path: `capabilities[${index}].type`,
              severity: 'error',
              message: "Capability must have a non-empty 'type' string"
            });
            validCap = false;
          }

          if (cap.properties !== undefined && (typeof cap.properties !== 'object' || cap.properties === null)) {
            issues.push({
              code: 'INVALID_TYPE',
              path: `capabilities[${index}].properties`,
              severity: 'error',
              message: "Capability 'properties' must be an object"
            });
            validCap = false;
          }

          if (validCap) {
            if (seenCapTypes.has(cap.type)) {
              issues.push({
                code: 'DUPLICATE_CAPABILITY',
                path: `capabilities[${index}].type`,
                severity: 'error',
                message: `Duplicate capability declaration for type '${cap.type}'`
              });
            }
            seenCapTypes.add(cap.type);
            capabilities.push({
              type: cap.type,
              properties: cap.properties ? { ...cap.properties } : {}
            });
          }
        });
      }
    }

    // 10. Validate Optional Metadata
    let metadata: Record<string, unknown> | undefined = undefined;
    if (parsedObj.metadata !== undefined && parsedObj.metadata !== null) {
      if (typeof parsedObj.metadata !== 'object') {
        issues.push({
          code: 'INVALID_TYPE',
          path: 'metadata',
          severity: 'error',
          message: "'metadata' must be an object"
        });
      } else {
        metadata = { ...parsedObj.metadata };
      }
    }

    const hasErrors = issues.some(issue => issue.severity === 'error');
    if (hasErrors) {
      return { manifest: null, issues };
    }

    // Build the manifest object
    const manifest: PluginManifest = {
      id: parsedObj.id,
      name: parsedObj.name,
      version: parsedObj.version,
      description: parsedObj.description,
      author: typeof parsedObj.author === 'string' ? parsedObj.author : {
        name: parsedObj.author.name,
        email: parsedObj.author.email,
        url: parsedObj.author.url
      },
      schemaVersion: parsedObj.schemaVersion,
      entryPoint: parsedObj.entryPoint,
      dependencies,
      capabilities,
      metadata
    };

    return { manifest, issues };
  }

  public static validate(manifest: unknown): PluginManifestValidationResult {
    const { issues } = this.performValidation(manifest);
    const hasErrors = issues.some(issue => issue.severity === 'error');
    
    // freezedeep
    const result: PluginManifestValidationResult = {
      valid: !hasErrors,
      issues
    };
    
    return this.freezeDeep(result);
  }

  public static parse(input: unknown): PluginManifest {
    const { manifest, issues } = this.performValidation(input);
    const hasErrors = issues.some(issue => issue.severity === 'error');
    
    if (hasErrors || !manifest) {
      const errorMsgs = issues.map(issue => `[${issue.code}] at ${issue.path || 'root'}: ${issue.message}`).join('; ');
      throw new PluginManifestError(`Manifest parsing failed: ${errorMsgs}`);
    }
    
    return this.freezeDeep(manifest);
  }

  private static freezeDeep<T>(value: T): T {
    if (Object.isFrozen(value)) {
      return value;
    }

    if (Array.isArray(value)) {
      const arrayValue = value.map((item) => this.freezeDeep(item));
      return Object.freeze(arrayValue) as T;
    }

    if (value && typeof value === 'object') {
      const objectValue = value as Record<string, unknown>;
      const copy: Record<string, unknown> = {};
      Object.keys(objectValue).forEach((key) => {
        copy[key] = this.freezeDeep(objectValue[key]);
      });
      return Object.freeze(copy) as unknown as T;
    }

    return value;
  }
}
