/**
 * Dependency Graph Analyzer & Certification Engine (Phase 16.2.5).
 *
 * Analyzes container service descriptors, detects missing dependencies, orphan services,
 * circular dependency cycles, lifetime violations (Singleton -> Scoped), computes graph statistics,
 * exports graph diagrams (Mermaid, DOT, Adjacency List, Adjacency Map), and issues production certifications.
 */

import {
  createDependencyAnalysis,
  createDependencyCertification,
  createDependencyGraph,
  createDependencyGraphEdge,
  createDependencyGraphNode,
  createDependencyIssue,
  createGraphStatistics,
  DependencyAnalysis,
  DependencyCertification,
  DependencyGraphEdge,
  DependencyGraphNode,
  DependencyIssue,
  ServiceLifetime,
} from './models';
import { IServiceCollection } from './interfaces';

export class DependencyGraphAnalyzer {
  public analyze(collection: IServiceCollection): DependencyAnalysis {
    const descriptors = collection.listServices();
    const nodeMap = new Map<string, DependencyGraphNode>();
    const edges: DependencyGraphEdge[] = [];
    const issues: DependencyIssue[] = [];

    // 1. Build Nodes & Map
    for (const descriptor of descriptors) {
      const deps: string[] = Array.isArray(descriptor.metadata?.dependencies)
        ? (descriptor.metadata.dependencies as string[])
        : (descriptor.implementation as any)?.$dependencies ?? [];

      const node = createDependencyGraphNode({
        serviceType: descriptor.serviceType,
        implementationType: descriptor.implementation?.name,
        lifetime: descriptor.lifetime,
        dependencies: deps,
        aliases: descriptor.aliases,
        tags: descriptor.tags,
      });

      nodeMap.set(descriptor.serviceType, node);
      for (const alias of descriptor.aliases) {
        if (!nodeMap.has(alias)) {
          nodeMap.set(alias, node);
        }
      }
    }

    // 2. Build Edges & Check Missing / Lifetime Violations
    for (const descriptor of descriptors) {
      const source = descriptor.serviceType;
      const deps: string[] = Array.isArray(descriptor.metadata?.dependencies)
        ? (descriptor.metadata.dependencies as string[])
        : (descriptor.implementation as any)?.$dependencies ?? [];

      for (const depKey of deps) {
        edges.push(createDependencyGraphEdge({ source, target: depKey }));

        const targetDescriptor = collection.getDescriptor(depKey);
        if (!targetDescriptor) {
          issues.push(
            createDependencyIssue({
              severity: 'error',
              service: source,
              message: `Service '${source}' depends on missing service '${depKey}'.`,
            }),
          );
        } else if (
          descriptor.lifetime === ServiceLifetime.SINGLETON &&
          targetDescriptor.lifetime === ServiceLifetime.SCOPED
        ) {
          issues.push(
            createDependencyIssue({
              severity: 'error',
              service: source,
              message: `Lifetime violation: Singleton '${source}' depends on Scoped service '${depKey}'.`,
            }),
          );
        }
      }
    }

    // 3. Detect Circular Dependencies (DFS)
    const cycles: string[][] = [];
    const visited = new Set<string>();
    const inStack = new Set<string>();
    const stack: string[] = [];

    const dfs = (curr: string) => {
      visited.add(curr);
      inStack.add(curr);
      stack.push(curr);

      const descriptor = collection.getDescriptor(curr);
      if (descriptor) {
        const deps: string[] = Array.isArray(descriptor.metadata?.dependencies)
          ? (descriptor.metadata.dependencies as string[])
          : (descriptor.implementation as any)?.$dependencies ?? [];

        for (const dep of deps) {
          if (inStack.has(dep)) {
            const cycleStartIdx = stack.indexOf(dep);
            const cycle = [...stack.slice(cycleStartIdx), dep];
            cycles.push(cycle);
            issues.push(
              createDependencyIssue({
                severity: 'error',
                service: curr,
                message: `Circular dependency detected: ${cycle.join(' -> ')}`,
              }),
            );
          } else if (!visited.has(dep)) {
            dfs(dep);
          }
        }
      }

      stack.pop();
      inStack.delete(curr);
    };

    for (const descriptor of descriptors) {
      if (!visited.has(descriptor.serviceType)) {
        dfs(descriptor.serviceType);
      }
    }

    // 4. Roots, Leaves & Orphans
    const incomingEdgeCount = new Map<string, number>();
    const outgoingEdgeCount = new Map<string, number>();

    for (const d of descriptors) {
      incomingEdgeCount.set(d.serviceType, 0);
      outgoingEdgeCount.set(d.serviceType, 0);
    }

    for (const edge of edges) {
      outgoingEdgeCount.set(edge.source, (outgoingEdgeCount.get(edge.source) ?? 0) + 1);
      incomingEdgeCount.set(edge.target, (incomingEdgeCount.get(edge.target) ?? 0) + 1);
    }

    const rootServices: string[] = [];
    const leafServices: string[] = [];
    const orphanServices: string[] = [];

    for (const d of descriptors) {
      const type = d.serviceType;
      const inCount = incomingEdgeCount.get(type) ?? 0;
      const outCount = outgoingEdgeCount.get(type) ?? 0;

      if (inCount === 0) rootServices.push(type);
      if (outCount === 0) leafServices.push(type);
      if (inCount === 0 && outCount === 0) orphanServices.push(type);
    }

    if (orphanServices.length > 0) {
      for (const orphan of orphanServices) {
        issues.push(
          createDependencyIssue({
            severity: 'warning',
            service: orphan,
            message: `Orphan service '${orphan}' has no dependencies and no dependent services.`,
          }),
        );
      }
    }

    // 5. Compute Depth Metrics
    let maxDepth = 0;
    let totalDepthSum = 0;
    const computeDepth = (type: string, currentDepth: number, seen: Set<string>): number => {
      if (seen.has(type)) return currentDepth;
      seen.add(type);
      let localMax = currentDepth;
      const d = collection.getDescriptor(type);
      if (d) {
        const deps: string[] = Array.isArray(d.metadata?.dependencies)
          ? (d.metadata.dependencies as string[])
          : (d.implementation as any)?.$dependencies ?? [];
        for (const dep of deps) {
          localMax = Math.max(localMax, computeDepth(dep, currentDepth + 1, new Set(seen)));
        }
      }
      return localMax;
    };

    for (const root of rootServices) {
      const depth = computeDepth(root, 1, new Set());
      maxDepth = Math.max(maxDepth, depth);
      totalDepthSum += depth;
    }

    const averageDepth = rootServices.length > 0 ? totalDepthSum / rootServices.length : 0;

    const graph = createDependencyGraph({
      nodes: descriptors.map((d) => nodeMap.get(d.serviceType)!),
      edges,
    });

    const statistics = createGraphStatistics({
      nodeCount: descriptors.length,
      edgeCount: edges.length,
      rootServices,
      leafServices,
      orphanServices,
      circularDependencies: cycles,
      averageDepth: Number(averageDepth.toFixed(2)),
      maxDepth,
    });

    const hasErrors = issues.some((i) => i.severity === 'error');

    return createDependencyAnalysis({
      graph,
      statistics,
      issues,
      healthy: !hasErrors,
    });
  }

