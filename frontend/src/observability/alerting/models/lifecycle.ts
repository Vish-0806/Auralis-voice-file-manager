export const AlertLifecycleState = {
  ACTIVE: 'ACTIVE',
  ACKNOWLEDGED: 'ACKNOWLEDGED',
  RESOLVED: 'RESOLVED',
  CLOSED: 'CLOSED'
} as const;

export type AlertLifecycleStateValue = typeof AlertLifecycleState[keyof typeof AlertLifecycleState];

export const AlertLifecycleActor = {
  SYSTEM: 'SYSTEM',
  USER: 'USER',
  PLUGIN: 'PLUGIN',
  AUTOMATION: 'AUTOMATION'
} as const;

export type AlertLifecycleActorValue = typeof AlertLifecycleActor[keyof typeof AlertLifecycleActor];

export interface AlertLifecycleHistoryEntry {
  readonly alertId: string;
  readonly fingerprint?: string;
  readonly previousState: AlertLifecycleStateValue | null;
  readonly nextState: AlertLifecycleStateValue;
  readonly timestamp: number;
  readonly actor: AlertLifecycleActorValue;
  readonly operation: string;
  readonly reason?: string;
  readonly metadata?: Record<string, unknown>;
}

export interface AlertLifecycleRecord {
  readonly alertId: string;
  readonly fingerprint?: string;
  readonly state: AlertLifecycleStateValue;
  readonly createdAt: number;
  readonly updatedAt: number;
  readonly history: ReadonlyArray<AlertLifecycleHistoryEntry>;
  readonly metadata?: Record<string, unknown>;
}
