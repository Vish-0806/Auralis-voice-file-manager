import { AlertRuleValidationError } from '../errors/AlertingErrors';

export function canonicalize(value: unknown): string {
  if (value === null) {
    return 'null';
  }
  if (value === undefined) {
    return 'undefined';
  }
  if (Array.isArray(value)) {
    return '[' + value.map(canonicalize).join(',') + ']';
  }
  if (typeof value === 'object') {
    const keys = Object.keys(value as object).sort();
    const parts = keys.map(k => `${k}:${canonicalize((value as any)[k])}`);
    return '{' + parts.join(',') + '}';
  }
  return String(value);
}

export function fnv1a(str: string): string {
  let hash = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

export function createAlertFingerprint(
  ruleId: string,
  ruleVersion: number | undefined,
  severity: string,
  sourceId: string,
  triggerIdentity: Record<string, unknown>
): string {
  if (!ruleId) {
    throw new AlertRuleValidationError('ruleId is required to generate a fingerprint');
  }
  if (!severity) {
    throw new AlertRuleValidationError('severity is required to generate a fingerprint');
  }
  if (!sourceId) {
    throw new AlertRuleValidationError('sourceId is required to generate a fingerprint');
  }

  const identityObj = {
    ruleId,
    ruleVersion: ruleVersion ?? null,
    severity,
    sourceId,
    triggerIdentity
  };

  const canonicalString = canonicalize(identityObj);
  return fnv1a(canonicalString);
}
