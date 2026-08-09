import type { IPlugin, PluginInput } from '../models/plugin';
import { PluginProvider } from '../provider/PluginProvider';
import { PluginRuntime } from '../runtime/PluginRuntime';

export function createPlugin(input: PluginInput): IPlugin {
  return {
    id: input.id,
    name: input.name,
    version: input.version,
    description: input.description,
    author: input.author,
    enabled: input.enabled ?? true,
    metadata: { ...(input.metadata ?? {}) },
    state: input.state ?? 'UNREGISTERED',
  };
}

export function createPluginProvider(): PluginProvider {
  return new PluginProvider();
}

export function createPluginRuntime(): PluginRuntime {
  return new PluginRuntime();
}
