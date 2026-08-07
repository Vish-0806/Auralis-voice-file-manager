import { beforeEach, describe, expect, it } from 'vitest';
import {
  CommandExecutionStatus,
  CommandExecutor,
  CommandPipeline,
  CommandProvider,
  CommandRegistry,
  CommandRuntime,
  CommandValidator,
  PermissionManager,
  PolicyManager,
  createCommandPermission,
  createExecutionPolicy,
  createPermissionDiagnostics,
  createPermissionHealth,
  createPermissionResult,
  createPermissionStatistics,
  createPolicyDecision,
  createPolicyDiagnostics,
  createPolicyHealth,
  createPolicyRule,
  createPolicyStatistics,
  createValidationDiagnostics,
  createValidationHealth,
  createValidationIssue,
  createValidationResult,
  createValidationRule,
  createValidationStatistics,
  getCommandRuntime,
  resetCommandProvider,
  resetCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.5 — Frontend Command Validation, Permissions & Policy Engine', () => {
  let registry: CommandRegistry;
  let executor: CommandExecutor;
  let validator: CommandValidator;
  let permissionManager: PermissionManager;
  let policyManager: PolicyManager;
  let pipeline: CommandPipeline;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();

    registry = new CommandRegistry();
    executor = new CommandExecutor(registry);
    validator = new CommandValidator(registry);
    permissionManager = new PermissionManager();
    policyManager = new PolicyManager();
    pipeline = new CommandPipeline(
      executor,
      undefined,
      undefined,
      undefined,
      registry,
      validator,
      permissionManager,
      policyManager,
    );
  });

  describe('1. Immutable Domain Models & Factory Functions', () => {
    it('should create immutable CommandPermission model', () => {
      const perm = createCommandPermission({
        name: 'fs.write',
        scope: 'workspace',
        roles: ['admin', 'editor'],
      });

      expect(perm.name).toBe('fs.write');
      expect(perm.scope).toBe('workspace');
      expect(perm.roles).toEqual(['admin', 'editor']);
      expect(perm.enabled).toBe(true);
      expect(Object.isFrozen(perm)).toBe(true);
    });

    it('should create immutable PermissionResult model', () => {
      const res = createPermissionResult({ granted: false, reason: 'Lacks role' });
      expect(res.granted).toBe(false);
      expect(res.reason).toBe('Lacks role');
      expect(Object.isFrozen(res)).toBe(true);
    });

    it('should create immutable ValidationIssue model', () => {
      const issue = createValidationIssue({
        severity: 'error',
        code: 'MISSING_PARAM',
        message: 'Parameter filepath is required',
        field: 'filepath',
      });

      expect(issue.severity).toBe('error');
      expect(issue.field).toBe('filepath');
      expect(Object.isFrozen(issue)).toBe(true);
    });

    it('should create immutable ValidationRule model', () => {
      const rule = createValidationRule({
        name: 'CheckFileExt',
        validate: () => null,
      });

      expect(rule.name).toBe('CheckFileExt');
      expect(rule.ruleId).toBeDefined();
      expect(Object.isFrozen(rule)).toBe(true);
    });

    it('should create immutable ValidationResult model', () => {
      const res = createValidationResult({
        commandId: 'file_delete',
        valid: true,
      });

      expect(res.commandId).toBe('file_delete');
      expect(res.valid).toBe(true);
      expect(Object.isFrozen(res)).toBe(true);
    });

    it('should create immutable PolicyRule & ExecutionPolicy models', () => {
      const prule = createPolicyRule({
        name: 'TimeRule',
        policyId: 'p1',
        condition: () => true,
      });

      const policy = createExecutionPolicy({
        name: 'WorkHoursPolicy',
        evaluate: () => createPolicyDecision({ allowed: true }),
      });

      expect(prule.name).toBe('TimeRule');
      expect(policy.name).toBe('WorkHoursPolicy');
      expect(Object.isFrozen(prule)).toBe(true);
      expect(Object.isFrozen(policy)).toBe(true);
    });

    it('should create immutable Telemetry & Diagnostics models', () => {
      const valDiag = createValidationDiagnostics({
        statistics: createValidationStatistics(),
        health: createValidationHealth(),
      });

      const permDiag = createPermissionDiagnostics({
        statistics: createPermissionStatistics(),
        health: createPermissionHealth(),
      });

      const polDiag = createPolicyDiagnostics({
        statistics: createPolicyStatistics(),
        health: createPolicyHealth(),
      });

      expect(valDiag.statistics).toBeDefined();
      expect(permDiag.health).toBeDefined();
      expect(polDiag.statistics).toBeDefined();
      expect(Object.isFrozen(valDiag)).toBe(true);
      expect(Object.isFrozen(permDiag)).toBe(true);
      expect(Object.isFrozen(polDiag)).toBe(true);
    });
  });

  describe('2. Command Validator Engine', () => {
    it('should return error for unregistered command', async () => {
      const res = await validator.validate({ commandId: 'unregistered_cmd' });
      expect(res.valid).toBe(false);
      expect(res.issues.some((i) => i.code === 'UNKNOWN_COMMAND')).toBe(true);
    });

    it('should return error for disabled command', async () => {
      registry.registerCommand({ id: 'cmd_off', displayName: 'Off Cmd', enabled: false });
      const res = await validator.validate({ commandId: 'cmd_off' });
      expect(res.valid).toBe(false);
      expect(res.issues.some((i) => i.code === 'COMMAND_DISABLED')).toBe(true);
    });

    it('should return warning for deprecated command', async () => {
      registry.registerCommand({ id: 'cmd_old', displayName: 'Old Cmd', deprecated: true });
      const res = await validator.validate({ commandId: 'cmd_old' });
      expect(res.valid).toBe(true);
      expect(res.issues.some((i) => i.code === 'COMMAND_DEPRECATED')).toBe(true);
    });

    it('should validate missing required parameters and invalid parameter types', async () => {
      registry.registerCommand({
        id: 'file_save',
        displayName: 'Save File',
        parameters: [
          { name: 'filename', type: 'string', required: true },
          { name: 'bytes', type: 'number', required: false },
        ],
      });

      const resMissing = await validator.validate({ commandId: 'file_save', args: {} });
      expect(resMissing.valid).toBe(false);
      expect(resMissing.issues.some((i) => i.code === 'MISSING_REQUIRED_PARAMETER')).toBe(true);

      const resInvalidType = await validator.validate({
        commandId: 'file_save',
        args: { filename: 'test.txt', bytes: 'not_a_number' },
      });
      expect(resInvalidType.valid).toBe(false);
      expect(resInvalidType.issues.some((i) => i.code === 'INVALID_PARAMETER_TYPE')).toBe(true);
    });

    it('should execute custom validation rules', async () => {
      registry.registerCommand({ id: 'custom_cmd', displayName: 'Custom Cmd' });

      validator.registerValidationRule({
        name: 'BlockFoo',
        validate: (req) => {
          if (req.args?.foo === 'bar') {
            return createValidationIssue({
              severity: 'error',
              code: 'FOO_NOT_ALLOWED',
              message: 'Foo bar is prohibited',
            });
          }
          return null;
        },
      });

      const resBlocked = await validator.validate({ commandId: 'custom_cmd', args: { foo: 'bar' } });
      expect(resBlocked.valid).toBe(false);

      const resAllowed = await validator.validate({ commandId: 'custom_cmd', args: { foo: 'baz' } });
      expect(resAllowed.valid).toBe(true);
    });
  });

  describe('3. Permission Manager Engine', () => {
    it('should grant and check permissions by role', () => {
      permissionManager.registerPermission({
        permissionId: 'delete_repo',
        name: 'Delete Repository',
        roles: ['admin'],
      });

      const checkAdmin = permissionManager.hasPermission('admin', 'delete_repo');
      expect(checkAdmin.granted).toBe(true);

      const checkUser = permissionManager.hasPermission('guest', 'delete_repo');
      expect(checkUser.granted).toBe(false);
    });

    it('should grant and revoke direct user permissions', () => {
      permissionManager.registerPermission({
        permissionId: 'export_data',
        name: 'Export Data',
      });

      expect(permissionManager.hasPermission('user_42', 'export_data').granted).toBe(false);

      permissionManager.grantPermission('user_42', 'export_data');
      expect(permissionManager.hasPermission('user_42', 'export_data').granted).toBe(true);

      permissionManager.revokePermission('user_42', 'export_data');
      expect(permissionManager.hasPermission('user_42', 'export_data').granted).toBe(false);
    });
  });

  describe('4. Policy Manager Engine', () => {
    it('should evaluate registered execution policies', async () => {
      policyManager.registerPolicy({
        name: 'RestrictProdEnv',
        evaluate: (req) => {
          if (req.metadata?.env === 'production' && req.commandId === 'drop_db') {
            return createPolicyDecision({
              allowed: false,
              reason: 'Cannot drop database in production',
            });
          }
          return createPolicyDecision({ allowed: true });
        },
      });

      const decisionDenied = await policyManager.evaluatePolicy({
        commandId: 'drop_db',
        metadata: { env: 'production' },
      });
      expect(decisionDenied.allowed).toBe(false);
      expect(decisionDenied.reason).toContain('production');

      const decisionAllowed = await policyManager.evaluatePolicy({
        commandId: 'drop_db',
        metadata: { env: 'development' },
      });
      expect(decisionAllowed.allowed).toBe(true);
    });
  });

  describe('5. Integrated Pipeline Validation Flow', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'secure_cmd',
        displayName: 'Secure Command',
        permission: 'secure_access',
        parameters: [{ name: 'key', type: 'string', required: true }],
      });

      executor.registerHandler('secure_cmd', () => 'secret_data');
      permissionManager.registerPermission({
        permissionId: 'secure_access',
        name: 'Secure Access',
        roles: ['admin'],
      });
    });

    it('should short-circuit pipeline when validation fails', async () => {
      const pipeRes = await pipeline.executePipeline({
        commandId: 'secure_cmd',
        args: {}, // missing required key parameter
      });

      expect(pipeRes.executionResult.status).toBe(CommandExecutionStatus.VALIDATION_FAILED);
      expect(pipeRes.executionResult.error?.code).toBe('MISSING_REQUIRED_PARAMETER');
    });

    it('should short-circuit pipeline when permission check fails', async () => {
      const pipeRes = await pipeline.executePipeline({
        commandId: 'secure_cmd',
        args: { key: 'valid_key' },
        userId: 'guest', // guest lacks secure_access permission
      });

      expect(pipeRes.executionResult.status).toBe(CommandExecutionStatus.REJECTED);
      expect(pipeRes.executionResult.error?.code).toBe('PERMISSION_DENIED');
    });

    it('should short-circuit pipeline when policy check fails', async () => {
      policyManager.registerPolicy({
        name: 'BlockAll',
        evaluate: () => createPolicyDecision({ allowed: false, reason: 'Blocked by policy' }),
      });

      const pipeRes = await pipeline.executePipeline({
        commandId: 'secure_cmd',
        args: { key: 'valid_key' },
        userId: 'admin',
      });

      expect(pipeRes.executionResult.status).toBe(CommandExecutionStatus.REJECTED);
      expect(pipeRes.executionResult.error?.code).toBe('POLICY_DENIED');
    });

    it('should execute successfully when validation, permission, and policy all pass', async () => {
      const pipeRes = await pipeline.executePipeline<string>({
        commandId: 'secure_cmd',
        args: { key: 'valid_key' },
        userId: 'admin',
      });

      expect(pipeRes.executionResult.status).toBe(CommandExecutionStatus.COMPLETED);
      expect(pipeRes.executionResult.value).toBe('secret_data');
    });
  });

  describe('6. Provider & Runtime Delegation Integration', () => {
    it('should delegate validation, permission, and policy APIs through CommandProvider and CommandRuntime', async () => {
      const provider = new CommandProvider();
      provider.initialize();
      const runtime = new CommandRuntime(provider);

      runtime.registerPermission({
        permissionId: 'perm_run',
        name: 'Run Permission',
        roles: ['developer'],
      });

      runtime.grantPermission('dev_user', 'perm_run');
      expect(runtime.hasPermission('dev_user', 'perm_run').granted).toBe(true);

      runtime.registerValidationRule({
        name: 'Rule1',
        validate: () => null,
      });
      expect(runtime.listValidationRules().length).toBe(1);

      runtime.registerPolicy({
        name: 'Policy1',
        evaluate: () => createPolicyDecision({ allowed: true }),
      });
      expect(runtime.listPolicies().length).toBe(1);
    });

    it('should include validation, permission, and policy telemetry in runtime diagnostics()', () => {
      const runtime = getCommandRuntime();
      runtime.initialize();

      const diag = runtime.diagnostics();
      expect(diag.validationDiagnostics).toBeDefined();
      expect(diag.permissionDiagnostics).toBeDefined();
      expect(diag.policyDiagnostics).toBeDefined();
    });
  });
});
