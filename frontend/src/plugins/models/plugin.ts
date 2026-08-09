import { PluginState, type PluginStateValue } from './plugin-state';

export type PluginId = string;
export type PluginName = string;
export type PluginVersion = string;

export type PluginCapabilityId = 'command' | 'event' | 'service' | 'ui' | 'storage';

export interface PluginMetadata {
  readonly [key: string]: unknown;
}

export interface IPlugin {
  readonly id: PluginId;
  readonly name: PluginName;
  readonly version: PluginVersion;
  readonly description?: string;
  readonly author?: string;
  readonly enabled: boolean;
  readonly metadata: PluginMetadata;
  readonly state: PluginStateValue;
}

export interface PluginInput extends Partial<Pick<IPlugin, 'description' | 'author' | 'enabled' | 'metadata' | 'state'>> {
  readonly id: PluginId;
  readonly name: PluginName;
  readonly version: PluginVersion;
}

function freezeDeep<T>(value: T): T {
  if (Array.isArray(value)) {
    const arrayValue = value.map((item) => freezeDeep(item));
    return Object.freeze(arrayValue) as T;
  }

  if (value && typeof value === 'object') {
    const objectValue = value as Record<string, unknown>;
    Object.keys(objectValue).forEach((key) => {
      const nestedValue = objectValue[key];
      if (nestedValue && typeof nestedValue === 'object') {
        objectValue[key] = freezeDeep(nestedValue);
      }
    });
    return Object.freeze(objectValue) as T;
  }

  return value;
}

export function createPlugin(input: PluginInput): IPlugin {
  const plugin: IPlugin = {
    id: input.id,
    name: input.name,
    version: input.version,
    description: input.description,
    author: input.author,
    enabled: input.enabled ?? true,
    metadata: freezeDeep({ ...(input.metadata ?? {}) }),
    state: input.state ?? PluginState.UNREGISTERED,
  };

  return freezeDeep(plugin);
}
