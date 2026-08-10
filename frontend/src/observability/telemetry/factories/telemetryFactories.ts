import { TelemetryType, Severity } from '../models/telemetry';
import { TelemetryValidationError } from '../errors/TelemetryErrors';

export function validateRecordId(id: string): void {
  if (!id || !id.trim()) {
    throw new TelemetryValidationError('Record ID cannot be empty.');
  }
}

export function validateTimestamp(timestamp: number): void {
  if (typeof timestamp !== 'number' || isNaN(timestamp) || timestamp <= 0) {
    throw new TelemetryValidationError('Record timestamp must be a valid positive number.');
  }
}

export function validateTelemetryType(type: string): void {
  if (!Object.values(TelemetryType).includes(type as any)) {
    throw new TelemetryValidationError(`Invalid telemetry type: ${type}`);
  }
}

export function validateSeverity(severity: string): void {
  if (!Object.values(Severity).includes(severity as any)) {
    throw new TelemetryValidationError(`Invalid severity level: ${severity}`);
  }
}

const UNSAFE_KEYS = ['password', 'token', 'secret', 'authorization', 'cookie', 'key'];

export function cleanUnsafeAttributes(attrs?: Record<string, unknown>): Record<string, unknown> | undefined {
  if (!attrs) return undefined;
  const cleaned: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(attrs)) {
    const lowerKey = k.toLowerCase();
    if (UNSAFE_KEYS.some(unsafe => lowerKey.includes(unsafe))) {
      cleaned[k] = '[REDACTED]';
    } else if (v === undefined || typeof v === 'function' || typeof v === 'symbol') {
      continue;
    } else {
      cleaned[k] = typeof v === 'object' && v !== null ? JSON.parse(JSON.stringify(v)) : v;
    }
  }
  return cleaned;
}

export function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function shouldSampleRecord(id: string, rate: number): boolean {
  if (rate >= 1.0) return true;
  if (rate <= 0.0) return false;
  const hash = hashCode(id);
  const normalized = (hash % 1000) / 1000;
  return normalized < rate;
}
