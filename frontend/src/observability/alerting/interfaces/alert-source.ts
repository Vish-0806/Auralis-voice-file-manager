export interface IAlertEvaluationContext {
  readonly sourceId: string;
  readonly componentId?: string;
  readonly status?: string;
  readonly severity?: string;
  readonly metrics?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
}
