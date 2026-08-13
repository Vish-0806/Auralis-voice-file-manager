export const AlertSeverity = {
  INFO: 'INFO',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  CRITICAL: 'CRITICAL'
} as const;

export type AlertSeverityValue = typeof AlertSeverity[keyof typeof AlertSeverity];

export const AlertSeverityOrder: Record<AlertSeverityValue, number> = {
  [AlertSeverity.INFO]: 1,
  [AlertSeverity.WARNING]: 2,
  [AlertSeverity.ERROR]: 3,
  [AlertSeverity.CRITICAL]: 4
};

export function compareSeverity(a: AlertSeverityValue, b: AlertSeverityValue): number {
  return AlertSeverityOrder[a] - AlertSeverityOrder[b];
}

export function isSeverityAtLeast(actual: AlertSeverityValue, minimum: AlertSeverityValue): boolean {
  return AlertSeverityOrder[actual] >= AlertSeverityOrder[minimum];
}