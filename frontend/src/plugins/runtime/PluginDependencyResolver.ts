import type { PluginManifest } from '../models/manifest';
import type { IPluginDiscoveryManager } from '../interfaces/plugin-discovery';
import type { IPluginDependencyResolver } from '../interfaces/plugin-dependency';
import type {
  PluginDependencyGraph,
  DependencyResolutionResult,
  DependencyResolutionStatistics,
  DependencyResolutionHealth,
  DependencyResolutionIssue
} from '../models/dependency';
import {
  DependencyResolutionStatus,
  DependencyResolutionIssueCode
} from '../models/dependency';
import { SemVerValidator } from './SemVerValidator';
import { PluginDependencyGraphBuilder } from './PluginDependencyGraphBuilder';
import { freezeDeepSafe } from '../models/dependency';

export class PluginDependencyResolver implements IPluginDependencyResolver {
  private currentGraph: PluginDependencyGraph = {
    nodes: new Map(),
    edges: []
  };

  private resolutionAttemptsCount = 0;
  private resolvedPluginsCount = 0;
  private unresolvedPluginsCount = 0;
  private missingDependenciesCount = 0;
  private versionConflictsCount = 0;
  private circularDependenciesCount = 0;
  private optionalDependencyWarningsCount = 0;
  private graphNodesCount = 0;
  private graphEdgesCount = 0;
  private resolutionFailuresCount = 0;

  constructor(private readonly discoveryManager: IPluginDiscoveryManager) {}

  public resolve(manifests: ReadonlyArray<PluginManifest>): DependencyResolutionResult {
    this.resolutionAttemptsCount += 1;
    return this.resolveInternal(manifests, false);
  }

  public resolveAll(): DependencyResolutionResult {
    const manifests = this.discoveryManager.findAll();
    return this.resolve(manifests);
  }

  public resolvePlugin(pluginId: string): DependencyResolutionResult {
    this.resolutionAttemptsCount += 1;
    const allManifests = this.discoveryManager.findAll();
    
    const manifestMap = new Map<string, PluginManifest>();
    allManifests.forEach(m => manifestMap.set(m.id, m));

    if (!manifestMap.has(pluginId)) {
      const issue: DependencyResolutionIssue = {
        code: DependencyResolutionIssueCode.MISSING_DEPENDENCY,
        severity: 'error',
        message: `Plugin '${pluginId}' not found for dependency resolution.`,
        dependencyId: pluginId
      };
      
      this.resolutionFailuresCount += 1;
      this.missingDependenciesCount += 1;
      
      const result: DependencyResolutionResult = {
        status: DependencyResolutionStatus.FAILED,
        plan: null,
        issues: [issue],
        resolvedIds: [],
        unresolvedIds: [pluginId]
      };
      return freezeDeepSafe(result);
    }

    const visited = new Set<string>();
    const collectTransitive = (id: string) => {
      if (visited.has(id)) return;
      visited.add(id);
      const manifest = manifestMap.get(id);
      if (manifest) {
        manifest.dependencies.forEach(d => {
          collectTransitive(d.id);
        });
      }
    };
    collectTransitive(pluginId);

    const filteredManifests = allManifests.filter(m => visited.has(m.id));
    return this.resolveInternal(filteredManifests, true);
  }

  public graph(): PluginDependencyGraph {
    return this.currentGraph;
  }

  public dependenciesOf(pluginId: string): ReadonlyArray<string> {
    const node = this.currentGraph.nodes.get(pluginId);
    if (!node) return [];
    return Object.freeze(node.dependencies.map(d => d.id).sort());
  }

  public dependentsOf(pluginId: string): ReadonlyArray<string> {
    const dependents: string[] = [];
    for (const node of this.currentGraph.nodes.values()) {
      if (node.dependencies.some(d => d.id === pluginId)) {
        dependents.push(node.id);
      }
    }
    return Object.freeze(dependents.sort());
  }

