import { beforeEach, describe, expect, it } from 'vitest';
import {
  ConfigurationProvider,
  ConfigurationProviderException,
  ConfigurationRuntime,
  ConfigurationSchemaManager,
  ConfigurationSourcePriority,
  ConfigurationValidationException,
  createConfigurationConstraint,
  createConfigurationDefinition,
  createConfigurationError,
  createConfigurationResolutionResult,
  createConfigurationSchema,
  createConfigurationValidationResult,
  createConfigurationWarning,
  createResolutionStatistics,
  createValidationStatistics,
  MemoryConfigurationSource,
  resetConfigurationProvider,
  resetConfigurationRuntime,
} from '../../src/runtime/config';

describe('Phase 16.3.3 — Frontend Configuration Validation & Schema Engine', () => {
  beforeEach(() => {
    resetConfigurationRuntime();
    resetConfigurationProvider();
  });

  describe('1. Immutable Models & Factory Functions', () => {
    it('should create immutable ConfigurationConstraint model', () => {
      const constraint = createConfigurationConstraint({
        minValue: 10,
        maxValue: 100,
        minLength: 2,
        maxLength: 20,
        regexPattern: '^[a-z]+$',
        allowedValues: ['a', 'b'],
      });

      expect(constraint.minValue).toBe(10);
      expect(constraint.maxValue).toBe(100);
      expect(constraint.regexPattern).toBe('^[a-z]+$');
      expect(Object.isFrozen(constraint)).toBe(true);
      expect(Object.isFrozen(constraint.allowedValues)).toBe(true);
    });

    it('should create immutable ConfigurationDefinition model', () => {
      const def = createConfigurationDefinition({
        key: 'server.port',
        expectedType: 'number',
        defaultValue: 8080,
        required: true,
      });

      expect(def.key).toBe('server.port');
      expect(def.expectedType).toBe('number');
      expect(def.defaultValue).toBe(8080);
      expect(def.required).toBe(true);
      expect(Object.isFrozen(def)).toBe(true);
    });

    it('should create immutable ConfigurationSchema model', () => {
      const def = createConfigurationDefinition({ key: 'k1', expectedType: 'string' });
      const schema = createConfigurationSchema({
        schemaName: 'ServerSchema',
        definitions: { k1: def },
      });

      expect(schema.schemaName).toBe('ServerSchema');
      expect(schema.definitions.k1).toBe(def);
      expect(Object.isFrozen(schema)).toBe(true);
      expect(Object.isFrozen(schema.definitions)).toBe(true);
    });

    it('should create immutable ConfigurationError and ConfigurationWarning models', () => {
      const err = createConfigurationError({ key: 'k1', message: 'Missing key' });
      expect(err.key).toBe('k1');
      expect(err.code).toBe('VALIDATION_ERROR');
      expect(Object.isFrozen(err)).toBe(true);

      const warn = createConfigurationWarning({ key: 'k2', message: 'Deprecated key' });
      expect(warn.key).toBe('k2');
      expect(warn.code).toBe('VALIDATION_WARNING');
      expect(Object.isFrozen(warn)).toBe(true);
    });

    it('should create immutable ConfigurationValidationResult and ConfigurationResolutionResult', () => {
      const res = createConfigurationValidationResult({ valid: true });
      expect(res.valid).toBe(true);
      expect(Object.isFrozen(res)).toBe(true);

      const resResult = createConfigurationResolutionResult({ key: 'k1', value: 42, converted: true });
      expect(resResult.key).toBe('k1');
      expect(resResult.value).toBe(42);
      expect(resResult.converted).toBe(true);
      expect(Object.isFrozen(resResult)).toBe(true);
    });

    it('should create immutable ValidationStatistics and ResolutionStatistics models', () => {
      const vStats = createValidationStatistics({ validations: 5 });
      expect(vStats.validations).toBe(5);
      expect(Object.isFrozen(vStats)).toBe(true);

      const rStats = createResolutionStatistics({ resolutions: 10 });
      expect(rStats.resolutions).toBe(10);
      expect(Object.isFrozen(rStats)).toBe(true);
    });
  });

  describe('2. ConfigurationSchemaManager Engine', () => {
    it('should register schema and retrieve by name', () => {
      const manager = new ConfigurationSchemaManager();
      const schema = createConfigurationSchema({ schemaName: 'AppSchema' });

      manager.registerSchema(schema);
      expect(manager.getSchema('AppSchema')).toBe(schema);
      expect(manager.contains('AppSchema')).toBe(true);
    });

    it('should reject registration of duplicate schema name', () => {
      const manager = new ConfigurationSchemaManager();
      const s1 = createConfigurationSchema({ schemaName: 'AppSchema' });
      const s2 = createConfigurationSchema({ schemaName: 'AppSchema' });

      manager.registerSchema(s1);
      expect(() => manager.registerSchema(s2)).toThrow(ConfigurationProviderException);
    });

    it('should reject null or empty schema name', () => {
      const manager = new ConfigurationSchemaManager();
      expect(() => manager.registerSchema(null as any)).toThrow(ConfigurationProviderException);
      expect(() => manager.registerSchema(createConfigurationSchema({ schemaName: '   ' }))).toThrow(
        ConfigurationProviderException,
      );
    });

    it('should unregister schema by name', () => {
      const manager = new ConfigurationSchemaManager();
      const schema = createConfigurationSchema({ schemaName: 'AppSchema' });

      manager.registerSchema(schema);
      expect(manager.unregisterSchema('AppSchema')).toBe(true);
      expect(manager.getSchema('AppSchema')).toBeUndefined();
    });

    it('should return false when unregistering non-existent schema', () => {
      const manager = new ConfigurationSchemaManager();
      expect(manager.unregisterSchema('NonExistent')).toBe(false);
    });

    it('should lookup definition across all registered schemas', () => {
      const manager = new ConfigurationSchemaManager();
      const def = createConfigurationDefinition({ key: 'db.port', expectedType: 'number' });
      const schema = createConfigurationSchema({ schemaName: 'DbSchema', definitions: { 'db.port': def } });

      manager.registerSchema(schema);
      expect(manager.getDefinition('db.port')).toBe(def);
      expect(manager.getDefinition('unknown.key')).toBeUndefined();
    });

    it('should clear all registered schemas', () => {
      const manager = new ConfigurationSchemaManager();
      manager.registerSchema(createConfigurationSchema({ schemaName: 'S1' }));
      manager.registerSchema(createConfigurationSchema({ schemaName: 'S2' }));

      expect(manager.listSchemas().length).toBe(2);
      manager.clear();
      expect(manager.listSchemas().length).toBe(0);
    });
  });

  describe('3. ConfigurationResolver & Type Conversion Engine', () => {
    it('should resolve string values correctly', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'app.name': 12345 }));

      const name = provider.resolve<string>('app.name', 'string');
      expect(name).toBe('12345');
    });

    it('should resolve and convert number values', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'server.port': '8080' }));

      const port = provider.resolve<number>('server.port', 'number');
      expect(port).toBe(8080);
    });

    it('should throw ConfigurationValidationException for invalid number conversion', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'server.port': 'not-a-number' }));

      expect(() => provider.resolve<number>('server.port', 'number')).toThrow(
        ConfigurationValidationException,
      );
    });

    it('should resolve and convert boolean values (true, 1, yes vs false, 0, no)', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(
        new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, {
          'f1': 'true',
          'f2': '1',
          'f3': 'yes',
          'f4': 'false',
          'f5': '0',
          'f6': 'no',
        }),
      );

      expect(provider.resolve<boolean>('f1', 'boolean')).toBe(true);
      expect(provider.resolve<boolean>('f2', 'boolean')).toBe(true);
      expect(provider.resolve<boolean>('f3', 'boolean')).toBe(true);
      expect(provider.resolve<boolean>('f4', 'boolean')).toBe(false);
      expect(provider.resolve<boolean>('f5', 'boolean')).toBe(false);
      expect(provider.resolve<boolean>('f6', 'boolean')).toBe(false);
    });

    it('should throw ConfigurationValidationException for invalid boolean string', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'flag': 'maybe' }));

      expect(() => provider.resolve<boolean>('flag', 'boolean')).toThrow(
        ConfigurationValidationException,
      );
    });

    it('should resolve and convert Date values from ISO string and Date instance', () => {
      const provider = new ConfigurationProvider();
      const existingDate = new Date('2026-05-01');
      provider.registerSource(
        new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, {
          'start.date': '2026-01-01',
          'existing.date': existingDate,
        }),
      );

      const date = provider.resolve<Date>('start.date', 'date');
      expect(date).toBeInstanceOf(Date);
      expect(date.getFullYear()).toBe(2026);

      const date2 = provider.resolve<Date>('existing.date', 'date');
      expect(date2).toBe(existingDate);
    });

    it('should throw ConfigurationValidationException for invalid Date', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'start.date': 'invalid-date' }));

      expect(() => provider.resolve<Date>('start.date', 'date')).toThrow(
        ConfigurationValidationException,
      );
    });

    it('should resolve and convert array values from comma-separated string and array', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(
        new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, {
          'hosts': 'h1, h2, h3',
          'raw.list': ['a', 'b'],
        }),
      );

      const hosts = provider.resolve<string[]>('hosts', 'array');
      expect(hosts).toEqual(['h1', 'h2', 'h3']);

      const raw = provider.resolve<string[]>('raw.list', 'array');
      expect(raw).toEqual(['a', 'b']);
    });

    it('should resolve Set and Map instances', () => {
      const provider = new ConfigurationProvider();
      const existingSet = new Set(['s1']);
      const existingMap = new Map([['k', 1]]);
      provider.registerSource(
        new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, {
          'tags': 't1,t2',
          'meta': { a: 1 },
          'existingSet': existingSet,
          'existingMap': existingMap,
        }),
      );

      const tagSet = provider.resolve<Set<string>>('tags', 'set');
      expect(tagSet).toBeInstanceOf(Set);
      expect(tagSet.has('t1')).toBe(true);

      const metaMap = provider.resolve<Map<string, number>>('meta', 'map');
      expect(metaMap).toBeInstanceOf(Map);
      expect(metaMap.get('a')).toBe(1);

      expect(provider.resolve('existingSet', 'set')).toBe(existingSet);
      expect(provider.resolve('existingMap', 'map')).toBe(existingMap);
    });

    it('should fallback to default value when raw value is missing', () => {
      const provider = new ConfigurationProvider();
      const port = provider.resolve<number>('server.port', 'number', 3000);
      expect(port).toBe(3000);
    });

    it('should throw ConfigurationValidationException when required key is missing without fallback', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'ReqSchema',
        definitions: {
          'secret.key': createConfigurationDefinition({
            key: 'secret.key',
            expectedType: 'string',
            required: true,
          }),
        },
      });

      provider.registerSchema(schema);
      expect(() => provider.resolve('secret.key')).toThrow(ConfigurationValidationException);
    });

    it('should resolve all configuration keys via resolveAll()', () => {
      const provider = new ConfigurationProvider();
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'a': '1', 'b': 'true' }));

      const resolved = provider.resolveAll();
      expect(resolved.a).toBe('1');
      expect(resolved.b).toBe('true');
    });
  });

  describe('4. ConfigurationValidator Engine', () => {
    it('should pass validation when all required fields and constraints are satisfied', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'AppConfig',
        definitions: {
          'server.port': createConfigurationDefinition({
            key: 'server.port',
            expectedType: 'number',
            required: true,
            constraint: createConfigurationConstraint({ minValue: 1024, maxValue: 65535 }),
          }),
          'app.env': createConfigurationDefinition({
            key: 'app.env',
            expectedType: 'string',
            required: true,
            constraint: createConfigurationConstraint({ allowedValues: ['dev', 'prod'] }),
          }),
        },
      });

      provider.registerSchema(schema);
      provider.registerSource(
        new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'server.port': 8080, 'app.env': 'prod' }),
      );

      const result = provider.validate('AppConfig');
      expect(result.valid).toBe(true);
      expect(result.errors.length).toBe(0);
    });

    it('should fail validation when required field is missing', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'AppConfig',
        definitions: {
          'api.key': createConfigurationDefinition({ key: 'api.key', expectedType: 'string', required: true }),
        },
      });

      provider.registerSchema(schema);
      const result = provider.validate('AppConfig');

      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === 'REQUIRED_FIELD_MISSING')).toBe(true);
    });

    it('should validate minValue constraint violation', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'MinSchema',
        definitions: {
          'port': createConfigurationDefinition({
            key: 'port',
            expectedType: 'number',
            constraint: createConfigurationConstraint({ minValue: 1024 }),
          }),
        },
      });

      provider.registerSchema(schema);
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { port: 80 }));

      const result = provider.validate('MinSchema');
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === 'MIN_VALUE_VIOLATION')).toBe(true);
    });

    it('should validate maxValue constraint violation', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'MaxSchema',
        definitions: {
          'threads': createConfigurationDefinition({
            key: 'threads',
            expectedType: 'number',
            constraint: createConfigurationConstraint({ maxValue: 16 }),
          }),
        },
      });

      provider.registerSchema(schema);
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { threads: 64 }));

      const result = provider.validate('MaxSchema');
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === 'MAX_VALUE_VIOLATION')).toBe(true);
    });

    it('should validate minLength and maxLength constraint violations', () => {
      const schema = createConfigurationSchema({
        schemaName: 'LengthSchema',
        definitions: {
          'pass': createConfigurationDefinition({
            key: 'pass',
            expectedType: 'string',
            constraint: createConfigurationConstraint({ minLength: 8, maxLength: 16 }),
          }),
        },
      });

      const provider = new ConfigurationProvider();
      provider.registerSchema(schema);
      provider.registerSource(new MemoryConfigurationSource('MemShort', 600, { pass: 'short' }));

      const shortRes = provider.validate('LengthSchema');
      expect(shortRes.valid).toBe(false);
      expect(shortRes.errors.some((e) => e.code === 'MIN_LENGTH_VIOLATION')).toBe(true);

      const provider2 = new ConfigurationProvider();
      provider2.registerSchema(schema);
      provider2.registerSource(new MemoryConfigurationSource('MemLong', 600, { pass: 'superlongpasswordexceedingmax' }));
      const longRes = provider2.validate('LengthSchema');
      expect(longRes.valid).toBe(false);
      expect(longRes.errors.some((e) => e.code === 'MAX_LENGTH_VIOLATION')).toBe(true);
    });

    it('should validate regexPattern constraint violation', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'RegexSchema',
        definitions: {
          'email': createConfigurationDefinition({
            key: 'email',
            expectedType: 'string',
            constraint: createConfigurationConstraint({ regexPattern: '^[a-z]+@[a-z]+\\.[a-z]+$' }),
          }),
        },
      });

      provider.registerSchema(schema);
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { email: 'invalid-email' }));

      const result = provider.validate('RegexSchema');
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === 'REGEX_MISMATCH')).toBe(true);
    });

    it('should validate allowedValues constraint violation', () => {
      const provider = new ConfigurationProvider();
      const schema = createConfigurationSchema({
        schemaName: 'EnumSchema',
        definitions: {
          'mode': createConfigurationDefinition({
            key: 'mode',
            expectedType: 'string',
            constraint: createConfigurationConstraint({ allowedValues: ['light', 'dark'] }),
          }),
        },
      });

      provider.registerSchema(schema);
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { mode: 'neon' }));

      const result = provider.validate('EnumSchema');
      expect(result.valid).toBe(false);
      expect(result.errors.some((e) => e.code === 'DISALLOWED_VALUE')).toBe(true);
    });

    it('should validate across all registered schemas when schemaName parameter is omitted', () => {
      const provider = new ConfigurationProvider();
      const s1 = createConfigurationSchema({
        schemaName: 'S1',
        definitions: { 'k1': createConfigurationDefinition({ key: 'k1', expectedType: 'string', required: true }) },
      });
      const s2 = createConfigurationSchema({
        schemaName: 'S2',
        definitions: { 'k2': createConfigurationDefinition({ key: 'k2', expectedType: 'number', required: true }) },
      });

      provider.registerSchema(s1);
      provider.registerSchema(s2);
      provider.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'k1': 'val1' }));

      const res = provider.validate();
      expect(res.valid).toBe(false);
      expect(res.errors.some((e) => e.key === 'k2')).toBe(true);
    });
  });

  describe('5. Provider & Runtime Delegation Integration', () => {
    it('should delegate registerSchema, getSchema, and listSchemas through ConfigurationRuntime', () => {
      const runtime = new ConfigurationRuntime();
      const schema = createConfigurationSchema({ schemaName: 'RuntimeSchema' });

      runtime.registerSchema(schema);
      expect(runtime.getSchema('RuntimeSchema')).toBe(schema);
      expect(runtime.listSchemas().length).toBe(1);

      expect(runtime.unregisterSchema('RuntimeSchema')).toBe(true);
      expect(runtime.listSchemas().length).toBe(0);
    });

    it('should delegate resolve, resolveAll, and validate through ConfigurationRuntime', () => {
      const runtime = new ConfigurationRuntime();
      runtime.registerSource(new MemoryConfigurationSource('Mem', ConfigurationSourcePriority.MEMORY, { 'port': '9090' }));

      const port = runtime.resolve<number>('port', 'number');
      expect(port).toBe(9090);

      const all = runtime.resolveAll();
      expect(all.port).toBe('9090');

      const val = runtime.validate();
      expect(val.valid).toBe(true);
    });

    it('should include schemas, validationStats, and resolutionStats in diagnostics()', () => {
      const provider = new ConfigurationProvider();
      provider.registerSchema(createConfigurationSchema({ schemaName: 'DiagSchema' }));
      provider.resolve<number>('missing.key', 'number', 123);
      provider.validate('DiagSchema');

      const diag = provider.diagnostics();
      expect(diag.schemas).toContain('DiagSchema');
      expect(diag.validationStats).toBeDefined();
      expect(diag.validationStats?.validations).toBeGreaterThan(0);
      expect(diag.resolutionStats).toBeDefined();
      expect(diag.resolutionStats?.resolutions).toBeGreaterThan(0);
    });
  });
});
