/**
 * Command Registry Implementation (Phase 16.6.2).
 *
 * Provides central registration, high-performance lookup, alias resolution,
 * metadata management, category filtering, search engine ranking, telemetry
 * statistics, and health reporting for all command definitions.
 */

import {
  CommandAlias,
  CommandCategory,
  CommandDefinition,
  CommandRegistration,
  CommandRegistryHealth,
  CommandRegistryStatistics,
  createCommandAlias,
  createCommandCategory,
  createCommandDefinition,
  createCommandRegistryHealth,
  createCommandRegistryStatistics,
} from './models';
import { CommandProviderException } from './exceptions';
import { ICommandRegistry } from './interfaces';

const DEFAULT_CATEGORIES: ReadonlyArray<string> = [
  'Filesystem',
  'Navigation',
  'Clipboard',
  'Compression',
  'Search',
  'Voice',
  'AI',
  'Settings',
  'Developer',
  'Diagnostics',
];

export class CommandRegistry implements ICommandRegistry {
  private readonly _commands = new Map<string, CommandDefinition>();
  private readonly _aliases = new Map<string, string>(); // alias -> commandId

  private _removedCommandsCount = 0;
  private _updatesCount = 0;
  private _lookupsCount = 0;
  private _failedLookupsCount = 0;
  private _searchesCount = 0;
  private _duplicateAttemptsCount = 0;
  private _invalidRegistrationsCount = 0;

  public registerCommand(registration: CommandRegistration | CommandDefinition): CommandDefinition {
    if (!registration) {
      this._invalidRegistrationsCount++;
      throw new CommandProviderException('Command registration cannot be null or undefined.');
    }

    if (!registration.id || !registration.id.trim()) {
      this._invalidRegistrationsCount++;
      throw new CommandProviderException('Command registration ID cannot be empty.');
    }

    if (!registration.displayName || !registration.displayName.trim()) {
      this._invalidRegistrationsCount++;
      throw new CommandProviderException('Command registration displayName cannot be empty.');
    }

    const commandId = registration.id.trim();

    if (this._commands.has(commandId)) {
      this._duplicateAttemptsCount++;
      throw new CommandProviderException(`Command ID '${commandId}' is already registered.`);
    }

    // Duplicate name check
    const normalizedName = registration.displayName.trim().toLowerCase();
    for (const existing of this._commands.values()) {
      if (existing.displayName.trim().toLowerCase() === normalizedName) {
        this._duplicateAttemptsCount++;
        throw new CommandProviderException(
          `Command with name '${registration.displayName}' is already registered.`,
        );
      }
    }

    // Duplicate alias check
    if (registration.aliases) {
      for (const alias of registration.aliases) {
        if (!alias || !alias.trim()) continue;
        const normalizedAlias = alias.trim().toLowerCase();
        if (this._aliases.has(normalizedAlias)) {
          const mappedCmdId = this._aliases.get(normalizedAlias)!;
          this._duplicateAttemptsCount++;
          throw new CommandProviderException(
            `Alias '${alias}' is already registered to command '${mappedCmdId}'.`,
          );
        }
      }
    }

    const definition = createCommandDefinition({
      id: commandId,
      displayName: registration.displayName.trim(),
      description: registration.description,
      category: registration.category,
      aliases: registration.aliases,
      parameters: registration.parameters,
      examples: registration.examples,
      version: registration.version,
      enabled: registration.enabled,
      hidden: registration.hidden,
      experimental: registration.experimental,
      deprecated: registration.deprecated,
      permission: registration.permission,
      tags: registration.tags,
    });

    this._commands.set(commandId, definition);

    for (const alias of definition.aliases) {
      if (alias && alias.trim()) {
        this._aliases.set(alias.trim().toLowerCase(), commandId);
      }
    }

    return definition;
  }

  public removeCommand(commandId: string): boolean {
    if (!commandId || !commandId.trim()) {
      return false;
    }

    const id = commandId.trim();
    const existing = this._commands.get(id);

    if (!existing) {
      return false;
    }

    this._commands.delete(id);

    for (const alias of existing.aliases) {
      if (alias && alias.trim()) {
        this._aliases.delete(alias.trim().toLowerCase());
      }
    }

    this._removedCommandsCount++;
    return true;
  }

