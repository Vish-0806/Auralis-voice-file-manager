import { beforeEach, describe, expect, it } from 'vitest';
import {
  CircularDependencyException,
  ContainerState,
  createContainerCapabilities,
  createContainerConfiguration,
  createContainerContext,
  createContainerDiagnostics,
  createContainerHealth,
  createContainerStatistics,
  createDependencyAnalysis,
  createDependencyCertification,
  createDependencyGraph,
  createDependencyGraphEdge,
  createDependencyGraphNode,
  createDependencyIssue,
  createDependencyNode,
  createGraphStatistics,
  createScopedContainer,
  createServiceDescriptorModel,
  createServiceRegistration,
  DependencyContainer,
  DependencyGraphAnalyzer,
  DependencyInjectionException,
  getDependencyContainer,
  getServiceProvider,
  resetDependencyContainer,
  resetServiceProvider,
  ServiceCollection,
  ServiceDescriptor,
  ServiceLifetime,
  ServiceProvider,
  ServiceRegistrationException,
  ServiceResolutionException,
  ServiceValidationException,
  setDependencyContainer,
  setServiceProvider,
} from '../../src/runtime/di';

class ConfigService {
  public env = 'test';
}

class LoggerService {
  constructor(public config: ConfigService) {}
}

class UserSessionService {
  constructor(public logger: LoggerService) {}
}

class OrphanService {
  public id = 'orphan';
}

