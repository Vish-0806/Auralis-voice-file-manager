import type { MonitorStatusValue, MonitoringHealth } from './health';
import type { MonitoringRuntimeStateValue } from './runtime';

export const MonitoringComponentType = {
  RUNTIME: 'RUNTIME',
  SERVICE: 'SERVICE',
  SUBSYSTEM: 'SUBSYSTEM',
  PROVIDER: 'PROVIDER',
  EXTERNAL: 'EXTERNAL'
} as const;

export type MonitoringComponentTypeValue = typeof MonitoringComponentType[keyof typeof MonitoringComponentType];

export interface MonitoringComponent {
  readonly id: string;
  readonly name: string;
  readonly type: MonitoringComponentTypeValue;
  readonly status: MonitorStatusValue;
  readonly enabled: boolean;
  readonly registeredAt: number;
  readonly lastCheckedAt?: number;
  readonly metadata: Record<string, unknown>;
}

export type MonitoringCheckCallback = () => void | Promise<void> | MonitorStatusValue | Promise<MonitorStatusValue>;

export interface MonitoringCheck {
  readonly id: string;
  readonly componentId: string;
  readonly name: string;
  readonly description?: string;
  readonly enabled: boolean;
  readonly executionOrder: number;
  readonly timeoutMs: number;
  readonly metadata: Record<string, unknown>;
  readonly execute: MonitoringCheckCallback;
}

export interface MonitoringResult {
  readonly checkId: string;
  readonly componentId: string;
  readonly status: MonitorStatusValue;
  readonly startedAt: number;
  readonly completedAt: number;
  readonly durationMs: number;
  readonly message?: string;
  readonly details?: unknown;
  readonly error?: Error;
}

export interface MonitoringStatistics {
  readonly totalChecks: number;
  readonly successfulChecks: number;
  readonly degradedChecks: number;
  readonly failedChecks: number;
  readonly skippedChecks: number;
  readonly totalExecutionTimeMs: number;
  readonly averageExecutionTimeMs: number;
  readonly lastCheckAt?: number;
}

export interface MonitoringDiagnostics {
  readonly runtimeState: MonitoringRuntimeStateValue;
  readonly componentCount: number;
  readonly checkCount: number;
  readonly statistics: MonitoringStatistics;
  readonly health: MonitoringHealth;
  readonly generatedAt: number;
}

export function freezeDeepSafe<T>(value: T): T {
  if (Object.isFrozen(value)) {
    return value;
  }

  if (Array.isArray(value)) {
    const arrayValue = value.map((item) => freezeDeepSafe(item));
    return Object.freeze(arrayValue) as T;
  }

  if (value instanceof Map) {
    const newMap = new Map();
    value.forEach((v, k) => {
      newMap.set(freezeDeepSafe(k), freezeDeepSafe(v));
    });
    return Object.freeze(newMap) as unknown as T;
  }

  if (value instanceof Set) {
    const newSet = new Set();
    value.forEach((v) => {
      newSet.add(freezeDeepSafe(v));
    });
    return Object.freeze(newSet) as unknown as T;
  }

  if (value && typeof value === 'object') {
    if (value instanceof Error || value instanceof RegExp || value instanceof Date) {
      return Object.freeze(value);
    }
    const objectValue = value as Record<string, unknown>;
    const copy: Record<string, unknown> = {};
    Object.keys(objectValue).forEach((key) => {
      copy[key] = freezeDeepSafe(objectValue[key]);
    });
    return Object.freeze(copy) as unknown as T;
  }

  return value;
}