  public updateCommand(
    commandId: string,
    updates: Partial<CommandDefinition>,
  ): CommandDefinition {
    if (!commandId || !commandId.trim()) {
      throw new CommandProviderException('Command ID cannot be empty.');
    }

    const id = commandId.trim();
    const existing = this._commands.get(id);

    if (!existing) {
      throw new CommandProviderException(`Cannot update command '${id}': command not found.`);
    }

    if (updates.displayName && updates.displayName.trim()) {
      const newName = updates.displayName.trim().toLowerCase();
      if (newName !== existing.displayName.trim().toLowerCase()) {
        for (const [otherId, otherCmd] of this._commands.entries()) {
          if (otherId !== id && otherCmd.displayName.trim().toLowerCase() === newName) {
            this._duplicateAttemptsCount++;
            throw new CommandProviderException(
              `Command with name '${updates.displayName}' is already registered.`,
            );
          }
        }
      }
    }

    if (updates.aliases) {
      for (const alias of updates.aliases) {
        if (!alias || !alias.trim()) continue;
        const normalizedAlias = alias.trim().toLowerCase();
        const existingMapped = this._aliases.get(normalizedAlias);
        if (existingMapped && existingMapped !== id) {
          this._duplicateAttemptsCount++;
          throw new CommandProviderException(
            `Alias '${alias}' is already registered to command '${existingMapped}'.`,
          );
        }
      }

      for (const oldAlias of existing.aliases) {
        if (oldAlias && oldAlias.trim()) {
          this._aliases.delete(oldAlias.trim().toLowerCase());
        }
      }

      for (const newAlias of updates.aliases) {
        if (newAlias && newAlias.trim()) {
          this._aliases.set(newAlias.trim().toLowerCase(), id);
        }
      }
    }

    const updatedDefinition = createCommandDefinition({
      ...existing,
      ...updates,
      id,
      displayName: updates.displayName ? updates.displayName.trim() : existing.displayName,
      aliases: updates.aliases ? updates.aliases : existing.aliases,
    });

    this._commands.set(id, updatedDefinition);
    this._updatesCount++;

    return updatedDefinition;
  }

  public containsCommand(commandId: string): boolean {
    if (!commandId || !commandId.trim()) {
      return false;
    }
    return this._commands.has(commandId.trim());
  }

  public findCommand(commandId: string): CommandDefinition | undefined {
    if (!commandId || !commandId.trim()) {
      this._failedLookupsCount++;
      return undefined;
    }

    const cmd = this._commands.get(commandId.trim());
    if (cmd) {
      this._lookupsCount++;
      return cmd;
    }

    this._failedLookupsCount++;
    return undefined;
  }

  public findByAlias(alias: string): CommandDefinition | undefined {
    if (!alias || !alias.trim()) {
      this._failedLookupsCount++;
      return undefined;
    }

    const normalizedAlias = alias.trim().toLowerCase();
    const commandId = this._aliases.get(normalizedAlias);

    if (!commandId) {
      this._failedLookupsCount++;
      return undefined;
    }

    return this.findCommand(commandId);
  }

  public findByName(name: string): CommandDefinition | undefined {
    if (!name || !name.trim()) {
      this._failedLookupsCount++;
      return undefined;
    }

    const normalizedName = name.trim().toLowerCase();
    for (const cmd of this._commands.values()) {
      if (cmd.displayName.trim().toLowerCase() === normalizedName) {
        this._lookupsCount++;
        return cmd;
      }
    }

    this._failedLookupsCount++;
    return undefined;
  }

  public listCommands(category?: string): ReadonlyArray<CommandDefinition> {
    const all = Array.from(this._commands.values());
    if (!category || !category.trim()) {
      return Object.freeze(all);
    }

    const normalizedCategory = category.trim().toLowerCase();
    const filtered = all.filter(
      (cmd) => cmd.category.trim().toLowerCase() === normalizedCategory,
    );
    return Object.freeze(filtered);
  }

  public listAliases(): ReadonlyArray<CommandAlias> {
    const list: CommandAlias[] = [];
    for (const [alias, commandId] of this._aliases.entries()) {
      list.push(createCommandAlias({ alias, commandId }));
    }
    return Object.freeze(list);
  }

