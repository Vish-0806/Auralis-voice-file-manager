import type { ITelemetryExporter } from '../interfaces/telemetry-exporter';
import {
  TelemetryExporterAlreadyExistsError,
  TelemetryExporterNotFoundError,
  TelemetryValidationError
} from '../errors/TelemetryErrors';

export class TelemetryRegistry {
  private readonly exporters = new Map<string, ITelemetryExporter>();

  public register(exporter: ITelemetryExporter): void {
    if (!exporter || !exporter.name || !exporter.name.trim()) {
      throw new TelemetryValidationError('Telemetry exporter must have a valid non-empty name.');
    }
    const name = exporter.name.trim();
    if (this.exporters.has(name)) {
      throw new TelemetryExporterAlreadyExistsError(`Telemetry exporter with name '${name}' is already registered.`);
    }
    this.exporters.set(name, exporter);
  }

  public get(name: string): ITelemetryExporter {
    if (!name || !name.trim()) {
      throw new TelemetryValidationError('Exporter name cannot be empty.');
    }
    const trimmed = name.trim();
    const exp = this.exporters.get(trimmed);
    if (!exp) {
      throw new TelemetryExporterNotFoundError(`Telemetry exporter '${trimmed}' not found.`);
    }
    return exp;
  }

  public has(name: string): boolean {
    if (!name) return false;
    return this.exporters.has(name.trim());
  }

  public remove(name: string): void {
    if (!name || !name.trim()) {
      throw new TelemetryValidationError('Exporter name cannot be empty.');
    }
    const trimmed = name.trim();
    if (!this.exporters.has(trimmed)) {
      throw new TelemetryExporterNotFoundError(`Telemetry exporter '${trimmed}' not found.`);
    }
    this.exporters.delete(trimmed);
  }

  public list(): ReadonlyArray<ITelemetryExporter> {
    const list = Array.from(this.exporters.values());
    list.sort((a, b) => a.name.localeCompare(b.name));
    return Object.freeze(list);
  }

  public clear(): void {
    this.exporters.clear();
  }

  public getExporterCount(): number {
    return this.exporters.size;
  }
}
