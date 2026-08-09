import type { PluginManifest } from '../models/manifest';
import type { PluginDependencyGraph, PluginDependencyNode, PluginDependencyEdge, PluginDependency } from '../models/dependency';
import { freezeDeepSafe } from '../models/dependency';

export class PluginDependencyGraphBuilder {
  public static build(manifests: ReadonlyArray<PluginManifest>): PluginDependencyGraph {
    const nodes = new Map<string, PluginDependencyNode>();
    const edges: PluginDependencyEdge[] = [];

    // Sort manifests by ID to ensure deterministic insertion order
    const sortedManifests = [...manifests].sort((a, b) => a.id.localeCompare(b.id));

    // Create nodes
    for (const manifest of sortedManifests) {
      const dependencies: PluginDependency[] = manifest.dependencies.map(d => ({
        id: d.id,
        versionRange: d.versionRange,
        optional: d.optional === true
      }));

      nodes.set(manifest.id, {
        id: manifest.id,
        manifest,
        dependencies: Object.freeze(dependencies)
      });
    }

    // Create edges (deterministically sorted by from and to)
    for (const node of nodes.values()) {
      for (const dep of node.dependencies) {
        edges.push({
          from: node.id,
          to: dep.id,
          required: !dep.optional,
          versionRange: dep.versionRange
        });
      }
    }

    // Sort edges to ensure determinism
    edges.sort((a, b) => {
      const cmp = a.from.localeCompare(b.from);
      if (cmp !== 0) return cmp;
      return a.to.localeCompare(b.to);
    });

    const graph: PluginDependencyGraph = {
      nodes,
      edges
    };

    return freezeDeepSafe(graph);
  }
}
