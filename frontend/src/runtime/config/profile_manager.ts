/**
 * Configuration Profile Manager (Phase 16.3.4).
 *
 * Manages configuration profiles (development, testing, production), activation,
 * parent profile inheritance override merging, profile snapshots, and telemetry.
 */

import {
  ConfigurationProfileDefinition,
  ConfigurationProfileSnapshot,
  createConfigurationProfileDefinition,
  createConfigurationProfileSnapshot,
  createProfileHealth,
  createProfileStatistics,
  ProfileHealth,
  ProfileStatistics,
} from './models';
import { ConfigurationProviderException } from './exceptions';

export class ProfileManager {
  private readonly _profiles = new Map<string, ConfigurationProfileDefinition>();
  private _activeProfileName = 'production';

  private _registrations = 0;
  private _activations = 0;

  constructor() {
    this.registerDefaultProfiles();
  }

  public registerProfile(profile: ConfigurationProfileDefinition): void {
    if (!profile) {
      throw new ConfigurationProviderException('Profile definition cannot be null or undefined.');
    }
    const name = profile.profileName.trim();
    if (!name) {
      throw new ConfigurationProviderException('Profile name cannot be empty.');
    }
    if (this._profiles.has(name)) {
      throw new ConfigurationProviderException(`Profile '${name}' is already registered.`);
    }

    this._profiles.set(name, profile);
    this._registrations++;

    if (profile.active) {
      this.activateProfile(name);
    }
  }

  public activateProfile(profileName: string): void {
    const key = profileName.trim();
    const target = this._profiles.get(key);
    if (!target) {
      throw new ConfigurationProviderException(`Profile '${profileName}' is not registered.`);
    }

    this._activeProfileName = key;
    this._activations++;

    for (const [name, prof] of Array.from(this._profiles.entries())) {
      this._profiles.set(
        name,
        createConfigurationProfileDefinition({
          ...prof,
          active: name === key,
        }),
      );
    }
  }

  public getActiveProfile(): ConfigurationProfileDefinition | undefined {
    return this._profiles.get(this._activeProfileName);
  }

  public getProfile(profileName: string): ConfigurationProfileDefinition | undefined {
    return this._profiles.get(profileName.trim());
  }

  public getMergedOverrides(): Readonly<Record<string, unknown>> {
    const active = this.getActiveProfile();
    if (!active) return Object.freeze({});

    const chain: ConfigurationProfileDefinition[] = [];
    let current: ConfigurationProfileDefinition | undefined = active;
    const visited = new Set<string>();

    while (current && !visited.has(current.profileName)) {
      visited.add(current.profileName);
      chain.unshift(current); // Parent goes first
      if (current.parentProfileName) {
        current = this._profiles.get(current.parentProfileName);
      } else {
        current = undefined;
      }
    }

    const merged: Record<string, unknown> = {};
    for (const prof of chain) {
      if (prof.overrides) {
        for (const [k, v] of Object.entries(prof.overrides)) {
          merged[k] = v;
        }
      }
    }

    return Object.freeze(merged);
  }

  public createSnapshot(): ConfigurationProfileSnapshot {
    return createConfigurationProfileSnapshot({
      activeProfileName: this._activeProfileName,
      mergedOverrides: this.getMergedOverrides(),
      registeredProfiles: Array.from(this._profiles.keys()),
      timestamp: new Date().toISOString(),
    });
  }

  public listProfiles(): ReadonlyArray<ConfigurationProfileDefinition> {
    return Object.freeze(Array.from(this._profiles.values()));
  }

  public statistics(): ProfileStatistics {
    const merged = this.getMergedOverrides();
    return createProfileStatistics({
      registrations: this._registrations,
      activations: this._activations,
      overrideKeysCount: Object.keys(merged).length,
    });
  }

  public health(): ProfileHealth {
    return createProfileHealth({
      healthy: this._profiles.has(this._activeProfileName),
      activeProfileName: this._activeProfileName,
      totalProfiles: this._profiles.size,
    });
  }

  private registerDefaultProfiles(): void {
    this.registerProfile(
      createConfigurationProfileDefinition({
        profileType: 'environment',
        profileName: 'development',
        priority: 100,
        active: false,
        overrides: { 'debug.enabled': true, 'log.level': 'debug' },
      }),
    );

    this.registerProfile(
      createConfigurationProfileDefinition({
        profileType: 'environment',
        profileName: 'testing',
        priority: 200,
        active: false,
        overrides: { 'debug.enabled': true, 'log.level': 'info' },
      }),
    );

    this.registerProfile(
      createConfigurationProfileDefinition({
        profileType: 'environment',
        profileName: 'production',
        priority: 300,
        active: true,
        overrides: { 'debug.enabled': false, 'log.level': 'warn' },
      }),
    );
  }
}
