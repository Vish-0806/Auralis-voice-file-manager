export interface AlertingStatistics {
  readonly registeredAlertCount: number;
}

export interface AlertingDiagnostics {
  readonly runtimeState: string;
  readonly registeredAlertCount: number;
  readonly generatedAt: number;
}