export interface AlertAction {
  readonly type: string;
  readonly config: Record<string, unknown>;
}