  public validate(collection: IServiceCollection): ReadonlyArray<DependencyIssue> {
    return this.analyze(collection).issues;
  }

  public certify(collection: IServiceCollection): DependencyCertification {
    const analysis = this.analyze(collection);
    const errors = analysis.issues.filter((i) => i.severity === 'error');
    const warnings = analysis.issues.filter((i) => i.severity === 'warning');

    const certified = errors.length === 0;
    const productionReady = certified && warnings.length === 0;

    const summary = certified
      ? productionReady
        ? 'Certified Production Ready: Dependency graph is clean, fully resolved, and error-free.'
        : `Certified with Warnings: Dependency graph is healthy with ${warnings.length} warning(s).`
      : `Certification Failed: ${errors.length} error(s) found in dependency graph.`;

    return createDependencyCertification({
      certified,
      productionReady,
      generatedAt: new Date().toISOString(),
      analysis,
      summary,
    });
  }

  public exportGraph(
    analysis: DependencyAnalysis,
    format: 'mermaid' | 'dot' | 'adjacency-list' | 'adjacency-map',
  ): string {
    const edges = analysis.graph.edges;
    const nodes = analysis.graph.nodes;

    if (format === 'mermaid') {
      const lines: string[] = ['graph TD'];
      for (const edge of edges) {
        lines.push(`  ${edge.source} --> ${edge.target}`);
      }
      return lines.join('\n');
    }

    if (format === 'dot') {
      const lines: string[] = ['digraph G {'];
      for (const edge of edges) {
        lines.push(`  "${edge.source}" -> "${edge.target}";`);
      }
      lines.push('}');
      return lines.join('\n');
    }

    if (format === 'adjacency-list') {
      const adj: Record<string, string[]> = {};
      for (const n of nodes) {
        adj[n.serviceType] = [];
      }
      for (const e of edges) {
        if (!adj[e.source]) adj[e.source] = [];
        adj[e.source].push(e.target);
      }
      return Object.entries(adj)
        .map(([k, v]) => `${k}: ${v.join(', ')}`)
        .join('\n');
    }

    if (format === 'adjacency-map') {
      const adj: Record<string, string[]> = {};
      for (const n of nodes) {
        adj[n.serviceType] = [];
      }
      for (const e of edges) {
        if (!adj[e.source]) adj[e.source] = [];
        adj[e.source].push(e.target);
      }
      return JSON.stringify(adj, null, 2);
    }

    throw new Error(`Unsupported export format: ${format}`);
  }
}