  public listCategories(): ReadonlyArray<CommandCategory> {
    const categoryCounts = new Map<string, number>();

    for (const catName of DEFAULT_CATEGORIES) {
      categoryCounts.set(catName, 0);
    }

    for (const cmd of this._commands.values()) {
      const catName = cmd.category ? cmd.category.trim() : 'General';
      const current = categoryCounts.get(catName) ?? 0;
      categoryCounts.set(catName, current + 1);
    }

    const result: CommandCategory[] = [];
    for (const [name, commandCount] of categoryCounts.entries()) {
      result.push(createCommandCategory({ name, commandCount }));
    }

    return Object.freeze(result);
  }

  public search(query: string): ReadonlyArray<CommandDefinition> {
    this._searchesCount++;

    if (!query || !query.trim()) {
      return Object.freeze(Array.from(this._commands.values()));
    }

    const q = query.trim().toLowerCase();
    const matches: Array<{ cmd: CommandDefinition; score: number }> = [];

    for (const cmd of this._commands.values()) {
      let score = 0;
      const idLower = cmd.id.toLowerCase();
      const nameLower = cmd.displayName.toLowerCase();
      const catLower = cmd.category.toLowerCase();
      const descLower = cmd.description.toLowerCase();

      if (idLower === q) score += 100;
      else if (idLower.startsWith(q)) score += 80;
      else if (idLower.includes(q)) score += 60;

      if (nameLower === q) score += 95;
      else if (nameLower.startsWith(q)) score += 75;
      else if (nameLower.includes(q)) score += 55;

      for (const alias of cmd.aliases) {
        const aliasLower = alias.toLowerCase();
        if (aliasLower === q) score += 90;
        else if (aliasLower.startsWith(q)) score += 70;
        else if (aliasLower.includes(q)) score += 50;
      }

      if (catLower.includes(q)) score += 40;

      if (cmd.tags) {
        for (const tag of cmd.tags) {
          if (tag.toLowerCase().includes(q)) {
            score += 30;
          }
        }
      }

      if (descLower.includes(q)) score += 20;

      if (score > 0) {
        matches.push({ cmd, score });
      }
    }

    matches.sort((a, b) => {
      if (b.score !== a.score) {
        return b.score - a.score;
      }
      return a.cmd.displayName.localeCompare(b.cmd.displayName);
    });

    return Object.freeze(matches.map((m) => m.cmd));
  }

  public statistics(): CommandRegistryStatistics {
    const categories = this.listCategories();
    const activeCategoryCount = categories.filter((c) => c.commandCount > 0).length;

    return createCommandRegistryStatistics({
      registeredCommands: this._commands.size,
      removedCommands: this._removedCommandsCount,
      updates: this._updatesCount,
      lookups: this._lookupsCount,
      failedLookups: this._failedLookupsCount,
      searches: this._searchesCount,
      duplicateAttempts: this._duplicateAttemptsCount,
      categoryCount: activeCategoryCount,
      aliasCount: this._aliases.size,
    });
  }

  public health(): CommandRegistryHealth {
    let missingMetadata = 0;

    for (const cmd of this._commands.values()) {
      if (!cmd.id || !cmd.displayName || !cmd.category) {
        missingMetadata++;
      }
    }

    const healthy =
      this._duplicateAttemptsCount === 0 &&
      this._invalidRegistrationsCount === 0 &&
      missingMetadata === 0;

    const message = healthy
      ? 'Command registry is fully operational and healthy.'
      : `Command registry operational with issues (duplicateAttempts: ${this._duplicateAttemptsCount}, missingMetadata: ${missingMetadata}, invalidRegistrations: ${this._invalidRegistrationsCount}).`;

    return createCommandRegistryHealth({
      healthy,
      duplicateIds: 0,
      duplicateAliases: 0,
      missingMetadata,
      orphanCategories: 0,
      invalidRegistrations: this._invalidRegistrationsCount,
      message,
    });
  }

  public clear(): void {
    this._commands.clear();
    this._aliases.clear();
    this._removedCommandsCount = 0;
    this._updatesCount = 0;
    this._lookupsCount = 0;
    this._failedLookupsCount = 0;
    this._searchesCount = 0;
    this._duplicateAttemptsCount = 0;
    this._invalidRegistrationsCount = 0;
  }
}
