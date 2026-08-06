import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationProvider,
  ConfigurationProviderException,
  ConfigurationRuntime,
  ConfigurationValidationException,
  createSensitiveAccessRecord,
  createSensitiveConfiguration,
  createSensitiveConfigurationReference,
  createSensitiveConfigurationSnapshot,
  createSensitiveHealth,
  createSensitiveStatistics,
  createSensitiveValuePolicy,
  resetConfigurationProvider,
  resetConfigurationRuntime,
  SecureConfigurationManager,
  SensitiveValueType,
} from '../../src/runtime/config';

describe('Phase 16.3.5 — Frontend Secure Configuration & Sensitive Data Management', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable SensitiveValuePolicy model with defaults', () => {
      const policy = createSensitiveValuePolicy();

      expect(policy.allowRead).toBe(true);
      expect(policy.allowWrite).toBe(true);
      expect(policy.allowExport).toBe(false);
      expect(policy.allowLogging).toBe(false);
      expect(policy.allowRedaction).toBe(true);
      expect(Object.isFrozen(policy)).toBe(true);
    });

    it('should create immutable SensitiveValuePolicy model with custom values', () => {
      const policy = createSensitiveValuePolicy({
        allowRead: false,
        allowWrite: true,
        allowExport: false,
        allowLogging: false,
      });

      expect(policy.allowRead).toBe(false);
      expect(policy.allowExport).toBe(false);
      expect(Object.isFrozen(policy)).toBe(true);
    });

    it('should create immutable SensitiveConfiguration model', () => {
      const config = createSensitiveConfiguration({
        key: 'db.password',
        rawValue: 'secret_123',
        sensitiveType: SensitiveValueType.PASSWORD,
      });

      expect(config.key).toBe('db.password');
      expect(config.rawValue).toBe('secret_123');
      expect(config.sensitiveType).toBe(SensitiveValueType.PASSWORD);
      expect(Object.isFrozen(config)).toBe(true);
      expect(Object.isFrozen(config.policy)).toBe(true);
    });

    it('should create immutable SensitiveConfigurationReference model', () => {
      const ref = createSensitiveConfigurationReference({
        key: 'db.password',
        sensitiveType: SensitiveValueType.PASSWORD,
        redactedValue: '********',
      });

      expect(ref.key).toBe('db.password');
      expect(ref.redactedValue).toBe('********');
      expect(Object.isFrozen(ref)).toBe(true);
    });

    it('should create immutable SensitiveConfigurationSnapshot model', () => {
      const ref = createSensitiveConfigurationReference({ key: 'k1', redactedValue: '****' });
      const snapshot = createSensitiveConfigurationSnapshot({ references: [ref] });

      expect(snapshot.sensitiveCount).toBe(1);
      expect(snapshot.references[0]).toBe(ref);
      expect(Object.isFrozen(snapshot)).toBe(true);
      expect(Object.isFrozen(snapshot.references)).toBe(true);
    });

    it('should create immutable SensitiveAccessRecord, SensitiveStatistics, and SensitiveHealth models', () => {
      const record = createSensitiveAccessRecord({ key: 'k1', action: 'READ', success: true });
      expect(record.action).toBe('READ');
      expect(Object.isFrozen(record)).toBe(true);

      const stats = createSensitiveStatistics({ totalValues: 5, reads: 10 });
      expect(stats.totalValues).toBe(5);
      expect(stats.reads).toBe(10);
      expect(Object.isFrozen(stats)).toBe(true);

      const health = createSensitiveHealth({ healthy: true, totalValues: 5 });
      expect(health.healthy).toBe(true);
      expect(health.totalValues).toBe(5);
      expect(Object.isFrozen(health)).toBe(true);
    });
  });

  describe('2. SecureConfigurationManager Registration, Update & Removal', () => {
    it('should register sensitive value and retrieve raw value', () => {
      const scm = new SecureConfigurationManager();
      scm.register('api.token', 'bearer_xyz_123', SensitiveValueType.TOKEN);

      expect(scm.contains('api.token')).toBe(true);
      expect(scm.getSensitiveValue('api.token')).toBe('bearer_xyz_123');
    });

    it('should reject registration of duplicate sensitive key', () => {
      const scm = new SecureConfigurationManager();
      scm.register('auth.secret', 'sec1', SensitiveValueType.PASSWORD);

      expect(() => scm.register('auth.secret', 'sec2', SensitiveValueType.PASSWORD)).toThrow(
        ConfigurationProviderException,
      );
    });

    it('should reject registration of empty key or null value', () => {
      const scm = new SecureConfigurationManager();
      expect(() => scm.register('   ', 'val')).toThrow(ConfigurationProviderException);
      expect(() => scm.register('key', null as any)).toThrow(ConfigurationProviderException);
    });

    it('should update existing sensitive value', () => {
      const scm = new SecureConfigurationManager();
      scm.register('auth.key', 'old_key', SensitiveValueType.API_KEY);

      scm.update('auth.key', 'new_key_value');
      expect(scm.getSensitiveValue('auth.key')).toBe('new_key_value');
    });

    it('should throw ConfigurationProviderException when updating non-existent key', () => {
      const scm = new SecureConfigurationManager();
      expect(() => scm.update('unknown_key', 'val')).toThrow(ConfigurationProviderException);
    });

    it('should remove sensitive value by key', () => {
      const scm = new SecureConfigurationManager();
      scm.register('temp.secret', 'temp', SensitiveValueType.CUSTOM);

      expect(scm.remove('temp.secret')).toBe(true);
      expect(scm.contains('temp.secret')).toBe(false);
      expect(scm.getSensitiveValue('temp.secret')).toBeUndefined();
    });

    it('should return false when removing non-existent key', () => {
      const scm = new SecureConfigurationManager();
      expect(scm.remove('nonexistent')).toBe(false);
    });

    it('should clear all sensitive values and audit log', () => {
      const scm = new SecureConfigurationManager();
      scm.register('k1', 'v1');
      scm.register('k2', 'v2');

      expect(scm.createSnapshot().sensitiveCount).toBe(2);
      scm.clear();
      expect(scm.createSnapshot().sensitiveCount).toBe(0);
      expect(scm.auditHistory().length).toBe(0);
    });

    it('should return undefined when requesting sensitive value for missing key', () => {
      const scm = new SecureConfigurationManager();
      expect(scm.getSensitiveValue('missing')).toBeUndefined();
      expect(scm.getRedactedValue('missing')).toBeUndefined();
    });
  });

  describe('3. Redaction Engine Rules', () => {
    it('should redact PASSWORD type to ********', () => {
      const scm = new SecureConfigurationManager();
      scm.register('user.pass', 'supersecretpassword123', SensitiveValueType.PASSWORD);

      expect(scm.getRedactedValue('user.pass')).toBe('********');
    });

    it('should redact TOKEN type preserving first 4 characters', () => {
      const scm = new SecureConfigurationManager();
      scm.register('oauth.token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9', SensitiveValueType.TOKEN);

      expect(scm.getRedactedValue('oauth.token')).toBe('eyJh****');
    });

    it('should redact short TOKEN type to ****', () => {
      const scm = new SecureConfigurationManager();
      scm.register('short.token', 'abc', SensitiveValueType.TOKEN);

      expect(scm.getRedactedValue('short.token')).toBe('****');
    });

    it('should redact API_KEY type preserving first 4 and last 4 characters', () => {
      const scm = new SecureConfigurationManager();
      scm.register('stripe.key', 'fake_api_key_0000000000000000000', SensitiveValueType.API_KEY);

      expect(scm.getRedactedValue('stripe.key')).toBe('fake...0000');
    });

    it('should redact short API_KEY type to ****', () => {
      const scm = new SecureConfigurationManager();
      scm.register('short.key', '12345', SensitiveValueType.API_KEY);

      expect(scm.getRedactedValue('short.key')).toBe('****');
    });

    it('should redact CERTIFICATE type to <CERTIFICATE>', () => {
      const scm = new SecureConfigurationManager();
      scm.register('ssl.cert', '-----BEGIN CERTIFICATE-----...', SensitiveValueType.CERTIFICATE);

      expect(scm.getRedactedValue('ssl.cert')).toBe('<CERTIFICATE>');
    });

    it('should redact PRIVATE_KEY type to <PRIVATE_KEY>', () => {
      const scm = new SecureConfigurationManager();
      scm.register('rsa.key', '-----BEGIN RSA PRIVATE KEY-----...', SensitiveValueType.PRIVATE_KEY);

      expect(scm.getRedactedValue('rsa.key')).toBe('<PRIVATE_KEY>');
    });

    it('should redact CONNECTION_STRING type to <CONNECTION_STRING>', () => {
      const scm = new SecureConfigurationManager();
      scm.register('db.url', 'postgres://user:pass@localhost:5432/db', SensitiveValueType.CONNECTION_STRING);

      expect(scm.getRedactedValue('db.url')).toBe('<CONNECTION_STRING>');
    });

    it('should redact CUSTOM type to [REDACTED]', () => {
      const scm = new SecureConfigurationManager();
      scm.register('custom.secret', 'mycustomdata', SensitiveValueType.CUSTOM);

      expect(scm.getRedactedValue('custom.secret')).toBe('[REDACTED]');
    });
  });

  describe('4. Policy Enforcement & Audit Access Logging', () => {
    it('should block reading sensitive value when allowRead policy is false', () => {
      const scm = new SecureConfigurationManager();
      scm.register(
        'restricted.key',
        'top_secret',
        SensitiveValueType.PASSWORD,
        createSensitiveValuePolicy({ allowRead: false }),
      );

      expect(() => scm.getSensitiveValue('restricted.key')).toThrow(ConfigurationValidationException);
      expect(scm.statistics().blockedAccesses).toBe(1);
    });

    it('should allow redaction even when allowRead policy is false', () => {
      const scm = new SecureConfigurationManager();
      scm.register(
        'restricted.key',
        'top_secret',
        SensitiveValueType.PASSWORD,
        createSensitiveValuePolicy({ allowRead: false }),
      );

      expect(scm.getRedactedValue('restricted.key')).toBe('********');
    });

    it('should log audit history for REGISTER, READ, REDACT, UPDATE, and REMOVE actions', () => {
      const scm = new SecureConfigurationManager();
      scm.register('audit.key', 'v1', SensitiveValueType.CUSTOM);
      scm.getSensitiveValue('audit.key');
      scm.getRedactedValue('audit.key');
      scm.update('audit.key', 'v2');
      scm.remove('audit.key');

      const history = scm.auditHistory();
      expect(history.length).toBe(5);
      expect(history[0].action).toBe('REGISTER');
      expect(history[1].action).toBe('READ');
      expect(history[2].action).toBe('REDACT');
      expect(history[3].action).toBe('UPDATE');
      expect(history[4].action).toBe('REMOVE');
    });

    it('should track statistics and health telemetry in SecureConfigurationManager', () => {
      const scm = new SecureConfigurationManager();
      scm.register('k1', 'v1');
      scm.getSensitiveValue('k1');
      scm.getRedactedValue('k1');

      const stats = scm.statistics();
      expect(stats.totalValues).toBe(1);
      expect(stats.reads).toBe(1);
      expect(stats.redactions).toBe(1);

      const health = scm.health();
      expect(health.healthy).toBe(true);
      expect(health.totalValues).toBe(1);
    });
  });

  describe('5. Provider & Runtime Delegation Integration & Diagnostics Protection', () => {
    it('should return redacted values when querying sensitive values via provider getEntry() and getAll()', () => {
      const provider = new ConfigurationProvider();
      provider.registerSensitiveValue('db.pass', 'secret_pass_123', SensitiveValueType.PASSWORD);

      expect(provider.getSensitiveValue('db.pass')).toBe('secret_pass_123');

      const entry = provider.getEntry('db.pass');
      expect(entry).toBeDefined();
      expect(entry?.value).toBe('********');

      const all = provider.getAll();
      expect(all['db.pass']).toBe('********');
    });

    it('should delegate sensitive APIs through ConfigurationRuntime coordinator', () => {
      const runtime = new ConfigurationRuntime();
      runtime.registerSensitiveValue('api.secret', 'fake_api_key_1234567890', SensitiveValueType.API_KEY);

      expect(runtime.getSensitiveValue('api.secret')).toBe('fake_api_key_1234567890');
      expect(runtime.getRedactedValue('api.secret')).toBe('fake...7890');

      const snapshot = runtime.createSensitiveSnapshot();
      expect(snapshot.sensitiveCount).toBe(1);
      expect(snapshot.references[0].redactedValue).toBe('fake...7890');

      expect(runtime.sensitiveStatistics().totalValues).toBe(1);
      expect(runtime.sensitiveHealth().healthy).toBe(true);

      expect(runtime.removeSensitiveValue('api.secret')).toBe(true);
      expect(runtime.createSensitiveSnapshot().sensitiveCount).toBe(0);
    });

    it('should protect provider diagnostics() by containing ZERO raw sensitive values', () => {
      const provider = new ConfigurationProvider();
      provider.registerSensitiveValue('master.key', 'raw_secret_key_never_expose', SensitiveValueType.PASSWORD);

      const diag = provider.diagnostics();
      const diagStr = JSON.stringify(diag);

      expect(diagStr).not.toContain('raw_secret_key_never_expose');
      expect(diag.sensitiveSnapshot).toBeDefined();
      expect(diag.sensitiveSnapshot?.references[0].redactedValue).toBe('********');
      expect(diag.sensitiveStats).toBeDefined();
      expect(diag.sensitiveHealth).toBeDefined();
    });
  });
});
