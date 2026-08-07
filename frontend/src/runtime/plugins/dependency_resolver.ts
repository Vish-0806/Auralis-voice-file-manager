/**
 * Dependency Resolver Engine (Phase 16.7).
 *
 * Implements IDependencyResolver to build plugin dependency graphs,
 * detect circular references, determine topological load order, and check
 * version ranges.
 */

import {
  PluginDescriptor,
  PluginResolutionResult,
  createPluginResolutionResult,
} from './models';
import { IDependencyResolver } from './interfaces';
import { PluginDependencyException } from './exceptions';
import { PluginManifestLoader } from './plugin_manifest';

export class DependencyResolver implements IDependencyResolver {
  private readonly _manifestLoader = new PluginManifestLoader();

  public resolveDependencies(plugins: ReadonlyArray<PluginDescriptor>): PluginResolutionResult {
    const pluginsMap = new Map<string, PluginDescriptor>();
    plugins.forEach(p => pluginsMap.set(p.id, p));

    const missingRequired: string[] = [];
    const missingOptional: string[] = [];
    let circularDetected = false;
    const loadOrder: string[] = [];

    // Verify dependencies and version constraints
    for (const plugin of plugins) {
      for (const dep of plugin.manifest.dependencies) {
        const target = pluginsMap.get(dep.id);
        if (!target) {
          if (dep.optional) {
            missingOptional.push(`${plugin.id} -> ${dep.id} (optional)`);
          } else {
            missingRequired.push(`${plugin.id} -> ${dep.id} (required)`);
          }
        } else {
          // Version range check
          const versionMatch = this._manifestLoader.satisfiesRange(target.manifest.version, dep.versionRange);
          if (!versionMatch) {
            const errStr = `${plugin.id} requires ${dep.id} @ ${dep.versionRange}, but found ${target.manifest.version}`;
            if (dep.optional) {
              missingOptional.push(errStr);
            } else {
              missingRequired.push(errStr);
            }
          }
        }
      }
    }

    // Circular Dependency Detection
    const visited = new Set<string>();
    const stack = new Set<string>();

    for (const plugin of plugins) {
      if (!visited.has(plugin.id)) {
        if (this.checkCircular(plugin.id, pluginsMap, visited, stack)) {
          circularDetected = true;
          break;
        }
      }
    }

    if (circularDetected) {
      throw new PluginDependencyException('Circular dependency detected in plugin graph.');
    }

    // Topological Sort
    const sortedVisited = new Set<string>();
    for (const plugin of plugins) {
      if (!sortedVisited.has(plugin.id)) {
        this.topologicalSort(plugin.id, pluginsMap, sortedVisited, loadOrder);
      }
    }

    return createPluginResolutionResult({
      pluginId: 'resolver',
      resolved: missingRequired.length === 0 && !circularDetected,
      missingRequired,
      missingOptional,
      circularDetected,
      loadOrder,
    });
  }

  public checkCircular(
    pluginId: string,
    pluginsMap: Map<string, PluginDescriptor>,
    visited: Set<string>,
    stack: Set<string>,
  ): boolean {
    visited.add(pluginId);
    stack.add(pluginId);

    const plugin = pluginsMap.get(pluginId);
    if (plugin) {
      for (const dep of plugin.manifest.dependencies) {
        if (stack.has(dep.id)) {
          return true;
        }
        if (!visited.has(dep.id)) {
          if (this.checkCircular(dep.id, pluginsMap, visited, stack)) {
            return true;
          }
        }
      }
    }

    stack.delete(pluginId);
    return false;
  }

  public topologicalSort(
    pluginId: string,
    pluginsMap: Map<string, PluginDescriptor>,
    visited: Set<string>,
    result: string[],
  ): void {
    visited.add(pluginId);

    const plugin = pluginsMap.get(pluginId);
    if (plugin) {
      for (const dep of plugin.manifest.dependencies) {
        if (!visited.has(dep.id)) {
          this.topologicalSort(dep.id, pluginsMap, visited, result);
        }
      }
    }

    result.push(pluginId);
  }
}