  public statistics(): DependencyResolutionStatistics {
    return Object.freeze({
      resolutionAttempts: this.resolutionAttemptsCount,
      resolvedPlugins: this.resolvedPluginsCount,
      unresolvedPlugins: this.unresolvedPluginsCount,
      missingDependencies: this.missingDependenciesCount,
      versionConflicts: this.versionConflictsCount,
      circularDependencies: this.circularDependenciesCount,
      optionalDependencyWarnings: this.optionalDependencyWarningsCount,
      graphNodes: this.graphNodesCount,
      graphEdges: this.graphEdgesCount,
      resolutionFailures: this.resolutionFailuresCount
    });
  }

  public health(): DependencyResolutionHealth {
    const cycleCount = this.circularDependenciesCount;
    const conflictCount = this.versionConflictsCount;
    const unresolvedCount = this.unresolvedPluginsCount;

    const healthy = unresolvedCount === 0 && cycleCount === 0 && conflictCount === 0;

    return Object.freeze({
      healthy,
      unresolvedDependencyCount: unresolvedCount,
      cycleCount,
      conflictCount,
      message: healthy 
        ? 'Dependency engine healthy' 
        : `Dependency engine issues detected: ${unresolvedCount} unresolved, ${cycleCount} cycles, ${conflictCount} conflicts.`
    });
  }

  public reset(): void {
    this.currentGraph = { nodes: new Map(), edges: [] };
    this.resolutionAttemptsCount = 0;
    this.resolvedPluginsCount = 0;
    this.unresolvedPluginsCount = 0;
    this.missingDependenciesCount = 0;
    this.versionConflictsCount = 0;
    this.circularDependenciesCount = 0;
    this.optionalDependencyWarningsCount = 0;
    this.graphNodesCount = 0;
    this.graphEdgesCount = 0;
    this.resolutionFailuresCount = 0;
  }

