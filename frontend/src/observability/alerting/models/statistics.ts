import type { AlertRuleStatistics } from './rule-statistics';

export interface AlertingStatistics extends AlertRuleStatistics {
  readonly registeredAlertCount: number;
  readonly totalEvaluations: number;
  readonly matchedEvaluations: number;
  readonly unmatchedEvaluations: number;
  readonly errorEvaluations: number;
  readonly skippedEvaluations: number;
  readonly totalEvaluationDuration: number;
  readonly averageEvaluationDuration: number;

  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;

  readonly totalDeduplicationChecks: number;
  readonly acceptedAlertCount: number;
  readonly duplicateAlertCount: number;
  readonly cooldownSuppressedCount: number;
  readonly activeCooldownCount: number;
  readonly trackedFingerprintCount: number;

  readonly lifecycleTransitions: number;
  readonly acknowledgements: number;
  readonly resolutions: number;
  readonly closures: number;
  readonly invalidTransitions: number;
  readonly activeAlerts: number;
  readonly acknowledgedAlerts: number;
  readonly resolvedAlerts: number;
  readonly closedAlerts: number;

  readonly suppressionEvaluations: number;
  readonly suppressedAlerts: number;
  readonly allowedAlerts: number;
  readonly policyMatches: number;
  readonly maintenanceMatches: number;
  readonly snoozedMatches: number;
  readonly evaluationFailures: number;
  readonly activePolicies: number;
  readonly activeMaintenanceWindows: number;
  readonly activeSnoozes: number;

  readonly notificationRequests: number;
  readonly validationFailures: number;
  readonly dispatchedNotifications: number;
  readonly deliveredNotifications: number;
  readonly failedNotifications: number;
  readonly skippedNotifications: number;
  readonly cancelledNotifications: number;
  readonly retryAttempts: number;
  readonly registeredChannels: number;
  readonly enabledChannels: number;
  readonly disabledChannels: number;
  readonly averageDeliveryDuration: number;

  // Extended for Phase 18.7.9
  readonly orchestrationsTotal: number;
  readonly orchestrationsSuccessful: number;
  readonly orchestrationsSkipped: number;
  readonly orchestrationsDuplicate: number;
  readonly orchestrationsSuppressed: number;
  readonly orchestrationsFailed: number;
  readonly averageOrchestrationDuration: number;
  readonly activeOrchestrations: number;
}

export interface AlertingDiagnostics extends AlertRuleStatistics {
  readonly runtimeState: string;
  readonly registeredAlertCount: number;
  readonly totalEvaluations: number;
  readonly matchedEvaluations: number;
  readonly unmatchedEvaluations: number;
  readonly errorEvaluations: number;
  readonly skippedEvaluations: number;
  readonly totalEvaluationDuration: number;
  readonly averageEvaluationDuration: number;

  readonly totalAlertGenerations: number;
  readonly successfulAlertGenerations: number;
  readonly rejectedAlertGenerations: number;
  readonly generationErrors: number;
  readonly totalGenerationDuration: number;
  readonly averageGenerationDuration: number;

  readonly totalDeduplicationChecks: number;
  readonly acceptedAlertCount: number;
  readonly duplicateAlertCount: number;
  readonly cooldownSuppressedCount: number;
  readonly activeCooldownCount: number;
  readonly trackedFingerprintCount: number;

  readonly lifecycleTransitions: number;
  readonly acknowledgements: number;
  readonly resolutions: number;
  readonly closures: number;
  readonly invalidTransitions: number;
  readonly activeAlerts: number;
  readonly acknowledgedAlerts: number;
  readonly resolvedAlerts: number;
  readonly closedAlerts: number;

  readonly suppressionEvaluations: number;
  readonly suppressedAlerts: number;
  readonly allowedAlerts: number;
  readonly policyMatches: number;
  readonly maintenanceMatches: number;
  readonly snoozedMatches: number;
  readonly evaluationFailures: number;
  readonly activePolicies: number;
  readonly activeMaintenanceWindows: number;
  readonly activeSnoozes: number;

  readonly notificationRequests: number;
  readonly validationFailures: number;
  readonly dispatchedNotifications: number;
  readonly deliveredNotifications: number;
  readonly failedNotifications: number;
  readonly skippedNotifications: number;
  readonly cancelledNotifications: number;
  readonly retryAttempts: number;
  readonly registeredChannels: number;
  readonly enabledChannels: number;
  readonly disabledChannels: number;
  readonly averageDeliveryDuration: number;

  // Extended for Phase 18.7.9
  readonly orchestrationsTotal: number;
  readonly orchestrationsSuccessful: number;
  readonly orchestrationsSkipped: number;
  readonly orchestrationsDuplicate: number;
  readonly orchestrationsSuppressed: number;
  readonly orchestrationsFailed: number;
  readonly averageOrchestrationDuration: number;
  readonly activeOrchestrations: number;

  readonly generatedAt: number;
}