export interface DiagnosticSourceDescriptor {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly version?: string | null;
  readonly enabled: boolean;
  readonly priority: number;
  readonly metadata: Record<string, unknown>;
}