  private resolveInternal(manifests: ReadonlyArray<PluginManifest>, isSinglePluginResolve: boolean): DependencyResolutionResult {
    const graph = PluginDependencyGraphBuilder.build(manifests);
    if (!isSinglePluginResolve) {
      this.currentGraph = graph;
      this.graphNodesCount = graph.nodes.size;
      this.graphEdgesCount = graph.edges.length;
    }

    const issues: DependencyResolutionIssue[] = [];
    const nodes = graph.nodes;

    // Validate relationships
    for (const node of nodes.values()) {
      for (const dep of node.dependencies) {
        const depNode = nodes.get(dep.id);
        if (!depNode) {
          issues.push({
            code: DependencyResolutionIssueCode.MISSING_DEPENDENCY,
            severity: dep.optional ? 'warning' : 'error',
            message: `Dependency '${dep.id}' of plugin '${node.id}' is missing.`,
            dependentId: node.id,
            dependencyId: dep.id,
            constraint: dep.versionRange
          });
          if (dep.optional) {
            this.optionalDependencyWarningsCount += 1;
          } else {
            this.missingDependenciesCount += 1;
          }
        } else {
          // Version compatibility check
          const satisfied = SemVerValidator.satisfies(depNode.manifest.version, dep.versionRange);
          if (!satisfied) {
            issues.push({
              code: DependencyResolutionIssueCode.VERSION_CONFLICT,
              severity: dep.optional ? 'warning' : 'error',
              message: `Dependency '${dep.id}' (${depNode.manifest.version}) of plugin '${node.id}' does not satisfy constraint '${dep.versionRange}'.`,
              dependentId: node.id,
              dependencyId: dep.id,
              constraint: dep.versionRange
            });
            if (dep.optional) {
              this.optionalDependencyWarningsCount += 1;
            } else {
              this.versionConflictsCount += 1;
            }
          }
        }
      }
    }

    // Cycle detection & topological sort using DFS
    const visited = new Map<string, number>(); // 0=white, 1=gray, 2=black
    const order: string[] = [];
    const dfsStack: string[] = [];
    const detectedCycles = new Set<string>();

    const dfs = (nodeId: string) => {
      visited.set(nodeId, 1);
      dfsStack.push(nodeId);

      const node = nodes.get(nodeId);
      if (node) {
        const sortedDeps = [...node.dependencies].sort((a, b) => a.id.localeCompare(b.id));
        for (const dep of sortedDeps) {
          const depId = dep.id;
          if (!nodes.has(depId)) {
            continue; // Missing dependency, already handled
          }

          const depState = visited.get(depId) || 0;
          if (depState === 1) {
            const cycleIndex = dfsStack.indexOf(depId);
            const cyclePath = dfsStack.slice(cycleIndex).concat(depId);
            const cycleKey = cyclePath.join('->');
            
            if (!detectedCycles.has(cycleKey)) {
              detectedCycles.add(cycleKey);
              
              // Determine if cycle contains any required edges
              let hasRequiredEdge = false;
              for (let i = 0; i < cyclePath.length - 1; i++) {
                const fromId = cyclePath[i];
                const toId = cyclePath[i + 1];
                const fromNode = nodes.get(fromId);
                const edgeDep = fromNode?.dependencies.find(d => d.id === toId);
                if (edgeDep && !edgeDep.optional) {
                  hasRequiredEdge = true;
                  break;
                }
              }

              issues.push({
                code: DependencyResolutionIssueCode.CIRCULAR_DEPENDENCY,
                severity: hasRequiredEdge ? 'error' : 'warning',
                message: `Circular dependency detected: ${cyclePath.join(' -> ')}`,
                path: Object.freeze(cyclePath)
              });
              this.circularDependenciesCount += 1;
            }
          } else if (depState === 0) {
            dfs(depId);
          }
        }
      }

      dfsStack.pop();
      visited.set(nodeId, 2);
      order.push(nodeId);
    };

    const sortedNodeIds = Array.from(nodes.keys()).sort((a, b) => a.localeCompare(b));
    for (const nodeId of sortedNodeIds) {
      if ((visited.get(nodeId) || 0) === 0) {
        dfs(nodeId);
      }
    }

    // Resolve bad (unresolved) nodes transitively
    const badNodes = new Set<string>();
    
    for (const issue of issues) {
      if (issue.severity === 'error') {
        if (issue.dependentId) {
          badNodes.add(issue.dependentId);
        }
        if (issue.code === DependencyResolutionIssueCode.CIRCULAR_DEPENDENCY && issue.path) {
          issue.path.forEach(id => badNodes.add(id));
        }
      }
    }

    let changed = true;
    while (changed) {
      changed = false;
      for (const node of nodes.values()) {
        if (badNodes.has(node.id)) continue;
        for (const dep of node.dependencies) {
          if (!dep.optional) {
            if (!nodes.has(dep.id) || badNodes.has(dep.id)) {
              badNodes.add(node.id);
              changed = true;
              break;
            }
          }
        }
      }
    }

    const unresolvedIds = Array.from(badNodes).sort();
    const resolvedIds = Array.from(nodes.keys()).filter(id => !badNodes.has(id)).sort();

    const hasErrors = issues.some(issue => issue.severity === 'error');
    const status = hasErrors ? DependencyResolutionStatus.FAILED : DependencyResolutionStatus.RESOLVED;

    let plan = null;
    if (!hasErrors) {
      plan = {
        order: [...order]
      };
      this.resolvedPluginsCount += order.length;
    } else {
      this.resolutionFailuresCount += 1;
      this.unresolvedPluginsCount += unresolvedIds.length;
      this.resolvedPluginsCount += resolvedIds.length;
    }

    const result: DependencyResolutionResult = {
      status,
      plan,
      issues,
      resolvedIds,
      unresolvedIds
    };

    return freezeDeepSafe(result);
  }
}
