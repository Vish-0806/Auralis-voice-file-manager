import { IDiagnosticsSource } from '../interfaces/diagnostics-source';
import { DiagnosticCheck } from '../models/check';
import {
  DiagnosticSourceAlreadyExistsError,
  DiagnosticSourceNotFoundError,
  DiagnosticCheckAlreadyExistsError,
  DiagnosticCheckNotFoundError
} from '../errors/DiagnosticsErrors';

export class DiagnosticsRegistry {
  private readonly sources = new Map<string, IDiagnosticsSource>();
  private readonly sourceIds: string[] = [];

  private readonly checks = new Map<string, DiagnosticCheck>();
  private readonly checkIds: string[] = [];

  public registerSource(source: IDiagnosticsSource): void {
    const id = source.descriptor.id;
    if (this.sources.has(id)) {
      throw new DiagnosticSourceAlreadyExistsError(`Diagnostic source with ID '${id}' is already registered.`);
    }
    this.sources.set(id, source);
    this.sourceIds.push(id);
  }

  public unregisterSource(sourceId: string): void {
    if (!this.sources.has(sourceId)) {
      throw new DiagnosticSourceNotFoundError(`Diagnostic source with ID '${sourceId}' not found.`);
    }
    this.sources.delete(sourceId);
    const idx = this.sourceIds.indexOf(sourceId);
    if (idx !== -1) {
      this.sourceIds.splice(idx, 1);
    }

    // Cascade remove checks
    const checksToRemove = this.getChecksForSource(sourceId);
    for (const check of checksToRemove) {
      this.unregisterCheck(check.id);
    }
  }

  public getSource(sourceId: string): IDiagnosticsSource | null {
    const s = this.sources.get(sourceId);
    return s || null;
  }

  public hasSource(sourceId: string): boolean {
    return this.sources.has(sourceId);
  }

  public listSources(): ReadonlyArray<IDiagnosticsSource> {
    const list = this.sourceIds.map(id => this.sources.get(id)!).filter(Boolean);
    return Object.freeze(list);
  }

  public registerCheck(check: DiagnosticCheck): void {
    if (!this.sources.has(check.sourceId)) {
      throw new DiagnosticSourceNotFoundError(`Cannot register check: diagnostic source with ID '${check.sourceId}' is not registered.`);
    }
    if (this.checks.has(check.id)) {
      throw new DiagnosticCheckAlreadyExistsError(`Diagnostic check with ID '${check.id}' is already registered.`);
    }
    this.checks.set(check.id, check);
    this.checkIds.push(check.id);
  }

  public unregisterCheck(checkId: string): void {
    if (!this.checks.has(checkId)) {
      throw new DiagnosticCheckNotFoundError(`Diagnostic check with ID '${checkId}' not found.`);
    }
    this.checks.delete(checkId);
    const idx = this.checkIds.indexOf(checkId);
    if (idx !== -1) {
      this.checkIds.splice(idx, 1);
    }
  }

  public getCheck(checkId: string): DiagnosticCheck | null {
    const c = this.checks.get(checkId);
    return c || null;
  }

  public listChecks(): ReadonlyArray<DiagnosticCheck> {
    const list = this.checkIds.map(id => this.checks.get(id)!).filter(Boolean);
    return Object.freeze(list);
  }

  public getChecksForSource(sourceId: string): ReadonlyArray<DiagnosticCheck> {
    const list = this.checkIds
      .map(id => this.checks.get(id)!)
      .filter(c => c && c.sourceId === sourceId);
    return Object.freeze(list);
  }
}
