import { beforeEach, describe, expect, it } from 'vitest';
import {
  PluginRuntime,
  PluginProvider,
  getPluginRuntime,
  getPluginProvider,
  setPluginRuntime,
  setPluginProvider,
  resetPluginRuntime,
  resetPluginProvider,
  PluginRuntimeStatus,
  PluginRuntimeState,
  PluginLifecycleState,
  // Exceptions
  PluginRuntimeException,
  PluginInitializationException,
  PluginRegistrationException,
  PluginValidationException,
  PluginDependencyException,
  PluginPermissionException,
  PluginSandboxException,
  PluginLifecycleException,
  PluginActivationException,
  PluginExecutionException,
  PluginCompatibilityException,
  PluginCertificationException,
  // Factories
  createPluginAuthor,
  createPluginVersion,
  createPluginDependency,
  createPluginCapability,
  createPluginPermission,
  createPluginSandbox,
  createPluginMetadata,
  createPluginContribution,
  createPluginExtensionPoint,
  createPluginManifest,
  createPluginDescriptor,
  createPluginContext,
  createPluginState,
  createPluginConfiguration,
  createPluginHealth,
  createPluginStatistics,
  createPluginDiagnostics,
  createPluginSnapshot,
  createPluginActivation,
  createPluginDeactivation,
  createPluginLoadResult,
  createPluginUnloadResult,
  createPluginRegistration,
  createPluginValidationIssue,
  createPluginValidationResult,
  createPluginCompatibilityResult,
  createPluginResolutionResult,
  createPluginService,
  createPluginLifecycleRecord,
  createPluginExecutionRecord,
  createPluginTelemetry,
  createCertificationIssue,
  createPluginCertification,
  createPluginCertificationSummary,
  createCertificationStatistics,
  createCertificationHealth,
  createCertificationReport,
  createPluginRuntimeState,
} from '../../src/runtime/plugins';

