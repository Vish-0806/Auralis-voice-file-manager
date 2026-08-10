import type { IPluginConfigurationStore } from '../interfaces/plugin-configuration';
import type { PluginConfiguration } from '../models/configuration';
import { freezeDeepSafe } from '../models/dependency';

export class InMemoryPluginConfigurationStore implements IPluginConfigurationStore {
  private readonly data = new Map<string, PluginConfiguration>();

  public readOperations = 0;
  public writeOperations = 0;
  public removeOperations = 0;

  public async read(pluginId: string): Promise<PluginConfiguration | null> {
    this.readOperations += 1;
    const config = this.data.get(pluginId);
    return config ? freezeDeepSafe(config) : null;
  }

  public async write(pluginId: string, config: PluginConfiguration): Promise<void> {
    this.writeOperations += 1;
    this.data.set(pluginId, freezeDeepSafe(config));
  }

  public async remove(pluginId: string): Promise<void> {
    this.removeOperations += 1;
    this.data.delete(pluginId);
  }

  public async exists(pluginId: string): Promise<boolean> {
    return this.data.has(pluginId);
  }

  public clear(): void {
    this.data.clear();
    this.readOperations = 0;
    this.writeOperations = 0;
    this.removeOperations = 0;
  }
}