describe('Phase 16.2.5 — Frontend Dependency Injection Production Certification & Graph Analysis', () => {
  beforeEach(() => {
    resetDependencyContainer();
    resetServiceProvider();
  });

  describe('1. Immutable Graph Models & Factory Functions', () => {
    it('should create immutable DependencyGraphNode and DependencyGraphEdge', () => {
      const node = createDependencyGraphNode({
        serviceType: 'ServiceA',
        lifetime: ServiceLifetime.SINGLETON,
        dependencies: ['ServiceB'],
      });
      expect(node.serviceType).toBe('ServiceA');
      expect(node.dependencies).toContain('ServiceB');
      expect(Object.isFrozen(node)).toBe(true);

      const edge = createDependencyGraphEdge({ source: 'ServiceA', target: 'ServiceB' });
      expect(edge.source).toBe('ServiceA');
      expect(edge.target).toBe('ServiceB');
      expect(Object.isFrozen(edge)).toBe(true);
    });

    it('should create immutable DependencyAnalysis and DependencyCertification', () => {
      const graph = createDependencyGraph();
      const stats = createGraphStatistics({ nodeCount: 1 });
      const issue = createDependencyIssue({ message: 'warn', service: 'S1', severity: 'warning' });

      const analysis = createDependencyAnalysis({ graph, statistics: stats, issues: [issue] });
      expect(analysis.healthy).toBe(true);
      expect(Object.isFrozen(analysis)).toBe(true);

      const cert = createDependencyCertification({ analysis, certified: true, productionReady: false });
      expect(cert.certified).toBe(true);
      expect(Object.isFrozen(cert)).toBe(true);
    });
  });

  describe('2. Graph Analysis & Root/Leaf/Orphan Detection', () => {
    it('should correctly analyze graph topology (roots, leaves, orphans)', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('ConfigService', ConfigService);
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['ConfigService'] });
      collection.addSingleton('OrphanService', OrphanService);

      const analyzer = new DependencyGraphAnalyzer();
      const analysis = analyzer.analyze(collection);

      expect(analysis.statistics.nodeCount).toBe(3);
      expect(analysis.statistics.edgeCount).toBe(1);
      expect(analysis.statistics.rootServices).toContain('LoggerService');
      expect(analysis.statistics.leafServices).toContain('ConfigService');
      expect(analysis.statistics.orphanServices).toContain('OrphanService');
    });

    it('should detect missing dependency errors', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['MissingConfig'] });

      const analyzer = new DependencyGraphAnalyzer();
      const analysis = analyzer.analyze(collection);

      expect(analysis.healthy).toBe(false);
      expect(analysis.issues.some((i) => i.message.includes('missing service'))).toBe(true);
    });

    it('should detect singleton -> scoped lifetime violations', () => {
      const collection = new ServiceCollection();
      collection.addScoped('UserSessionService', UserSessionService);
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['UserSessionService'] });

      const analyzer = new DependencyGraphAnalyzer();
      const analysis = analyzer.analyze(collection);

      expect(analysis.healthy).toBe(false);
      expect(analysis.issues.some((i) => i.message.includes('Lifetime violation'))).toBe(true);
    });
  });

  describe('3. Production Certification Engine', () => {
    it('should issue production certification for clean container', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('ConfigService', ConfigService);
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['ConfigService'] });

      const analyzer = new DependencyGraphAnalyzer();
      const cert = analyzer.certify(collection);

      expect(cert.certified).toBe(true);
      expect(cert.productionReady).toBe(true);
      expect(cert.summary).toContain('Certified Production Ready');
    });

    it('should fail certification when errors are present', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['MissingConfig'] });

      const analyzer = new DependencyGraphAnalyzer();
      const cert = analyzer.certify(collection);

      expect(cert.certified).toBe(false);
      expect(cert.productionReady).toBe(false);
      expect(cert.summary).toContain('Certification Failed');
    });
  });

  describe('4. Diagram & Structure Export Formats', () => {
    it('should export Mermaid, DOT, Adjacency List, and Adjacency Map', () => {
      const collection = new ServiceCollection();
      collection.addSingleton('ConfigService', ConfigService);
      collection.addSingleton('LoggerService', LoggerService, { dependencies: ['ConfigService'] });

      const container = new DependencyContainer(undefined, collection);
      const mermaid = container.exportGraph('mermaid');
      expect(mermaid).toContain('graph TD');
      expect(mermaid).toContain('LoggerService --> ConfigService');

      const dot = container.exportGraph('dot');
      expect(dot).toContain('digraph G');
      expect(dot).toContain('"LoggerService" -> "ConfigService";');

      const adjList = container.exportGraph('adjacency-list');
      expect(adjList).toContain('LoggerService: ConfigService');

      const adjMap = container.exportGraph('adjacency-map');
      expect(adjMap).toContain('"LoggerService": [\n    "ConfigService"\n  ]');
    });
  });

  describe('5. Container & Diagnostics Integration', () => {
    it('should expose graph analysis and certification via DependencyContainer & diagnostics()', () => {
      const container = new DependencyContainer();
      container.collection().addSingleton('ConfigService', ConfigService);
      container.collection().addSingleton('LoggerService', LoggerService, { dependencies: ['ConfigService'] });

      const analysis = container.analyzeGraph();
      expect(analysis.statistics.nodeCount).toBe(2);

      const issues = container.validateGraph();
      expect(issues.length).toBe(0);

      const cert = container.certify();
      expect(cert.certified).toBe(true);

      const diag = container.diagnostics();
      expect(diag.graphSummary).toBeDefined();
      expect(diag.certification?.certified).toBe(true);

      const scopeModel = createScopedContainer({ scopeId: 'sc1' });
      expect(scopeModel.scopeId).toBe('sc1');

      expect(createContainerCapabilities().supportsScopes).toBe(true);
      expect(createContainerConfiguration().name).toBe('Auralis Container');
      expect(createContainerContext().containerId).toBe('default-container');
      expect(createContainerDiagnostics().state).toBe(ContainerState.UNINITIALIZED);
      expect(createContainerHealth().healthy).toBe(false);
      expect(createContainerStatistics().totalRegistrations).toBe(0);
      expect(createDependencyNode({ serviceType: 'S1' }).serviceType).toBe('S1');
      expect(createServiceDescriptorModel({ descriptorId: 'd1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON }).serviceType).toBe('S1');
      expect(createServiceRegistration({ descriptorId: 'r1', serviceType: 'S1', lifetime: ServiceLifetime.SINGLETON }).serviceType).toBe('S1');

      expect(new CircularDependencyException('c')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceResolutionException('r')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceRegistrationException('rg')).toBeInstanceOf(DependencyInjectionException);
      expect(new ServiceValidationException('v')).toBeInstanceOf(DependencyInjectionException);

      expect(getServiceProvider()).toBeDefined();
      const customSP = new ServiceProvider();
      setServiceProvider(customSP);
      expect(getServiceProvider()).toBe(customSP);
      resetServiceProvider();

      expect(getDependencyContainer()).toBeDefined();
      const customDC = new DependencyContainer();
      setDependencyContainer(customDC);
      expect(getDependencyContainer()).toBe(customDC);
      resetDependencyContainer();

      const desc = new ServiceDescriptor('S1', ServiceLifetime.SINGLETON, ConfigService);
      expect(desc.serviceType).toBe('S1');
    });
  });
});