describe('Phase 16.7 — Plugin Runtime Coordinator & Singletons Tests', () => {
  beforeEach(() => {
    resetPluginRuntime();
    resetPluginProvider();
  });

  describe('1. Global Accessors & Singletons', () => {
    it('should lazily create a global provider instance if none exists', () => {
      const provider = getPluginProvider();
      expect(provider).toBeInstanceOf(PluginProvider);
      expect(getPluginProvider()).toBe(provider);
    });

    it('should allow setting a custom provider instance', () => {
      const customProvider = new PluginProvider();
      setPluginProvider(customProvider);
      expect(getPluginProvider()).toBe(customProvider);
    });

    it('should reset the global provider instance', () => {
      const provider = getPluginProvider();
      resetPluginProvider();
      expect(getPluginProvider()).not.toBe(provider);
    });

    it('should lazily create a global runtime coordinator instance', () => {
      const runtime = getPluginRuntime();
      expect(runtime).toBeInstanceOf(PluginRuntime);
      expect(getPluginRuntime()).toBe(runtime);
    });

    it('should allow setting a custom runtime coordinator instance', () => {
      const customRuntime = new PluginRuntime();
      setPluginRuntime(customRuntime);
      expect(getPluginRuntime()).toBe(customRuntime);
    });

    it('should reset the global runtime coordinator and provider instances', () => {
      const runtime = getPluginRuntime();
      const provider = getPluginProvider();
      resetPluginRuntime();
      expect(getPluginRuntime()).not.toBe(runtime);
      expect(getPluginProvider()).not.toBe(provider);
    });
  });

  describe('2. PluginRuntime Coordinator Delegation', () => {
    it('should forward initialize call to the provider instance', () => {
      const runtime = getPluginRuntime();
      expect(() => runtime.initialize()).not.toThrow();
    });

    it('should forward shutdown call to the provider instance', () => {
      const runtime = getPluginRuntime();
      expect(() => runtime.shutdown()).not.toThrow();
    });

    it('should retrieve registry from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getRegistry()).toBeDefined();
    });

    it('should retrieve loader from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getLoader()).toBeDefined();
    });

    it('should retrieve lifecycle manager from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getLifecycleManager()).toBeDefined();
    });

    it('should retrieve dependency resolver from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getDependencyResolver()).toBeDefined();
    });

    it('should retrieve capability manager from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getCapabilityManager()).toBeDefined();
    });

    it('should retrieve service registry from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getServiceRegistry()).toBeDefined();
    });

    it('should retrieve permission manager from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getPermissionManager()).toBeDefined();
    });

    it('should retrieve sandbox manager from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getSandboxManager()).toBeDefined();
    });

    it('should retrieve validator from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getValidator()).toBeDefined();
    });

    it('should retrieve diagnostics from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getDiagnostics()).toBeDefined();
    });

    it('should retrieve certifier from provider delegation', () => {
      const runtime = getPluginRuntime();
      expect(runtime.getCertifier()).toBeDefined();
    });
  });

  describe('3. Custom Exceptions Instantiation', () => {
    it('should instantiate PluginRuntimeException', () => {
      const e = new PluginRuntimeException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginRuntimeException');
    });

    it('should instantiate PluginInitializationException', () => {
      const e = new PluginInitializationException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginInitializationException');
    });

    it('should instantiate PluginRegistrationException', () => {
      const e = new PluginRegistrationException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginRegistrationException');
    });

    it('should instantiate PluginValidationException', () => {
      const e = new PluginValidationException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginValidationException');
    });

    it('should instantiate PluginDependencyException', () => {
      const e = new PluginDependencyException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginDependencyException');
    });

    it('should instantiate PluginPermissionException', () => {
      const e = new PluginPermissionException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginPermissionException');
    });

    it('should instantiate PluginSandboxException', () => {
      const e = new PluginSandboxException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginSandboxException');
    });

    it('should instantiate PluginLifecycleException', () => {
      const e = new PluginLifecycleException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginLifecycleException');
    });

    it('should instantiate PluginActivationException', () => {
      const e = new PluginActivationException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginActivationException');
    });

    it('should instantiate PluginExecutionException', () => {
      const e = new PluginExecutionException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginExecutionException');
    });

    it('should instantiate PluginCompatibilityException', () => {
      const e = new PluginCompatibilityException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginCompatibilityException');
    });

    it('should instantiate PluginCertificationException', () => {
      const e = new PluginCertificationException('msg');
      expect(e.message).toBe('msg');
      expect(e.name).toBe('PluginCertificationException');
    });
  });

  describe('4. Factory Functions Immutability & Defaults', () => {
    it('should create immutable PluginAuthor', () => {
      const m = createPluginAuthor();
      expect(m.name).toBe('Unknown');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginVersion', () => {
      const m = createPluginVersion({ major: 2 });
      expect(m.major).toBe(2);
      expect(m.raw).toBe('2.0.0');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginDependency', () => {
      const m = createPluginDependency({ id: 'dep' });
      expect(m.id).toBe('dep');
      expect(m.versionRange).toBe('*');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginCapability', () => {
      const m = createPluginCapability({ type: 'command', name: 'cmd' });
      expect(m.type).toBe('command');
      expect(m.name).toBe('cmd');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.details)).toBe(true);
    });

    it('should create immutable PluginPermission', () => {
      const m = createPluginPermission({ scope: 'filesystem' });
      expect(m.scope).toBe('filesystem');
      expect(m.required).toBe(true);
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginSandbox', () => {
      const m = createPluginSandbox();
      expect(m.executionIsolation).toBe(true);
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.capabilityRestrictions)).toBe(true);
    });

    it('should create immutable PluginMetadata', () => {
      const m = createPluginMetadata();
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginContribution', () => {
      const m = createPluginContribution({ target: 'target' });
      expect(m.target).toBe('target');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginExtensionPoint', () => {
      const m = createPluginExtensionPoint({ id: 'ep' });
      expect(m.id).toBe('ep');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginManifest', () => {
      const m = createPluginManifest({ id: 'id', name: 'name' });
      expect(m.id).toBe('id');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.dependencies)).toBe(true);
    });

    it('should create immutable PluginDescriptor', () => {
      const manifest = createPluginManifest({ id: 'id', name: 'name' });
      const m = createPluginDescriptor({ id: 'id', manifest });
      expect(m.id).toBe('id');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginContext', () => {
      const m = createPluginContext({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginState', () => {
      const m = createPluginState({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginConfiguration', () => {
      const m = createPluginConfiguration({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginHealth', () => {
      const m = createPluginHealth({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.issues)).toBe(true);
    });

    it('should create immutable PluginStatistics', () => {
      const m = createPluginStatistics({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginDiagnostics', () => {
      const m = createPluginDiagnostics({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginSnapshot', () => {
      const m = createPluginSnapshot({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginActivation', () => {
      const m = createPluginActivation({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginDeactivation', () => {
      const m = createPluginDeactivation({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginLoadResult', () => {
      const m = createPluginLoadResult({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginUnloadResult', () => {
      const m = createPluginUnloadResult({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginRegistration', () => {
      const m = createPluginRegistration({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginValidationIssue', () => {
      const m = createPluginValidationIssue({ severity: 'error', path: 'p', message: 'm' });
      expect(m.severity).toBe('error');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginValidationResult', () => {
      const m = createPluginValidationResult({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.issues)).toBe(true);
    });

    it('should create immutable PluginCompatibilityResult', () => {
      const m = createPluginCompatibilityResult({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginResolutionResult', () => {
      const m = createPluginResolutionResult({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.missingRequired)).toBe(true);
    });

    it('should create immutable PluginService', () => {
      const m = createPluginService({ id: 's', pluginId: 'p', interfaceName: 'i' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginLifecycleRecord', () => {
      const m = createPluginLifecycleRecord({ pluginId: 'p', state: PluginLifecycleState.ACTIVATED });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginExecutionRecord', () => {
      const m = createPluginExecutionRecord({ pluginId: 'p', action: 'act' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginTelemetry', () => {
      const m = createPluginTelemetry({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.logs)).toBe(true);
    });

    it('should create immutable CertificationIssue', () => {
      const m = createCertificationIssue({ type: 't', message: 'm' });
      expect(m.type).toBe('t');
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable PluginCertification', () => {
      const m = createPluginCertification({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.issues)).toBe(true);
    });

    it('should create immutable PluginCertificationSummary', () => {
      const m = createPluginCertificationSummary();
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable CertificationStatistics', () => {
      const m = createCertificationStatistics();
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable CertificationHealth', () => {
      const m = createCertificationHealth();
      expect(Object.isFrozen(m)).toBe(true);
    });

    it('should create immutable CertificationReport', () => {
      const m = createCertificationReport({ pluginId: 'p' });
      expect(m.pluginId).toBe('p');
      expect(Object.isFrozen(m)).toBe(true);
      expect(Object.isFrozen(m.certification)).toBe(true);
    });

    it('should create immutable PluginRuntimeState', () => {
      const m = createPluginRuntimeState();
      expect(m.runtimeState).toBe(PluginRuntimeStatus.UNINITIALIZED);
      expect(Object.isFrozen(m)).toBe(true);
    });
  });

  describe('5. Enums Validation', () => {
    it('should verify PluginRuntimeStatus enum values', () => {
      expect(PluginRuntimeStatus.UNINITIALIZED).toBe('UNINITIALIZED');
      expect(PluginRuntimeStatus.INITIALIZING).toBe('INITIALIZING');
      expect(PluginRuntimeStatus.READY).toBe('READY');
      expect(PluginRuntimeStatus.STOPPING).toBe('STOPPING');
      expect(PluginRuntimeStatus.STOPPED).toBe('STOPPED');
    });
  });
});
