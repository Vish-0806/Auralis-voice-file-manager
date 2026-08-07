import { beforeEach, describe, expect, it } from 'vitest';
import {
  CommandProvider,
  CommandProviderException,
  CommandRegistry,
  CommandRuntime,
  createCommandAlias,
  createCommandCategory,
  createCommandDefinition,
  createCommandDiagnostics,
  createCommandParameter,
  createCommandRegistration,
  createCommandRegistryHealth,
  createCommandRegistryStatistics,
  getCommandRuntime,
  resetCommandProvider,
  resetCommandRuntime,
} from '../../src/runtime/commands';

describe('Phase 16.6.2 — Frontend Command Registry & Command Registration Engine', () => {
  let registry: CommandRegistry;

  beforeEach(() => {
    resetCommandRuntime();
    resetCommandProvider();
    registry = new CommandRegistry();
  });

  describe('1. Immutable Domain Models & Factory Functions', () => {
    it('should create immutable CommandParameter model', () => {
      const param = createCommandParameter({
        name: 'filePath',
        type: 'string',
        required: true,
        description: 'Target file path',
      });

      expect(param.name).toBe('filePath');
      expect(param.type).toBe('string');
      expect(param.required).toBe(true);
      expect(param.description).toBe('Target file path');
      expect(Object.isFrozen(param)).toBe(true);
    });

    it('should create CommandParameter with default values', () => {
      const param = createCommandParameter({ name: 'count' });
      expect(param.name).toBe('count');
      expect(param.type).toBe('any');
      expect(param.required).toBe(false);
      expect(Object.isFrozen(param)).toBe(true);
    });

    it('should create immutable CommandDefinition model', () => {
      const def = createCommandDefinition({
        id: 'open_downloads',
        displayName: 'Open Downloads Folder',
        description: 'Navigates to user downloads directory',
        category: 'Navigation',
        aliases: ['downloads', 'my downloads'],
        tags: ['fs', 'downloads'],
      });

      expect(def.id).toBe('open_downloads');
      expect(def.displayName).toBe('Open Downloads Folder');
      expect(def.description).toBe('Navigates to user downloads directory');
      expect(def.category).toBe('Navigation');
      expect(def.aliases).toEqual(['downloads', 'my downloads']);
      expect(def.tags).toEqual(['fs', 'downloads']);
      expect(def.enabled).toBe(true);
      expect(def.hidden).toBe(false);
      expect(def.experimental).toBe(false);
      expect(def.deprecated).toBe(false);
      expect(Object.isFrozen(def)).toBe(true);
      expect(Object.isFrozen(def.aliases)).toBe(true);
    });

    it('should create immutable CommandAlias model', () => {
      const alias = createCommandAlias({ alias: 'dl', commandId: 'open_downloads' });
      expect(alias.alias).toBe('dl');
      expect(alias.commandId).toBe('open_downloads');
      expect(Object.isFrozen(alias)).toBe(true);
    });

    it('should create immutable CommandCategory model', () => {
      const cat = createCommandCategory({ name: 'Filesystem', commandCount: 5 });
      expect(cat.name).toBe('Filesystem');
      expect(cat.commandCount).toBe(5);
      expect(Object.isFrozen(cat)).toBe(true);
    });

    it('should create immutable CommandRegistration model', () => {
      const reg = createCommandRegistration({
        id: 'copy_file',
        displayName: 'Copy File',
        category: 'Filesystem',
      });
      expect(reg.id).toBe('copy_file');
      expect(reg.displayName).toBe('Copy File');
      expect(reg.category).toBe('Filesystem');
      expect(reg.registeredAt).toBeDefined();
      expect(Object.isFrozen(reg)).toBe(true);
    });

    it('should create immutable CommandRegistryStatistics model', () => {
      const stats = createCommandRegistryStatistics({ registeredCommands: 10, searches: 5 });
      expect(stats.registeredCommands).toBe(10);
      expect(stats.searches).toBe(5);
      expect(stats.removedCommands).toBe(0);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should create immutable CommandRegistryHealth model', () => {
      const health = createCommandRegistryHealth({ healthy: true, duplicateIds: 0 });
      expect(health.healthy).toBe(true);
      expect(health.duplicateIds).toBe(0);
      expect(health.message).toBeDefined();
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should create immutable CommandDiagnostics with registry data', () => {
      const stats = createCommandRegistryStatistics({ registeredCommands: 2 });
      const health = createCommandRegistryHealth({ healthy: true });
      const diag = createCommandDiagnostics({
        registeredCommands: ['cmd_1', 'cmd_2'],
        registryStatistics: stats,
        registryHealth: health,
      });

      expect(diag.registeredCommands).toEqual(['cmd_1', 'cmd_2']);
      expect(diag.registryStatistics?.registeredCommands).toBe(2);
      expect(diag.registryHealth?.healthy).toBe(true);
      expect(Object.isFrozen(diag)).toBe(true);
    });
  });

  describe('2. Command Registration & Validation', () => {
    it('should successfully register a valid command', () => {
      const def = registry.registerCommand({
        id: 'file_copy',
        displayName: 'Copy Selected File',
        description: 'Copies file to clipboard',
        category: 'Filesystem',
      });

      expect(def.id).toBe('file_copy');
      expect(def.displayName).toBe('Copy Selected File');
      expect(registry.containsCommand('file_copy')).toBe(true);
    });

    it('should throw CommandProviderException when registering null or undefined', () => {
      expect(() => registry.registerCommand(null as any)).toThrow(CommandProviderException);
      expect(() => registry.registerCommand(undefined as any)).toThrow(CommandProviderException);
    });

    it('should throw CommandProviderException when ID is empty or whitespace', () => {
      expect(() => registry.registerCommand({ id: '', displayName: 'Test' })).toThrow(
        CommandProviderException,
      );
      expect(() => registry.registerCommand({ id: '   ', displayName: 'Test' })).toThrow(
        CommandProviderException,
      );
    });

    it('should throw CommandProviderException when displayName is empty or whitespace', () => {
      expect(() => registry.registerCommand({ id: 'cmd_1', displayName: '' })).toThrow(
        CommandProviderException,
      );
      expect(() => registry.registerCommand({ id: 'cmd_1', displayName: '  ' })).toThrow(
        CommandProviderException,
      );
    });

    it('should return frozen CommandDefinition upon registration', () => {
      const def = registry.registerCommand({
        id: 'cmd_freeze',
        displayName: 'Freeze Test',
      });
      expect(Object.isFrozen(def)).toBe(true);
    });
  });

  describe('3. Duplicate Rejection Validation', () => {
    it('should reject duplicate command ID and throw CommandProviderException', () => {
      registry.registerCommand({ id: 'move_file', displayName: 'Move File' });

      expect(() =>
        registry.registerCommand({ id: 'move_file', displayName: 'Move File 2' }),
      ).toThrow(CommandProviderException);

      expect(registry.statistics().duplicateAttempts).toBe(1);
    });

    it('should reject duplicate command name and throw CommandProviderException', () => {
      registry.registerCommand({ id: 'rename_file', displayName: 'Rename File' });

      expect(() =>
        registry.registerCommand({ id: 'rename_file_2', displayName: 'Rename File' }),
      ).toThrow(CommandProviderException);

      expect(registry.statistics().duplicateAttempts).toBe(1);
    });

    it('should reject duplicate name case-insensitively', () => {
      registry.registerCommand({ id: 'open_search', displayName: 'Search Files' });

      expect(() =>
        registry.registerCommand({ id: 'search_2', displayName: 'search files' }),
      ).toThrow(CommandProviderException);
    });

    it('should reject duplicate alias across commands and throw CommandProviderException', () => {
      registry.registerCommand({
        id: 'downloads_open',
        displayName: 'Open Downloads',
        aliases: ['dl', 'downloads'],
      });

      expect(() =>
        registry.registerCommand({
          id: 'downloads_show',
          displayName: 'Show Downloads',
          aliases: ['dl'],
        }),
      ).toThrow(CommandProviderException);

      expect(registry.statistics().duplicateAttempts).toBe(1);
    });

    it('should never silently overwrite existing command registration', () => {
      registry.registerCommand({ id: 'c1', displayName: 'Original Name' });

      try {
        registry.registerCommand({ id: 'c1', displayName: 'New Name' });
      } catch {
        // expected
      }

      const existing = registry.findCommand('c1');
      expect(existing?.displayName).toBe('Original Name');
    });
  });

  describe('4. Command Removal', () => {
    it('should remove existing command by ID', () => {
      registry.registerCommand({ id: 'delete_file', displayName: 'Delete File' });
      expect(registry.containsCommand('delete_file')).toBe(true);

      const removed = registry.removeCommand('delete_file');
      expect(removed).toBe(true);
      expect(registry.containsCommand('delete_file')).toBe(false);
      expect(registry.statistics().removedCommands).toBe(1);
    });

    it('should remove associated aliases when command is removed', () => {
      registry.registerCommand({
        id: 'compress_zip',
        displayName: 'Zip Files',
        aliases: ['zip', 'compress'],
      });

      expect(registry.findByAlias('zip')).toBeDefined();

      registry.removeCommand('compress_zip');
      expect(registry.findByAlias('zip')).toBeUndefined();
      expect(registry.findByAlias('compress')).toBeUndefined();
    });

    it('should return false when removing non-existent command', () => {
      const removed = registry.removeCommand('non_existent');
      expect(removed).toBe(false);
    });

    it('should return false when command ID is empty', () => {
      expect(registry.removeCommand('')).toBe(false);
      expect(registry.removeCommand('  ')).toBe(false);
    });
  });

  describe('5. Command Updating', () => {
    it('should update command definition properties', () => {
      registry.registerCommand({
        id: 'file_edit',
        displayName: 'Edit File',
        description: 'Old Description',
      });

      const updated = registry.updateCommand('file_edit', {
        description: 'New Description',
      });

      expect(updated.description).toBe('New Description');
      expect(updated.displayName).toBe('Edit File');
      expect(registry.findCommand('file_edit')?.description).toBe('New Description');
      expect(registry.statistics().updates).toBe(1);
    });

    it('should throw CommandProviderException when updating non-existent command', () => {
      expect(() =>
        registry.updateCommand('unknown', { displayName: 'Updated' }),
      ).toThrow(CommandProviderException);
    });

    it('should update aliases and re-map lookup table', () => {
      registry.registerCommand({
        id: 'nav_home',
        displayName: 'Go Home',
        aliases: ['home'],
      });

      expect(registry.findByAlias('home')?.id).toBe('nav_home');

      registry.updateCommand('nav_home', { aliases: ['dashboard'] });

      expect(registry.findByAlias('home')).toBeUndefined();
      expect(registry.findByAlias('dashboard')?.id).toBe('nav_home');
    });

    it('should prevent alias collision with another command during update', () => {
      registry.registerCommand({ id: 'cmd_a', displayName: 'A', aliases: ['a'] });
      registry.registerCommand({ id: 'cmd_b', displayName: 'B', aliases: ['b'] });

      expect(() => registry.updateCommand('cmd_b', { aliases: ['a'] })).toThrow(
        CommandProviderException,
      );
    });

    it('should prevent name collision with another command during update', () => {
      registry.registerCommand({ id: 'cmd_1', displayName: 'First' });
      registry.registerCommand({ id: 'cmd_2', displayName: 'Second' });

      expect(() => registry.updateCommand('cmd_2', { displayName: 'First' })).toThrow(
        CommandProviderException,
      );
    });
  });

  describe('6. High-Performance Lookups & Alias Resolution', () => {
    it('should find command by ID', () => {
      registry.registerCommand({ id: 'voice_listen', displayName: 'Start Voice Listener' });
      const cmd = registry.findCommand('voice_listen');
      expect(cmd).toBeDefined();
      expect(cmd?.displayName).toBe('Start Voice Listener');
      expect(registry.statistics().lookups).toBe(1);
    });

    it('should increment failedLookups when finding non-existent ID', () => {
      const cmd = registry.findCommand('invalid_id');
      expect(cmd).toBeUndefined();
      expect(registry.statistics().failedLookups).toBe(1);
    });

    it('should find command by alias case-insensitively', () => {
      registry.registerCommand({
        id: 'open_downloads',
        displayName: 'Open Downloads',
        aliases: ['downloads', 'download folder', 'my downloads'],
      });

      const cmd1 = registry.findByAlias('downloads');
      const cmd2 = registry.findByAlias('DOWNLOAD FOLDER');
      const cmd3 = registry.findByAlias('  My Downloads  ');

      expect(cmd1?.id).toBe('open_downloads');
      expect(cmd2?.id).toBe('open_downloads');
      expect(cmd3?.id).toBe('open_downloads');
    });

    it('should find command by displayName case-insensitively', () => {
      registry.registerCommand({ id: 'sys_settings', displayName: 'Open Settings' });
      const cmd = registry.findByName('open settings');
      expect(cmd?.id).toBe('sys_settings');
    });

    it('should list all registered aliases', () => {
      registry.registerCommand({
        id: 'c1',
        displayName: 'C1',
        aliases: ['alias1', 'alias2'],
      });

      const aliases = registry.listAliases();
      expect(aliases.length).toBe(2);
      expect(aliases.map((a) => a.alias)).toContain('alias1');
      expect(aliases.map((a) => a.alias)).toContain('alias2');
    });
  });

  describe('7. Category Management', () => {
    it('should include preset categories in listCategories()', () => {
      const categories = registry.listCategories();
      const names = categories.map((c) => c.name);

      expect(names).toContain('Filesystem');
      expect(names).toContain('Navigation');
      expect(names).toContain('Clipboard');
      expect(names).toContain('Compression');
      expect(names).toContain('Search');
      expect(names).toContain('Voice');
      expect(names).toContain('AI');
      expect(names).toContain('Settings');
      expect(names).toContain('Developer');
      expect(names).toContain('Diagnostics');
    });

    it('should accurately count commands per category', () => {
      registry.registerCommand({ id: 'c1', displayName: 'C1', category: 'Filesystem' });
      registry.registerCommand({ id: 'c2', displayName: 'C2', category: 'Filesystem' });
      registry.registerCommand({ id: 'c3', displayName: 'C3', category: 'Voice' });

      const categories = registry.listCategories();
      const fsCat = categories.find((c) => c.name === 'Filesystem');
      const voiceCat = categories.find((c) => c.name === 'Voice');

      expect(fsCat?.commandCount).toBe(2);
      expect(voiceCat?.commandCount).toBe(1);
    });

    it('should list commands filtered by category case-insensitively', () => {
      registry.registerCommand({ id: 'c1', displayName: 'C1', category: 'Filesystem' });
      registry.registerCommand({ id: 'c2', displayName: 'C2', category: 'Search' });

      const fsCommands = registry.listCommands('filesystem');
      expect(fsCommands.length).toBe(1);
      expect(fsCommands[0].id).toBe('c1');
    });
  });

  describe('8. Search Engine & Ranking', () => {
    beforeEach(() => {
      registry.registerCommand({
        id: 'file_copy',
        displayName: 'Copy File',
        description: 'Copies selected file to clipboard',
        category: 'Filesystem',
        aliases: ['copy'],
        tags: ['clipboard', 'fs'],
      });

      registry.registerCommand({
        id: 'file_move',
        displayName: 'Move File',
        description: 'Moves selected file to destination folder',
        category: 'Filesystem',
        aliases: ['mv'],
        tags: ['fs'],
      });

      registry.registerCommand({
        id: 'search_files',
        displayName: 'Search Files',
        description: 'Searches workspace files',
        category: 'Search',
        aliases: ['find'],
        tags: ['query', 'find'],
      });
    });

    it('should return ranked matches for exact ID/Name/Alias search', () => {
      const results = registry.search('copy');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].id).toBe('file_copy');
    });

    it('should return matches based on tag search', () => {
      const results = registry.search('query');
      expect(results.length).toBe(1);
      expect(results[0].id).toBe('search_files');
    });

    it('should return all commands on empty or whitespace search query', () => {
      const results = registry.search('');
      expect(results.length).toBe(3);
    });

    it('should increment search count in statistics', () => {
      registry.search('file');
      expect(registry.statistics().searches).toBe(1);
    });
  });

  describe('9. Telemetry Statistics & Health', () => {
    it('should generate immutable CommandRegistryStatistics snapshot', () => {
      registry.registerCommand({ id: 'c1', displayName: 'C1', aliases: ['a1'] });
      registry.findCommand('c1');
      registry.findCommand('invalid');

      const stats = registry.statistics();
      expect(stats.registeredCommands).toBe(1);
      expect(stats.lookups).toBe(1);
      expect(stats.failedLookups).toBe(1);
      expect(stats.aliasCount).toBe(1);
      expect(Object.isFrozen(stats)).toBe(true);
    });

    it('should generate healthy CommandRegistryHealth snapshot for clean registry', () => {
      registry.registerCommand({
        id: 'c1',
        displayName: 'C1',
        description: 'Desc 1',
        category: 'Filesystem',
      });

      const health = registry.health();
      expect(health.healthy).toBe(true);
      expect(health.missingMetadata).toBe(0);
      expect(health.duplicateIds).toBe(0);
      expect(Object.isFrozen(health)).toBe(true);
    });

    it('should clear all registrations, aliases, and statistics on clear()', () => {
      registry.registerCommand({ id: 'c1', displayName: 'C1', aliases: ['a1'] });
      registry.clear();

      expect(registry.containsCommand('c1')).toBe(false);
      expect(registry.findByAlias('a1')).toBeUndefined();
      expect(registry.statistics().registeredCommands).toBe(0);
      expect(registry.statistics().aliasCount).toBe(0);
    });
  });

  describe('10. Provider & Runtime Integration', () => {
    it('should delegate registerCommand and lookup through CommandProvider and CommandRuntime', () => {
      const provider = new CommandProvider();
      provider.initialize();
      const runtime = new CommandRuntime(provider);

      const def = runtime.registerCommand({
        id: 'open_terminal',
        displayName: 'Open Terminal',
        aliases: ['term', 'cli'],
        category: 'Developer',
      });

      expect(def.id).toBe('open_terminal');
      expect(runtime.containsCommand('open_terminal')).toBe(true);
      expect(runtime.findByAlias('term')?.id).toBe('open_terminal');
      expect(runtime.findByName('open terminal')?.id).toBe('open_terminal');
    });

    it('should include command registry data in runtime diagnostics()', () => {
      const runtime = new CommandRuntime();
      runtime.initialize();

      runtime.registerCommand({
        id: 'open_ai_chat',
        displayName: 'Open AI Assistant',
        category: 'AI',
        aliases: ['ai', 'assistant'],
      });

      const diag = runtime.diagnostics();
      expect(diag.registeredCommands).toContain('open_ai_chat');
      expect(diag.registeredCategories).toContain('AI');
      expect(diag.registeredAliases).toContain('ai');
      expect(diag.registryStatistics?.registeredCommands).toBe(1);
      expect(diag.registryHealth?.healthy).toBe(true);
    });

    it('should delegate search and category listing through CommandRuntime', () => {
      const runtime = new CommandRuntime();
      runtime.initialize();

      runtime.registerCommand({
        id: 'clipboard_copy',
        displayName: 'Copy to Clipboard',
        category: 'Clipboard',
      });

      const categories = runtime.listCategories();
      expect(categories.some((c) => c.name === 'Clipboard')).toBe(true);

      const searchResults = runtime.search('clipboard');
      expect(searchResults.length).toBe(1);
      expect(searchResults[0].id).toBe('clipboard_copy');
    });

    it('should clean up registry singletons on resetCommandRuntime()', () => {
      const r1 = getCommandRuntime();
      r1.registerCommand({ id: 'c1', displayName: 'C1' });
      expect(r1.containsCommand('c1')).toBe(true);

      resetCommandRuntime();

      const r2 = getCommandRuntime();
      expect(r2.containsCommand('c1')).toBe(false);
    });
  });
});
