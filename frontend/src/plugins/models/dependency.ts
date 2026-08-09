import type { PluginManifest } from './manifest';

export interface PluginDependency {
  readonly id: string;
  readonly versionRange: string;
  readonly optional: boolean;
}

export interface PluginDependencyNode {
  readonly id: string;
  readonly manifest: PluginManifest;
  readonly dependencies: ReadonlyArray<PluginDependency>;
}

export interface PluginDependencyEdge {
  readonly from: string;
  readonly to: string;
  readonly required: boolean;
  readonly versionRange: string;
}

export interface PluginDependencyGraph {
  readonly nodes: ReadonlyMap<string, PluginDependencyNode>;
  readonly edges: ReadonlyArray<PluginDependencyEdge>;
}

export const DependencyResolutionStatus = {
  RESOLVED: 'RESOLVED',
  FAILED: 'FAILED',
  PARTIAL: 'PARTIAL'
} as const;
export type DependencyResolutionStatusValue = typeof DependencyResolutionStatus[keyof typeof DependencyResolutionStatus];

export const DependencyResolutionIssueCode = {
  MISSING_DEPENDENCY: 'MISSING_DEPENDENCY',
  VERSION_CONFLICT: 'VERSION_CONFLICT',
  CIRCULAR_DEPENDENCY: 'CIRCULAR_DEPENDENCY',
  INVALID_CONSTRAINT: 'INVALID_CONSTRAINT'
} as const;
export type DependencyResolutionIssueCodeValue = typeof DependencyResolutionIssueCode[keyof typeof DependencyResolutionIssueCode];

export interface DependencyResolutionIssue {
  readonly code: DependencyResolutionIssueCodeValue;
  readonly severity: 'error' | 'warning';
  readonly message: string;
  readonly dependentId?: string;
  readonly dependencyId?: string;
  readonly constraint?: string;
  readonly path?: ReadonlyArray<string>;
}

export interface DependencyResolutionPlan {
  readonly order: ReadonlyArray<string>;
}

export interface DependencyResolutionResult {
  readonly status: DependencyResolutionStatusValue;
  readonly plan: DependencyResolutionPlan | null;
  readonly issues: ReadonlyArray<DependencyResolutionIssue>;
  readonly resolvedIds: ReadonlyArray<string>;
  readonly unresolvedIds: ReadonlyArray<string>;
}

export interface DependencyResolutionStatistics {
  readonly resolutionAttempts: number;
  readonly resolvedPlugins: number;
  readonly unresolvedPlugins: number;
  readonly missingDependencies: number;
  readonly versionConflicts: number;
  readonly circularDependencies: number;
  readonly optionalDependencyWarnings: number;
  readonly graphNodes: number;
  readonly graphEdges: number;
  readonly resolutionFailures: number;
}

export interface DependencyResolutionHealth {
  readonly healthy: boolean;
  readonly unresolvedDependencyCount: number;
  readonly cycleCount: number;
  readonly conflictCount: number;
  readonly message: string;
}

export function createDependencyResult(input: Omit<DependencyResolutionResult, typeof Symbol.toStringTag>): DependencyResolutionResult {
  return freezeDeepSafe(input);
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
    const objectValue = value as Record<string, unknown>;
    const copy: Record<string, unknown> = {};
    Object.keys(objectValue).forEach((key) => {
      copy[key] = freezeDeepSafe(objectValue[key]);
    });
    return Object.freeze(copy) as unknown as T;
  }

  return value;
}
