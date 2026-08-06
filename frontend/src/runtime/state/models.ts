/**
 * State Management Runtime Domain Models (Phase 16.5).
 *
 * Defines immutable state models, snapshots, context metadata, statistics metrics,
 * health evaluation snapshots, capabilities reporting, containers, store models,
 * actions, reducers, middleware execution, selectors, history, persistence records,
 * synchronization records, and production certification models for the Frontend State Runtime.
 */

export enum StateRuntimeState {
  UNINITIALIZED = 'UNINITIALIZED',
  INITIALIZING = 'INITIALIZING',
  READY = 'READY',
  STOPPING = 'STOPPING',
  STOPPED = 'STOPPED',
}

export interface StateContainer<T = unknown> {
  readonly containerId: string;
  readonly name: string;
  readonly state: T;
  readonly version: number;
  readonly updatedAt: string;
}

export interface StateSnapshot<T = unknown> {
  readonly snapshotId: string;
  readonly containerId: string;
  readonly state: T;
  readonly version: number;
  readonly capturedAt: string;
}

export interface StateMetadata {
  readonly runtimeId: string;
  readonly environment: string;
  readonly strictMode: boolean;
}

export interface StateContext {
  readonly runtimeId: string;
  readonly createdAt: string;
  readonly environment: string;
}

export interface StateCapabilities {
  readonly supportsContainers: boolean;
  readonly supportsReducers: boolean;
  readonly supportsMiddleware: boolean;
  readonly supportsSelectors: boolean;
  readonly supportsUndoRedo: boolean;
  readonly supportsPersistence: boolean;
  readonly supportsSynchronization: boolean;
  readonly supportsDiagnostics: boolean;
}

export interface StateStatistics {
  readonly initializations: number;
  readonly shutdowns: number;
  readonly restarts: number;
  readonly errors: number;
  readonly uptime: number;
}

export interface StateHealth {
  readonly healthy: boolean;
  readonly runtimeState: StateRuntimeState;
  readonly message: string;
}

export interface ApplicationState<T = unknown> {
  readonly globalState: T;
  readonly metadata: StateMetadata;
  readonly timestamp: string;
}

export interface StoreSnapshot<T = unknown> {
  readonly snapshotId: string;
  readonly storeId: string;
  readonly state: T;
  readonly timestamp: string;
}

export interface StoreStatistics {
  readonly readCount: number;
  readonly writeCount: number;
  readonly updateCount: number;
  readonly resetCount: number;
}

export interface StoreHealth {
  readonly healthy: boolean;
  readonly activeContainers: number;
  readonly errorRate: number;
}

export interface Subscription {
  readonly subscriptionId: string;
  readonly containerId: string;
  readonly subscribedAt: string;
  readonly active: boolean;
}

export interface Subscriber<T = unknown> {
  readonly subscriptionId: string;
  readonly containerId: string;
  readonly handler: (state: T) => void | Promise<void>;
  readonly active: boolean;
}

export interface Action<T = unknown> {
  readonly type: string;
  readonly payload: T;
  readonly actionId: string;
  readonly timestamp: string;
  readonly metadata?: Record<string, unknown>;
}

export interface ActionContext {
  readonly actionId: string;
  readonly source?: string;
  readonly correlationId?: string;
}

export interface Reducer<S = unknown, A = Action> {
  readonly reducerId: string;
  readonly name: string;
  readonly reduce: (state: S, action: A) => S;
}

export interface ReducerExecution {
  readonly reducerId: string;
  readonly actionType: string;
  readonly success: boolean;
  readonly durationMs: number;
  readonly error?: string;
  readonly executedAt: string;
}

export interface MiddlewareExecution {
  readonly middlewareId: string;
  readonly actionType: string;
  readonly phase: 'BEFORE' | 'AFTER' | 'ERROR';
  readonly success: boolean;
  readonly durationMs: number;
  readonly error?: string;
  readonly executedAt: string;
}

export interface Selector<S = unknown, R = unknown> {
  readonly selectorId: string;
  readonly name: string;
  readonly select: (state: S) => R;
}

export interface SelectorResult<R = unknown> {
  readonly value: R;
  readonly memoized: boolean;
  readonly durationMs: number;
  readonly evaluatedAt: string;
}

export interface StateHistory<T = unknown> {
  readonly snapshots: ReadonlyArray<StateSnapshot<T>>;
  readonly currentIndex: number;
  readonly maxSize: number;
}

export interface UndoRecord<T = unknown> {
  readonly undoId: string;
  readonly previousState: T;
  readonly undoneAt: string;
}

export interface RedoRecord<T = unknown> {
  readonly redoId: string;
  readonly nextState: T;
  readonly redoneAt: string;
}

export interface PersistenceRecord {
  readonly recordId: string;
  readonly containerId: string;
  readonly key: string;
  readonly version: number;
  readonly persistedAt: string;
}

export interface SynchronizationRecord {
  readonly syncId: string;
  readonly sourceContainerId: string;
  readonly targetContainerId: string;
  readonly conflictDetected: boolean;
  readonly resolved: boolean;
  readonly syncedAt: string;
}

export interface CertificationIssue {
  readonly issueId: string;
  readonly severity: 'INFO' | 'WARNING' | 'CRITICAL';
  readonly category: string;
  readonly message: string;
  readonly timestamp: string;
}

export interface StateCertification {
  readonly certified: boolean;
  readonly score: number;
  readonly passedChecks: number;
  readonly failedChecks: number;
  readonly certifiedAt: string;
}

export interface StateCertificationSummary {
  readonly certified: boolean;
  readonly score: number;
  readonly status: string;
  readonly certifiedAt: string;
}

export interface CertificationStatistics {
  readonly totalCertifications: number;
  readonly passedCertifications: number;
  readonly failedCertifications: number;
  readonly averageScore: number;
}

export interface CertificationHealth {
  readonly healthy: boolean;
  readonly certified: boolean;
  readonly score: number;
}

export interface CertificationReport {
  readonly certification: StateCertification;
  readonly summary: StateCertificationSummary;
  readonly issues: ReadonlyArray<CertificationIssue>;
  readonly diagnostics: StateDiagnostics;
  readonly generatedAt: string;
}

export interface StateConfiguration {
  readonly runtimeName: string;
  readonly version: string;
  readonly strictMode: boolean;
  readonly maxHistorySize?: number;
}

export interface StateDiagnostics {
  readonly health: StateHealth;
  readonly statistics: StateStatistics;
  readonly capabilities: StateCapabilities;
  readonly context: StateContext;
  readonly containersCount?: number;
  readonly actionsCount?: number;
  readonly reducersCount?: number;
  readonly middlewaresCount?: number;
  readonly selectorsCount?: number;
  readonly historySize?: number;
  readonly persistenceStatus?: string;
  readonly certification?: StateCertification;
  readonly certificationSummary?: StateCertificationSummary;
  readonly timestamp: string;
}

// Factories
export function createStateContainer<T = unknown>(
  params: Partial<StateContainer<T>> & { name: string; state: T },
): StateContainer<T> {
  return Object.freeze({
    containerId: params.containerId ?? `cnt_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    state: params.state,
    version: params.version ?? 1,
    updatedAt: params.updatedAt ?? new Date().toISOString(),
  });
}

export function createStateSnapshot<T = unknown>(
  params: Partial<StateSnapshot<T>> & { containerId: string; state: T },
): StateSnapshot<T> {
  return Object.freeze({
    snapshotId: params.snapshotId ?? `snp_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    containerId: params.containerId,
    state: params.state,
    version: params.version ?? 1,
    capturedAt: params.capturedAt ?? new Date().toISOString(),
  });
}

export function createStateMetadata(params: Partial<StateMetadata> = {}): StateMetadata {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `state_rt_${Date.now()}`,
    environment: params.environment ?? 'production',
    strictMode: params.strictMode ?? true,
  });
}

export function createStateContext(params: Partial<StateContext> = {}): StateContext {
  return Object.freeze({
    runtimeId: params.runtimeId ?? `state_runtime_${Date.now()}`,
    createdAt: params.createdAt ?? new Date().toISOString(),
    environment: params.environment ?? 'production',
  });
}

export function createStateCapabilities(params: Partial<StateCapabilities> = {}): StateCapabilities {
  return Object.freeze({
    supportsContainers: params.supportsContainers ?? true,
    supportsReducers: params.supportsReducers ?? true,
    supportsMiddleware: params.supportsMiddleware ?? true,
    supportsSelectors: params.supportsSelectors ?? true,
    supportsUndoRedo: params.supportsUndoRedo ?? true,
    supportsPersistence: params.supportsPersistence ?? true,
    supportsSynchronization: params.supportsSynchronization ?? true,
    supportsDiagnostics: params.supportsDiagnostics ?? true,
  });
}

export function createStateStatistics(params: Partial<StateStatistics> = {}): StateStatistics {
  return Object.freeze({
    initializations: params.initializations ?? 0,
    shutdowns: params.shutdowns ?? 0,
    restarts: params.restarts ?? 0,
    errors: params.errors ?? 0,
    uptime: params.uptime ?? 0,
  });
}

export function createStateHealth(params: Partial<StateHealth> = {}): StateHealth {
  return Object.freeze({
    healthy: params.healthy ?? false,
    runtimeState: params.runtimeState ?? StateRuntimeState.UNINITIALIZED,
    message: params.message ?? 'State runtime is uninitialized.',
  });
}

export function createApplicationState<T = unknown>(
  params: Partial<ApplicationState<T>> & { globalState: T },
): ApplicationState<T> {
  return Object.freeze({
    globalState: params.globalState,
    metadata: params.metadata ?? createStateMetadata(),
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createStoreSnapshot<T = unknown>(
  params: Partial<StoreSnapshot<T>> & { storeId: string; state: T },
): StoreSnapshot<T> {
  return Object.freeze({
    snapshotId: params.snapshotId ?? `ss_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    storeId: params.storeId,
    state: params.state,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createStoreStatistics(params: Partial<StoreStatistics> = {}): StoreStatistics {
  return Object.freeze({
    readCount: params.readCount ?? 0,
    writeCount: params.writeCount ?? 0,
    updateCount: params.updateCount ?? 0,
    resetCount: params.resetCount ?? 0,
  });
}

export function createStoreHealth(params: Partial<StoreHealth> = {}): StoreHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    activeContainers: params.activeContainers ?? 0,
    errorRate: params.errorRate ?? 0,
  });
}

export function createSubscription(params: Partial<Subscription> & { containerId: string }): Subscription {
  return Object.freeze({
    subscriptionId: params.subscriptionId ?? `sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    containerId: params.containerId,
    subscribedAt: params.subscribedAt ?? new Date().toISOString(),
    active: params.active ?? true,
  });
}

export function createSubscriber<T = unknown>(
  params: Partial<Subscriber<T>> & { containerId: string; handler: (state: T) => void | Promise<void> },
): Subscriber<T> {
  return Object.freeze({
    subscriptionId: params.subscriptionId ?? `sub_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    containerId: params.containerId,
    handler: params.handler,
    active: params.active ?? true,
  });
}

export function createAction<T = unknown>(
  params: Partial<Action<T>> & { type: string; payload: T },
): Action<T> {
  return Object.freeze({
    type: params.type,
    payload: params.payload,
    actionId: params.actionId ?? `act_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    timestamp: params.timestamp ?? new Date().toISOString(),
    metadata: params.metadata ? Object.freeze({ ...params.metadata }) : undefined,
  });
}

export function createActionContext(params: Partial<ActionContext> = {}): ActionContext {
  return Object.freeze({
    actionId: params.actionId ?? `act_${Date.now()}`,
    source: params.source,
    correlationId: params.correlationId,
  });
}

export function createReducer<S = unknown, A = Action>(
  params: Partial<Reducer<S, A>> & { name: string; reduce: (state: S, action: A) => S },
): Reducer<S, A> {
  return Object.freeze({
    reducerId: params.reducerId ?? `red_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    reduce: params.reduce,
  });
}

export function createReducerExecution(
  params: Partial<ReducerExecution> & { reducerId: string; actionType: string },
): ReducerExecution {
  return Object.freeze({
    reducerId: params.reducerId,
    actionType: params.actionType,
    success: params.success ?? true,
    durationMs: params.durationMs ?? 0,
    error: params.error,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createMiddlewareExecution(
  params: Partial<MiddlewareExecution> & { middlewareId: string; actionType: string },
): MiddlewareExecution {
  return Object.freeze({
    middlewareId: params.middlewareId,
    actionType: params.actionType,
    phase: params.phase ?? 'BEFORE',
    success: params.success ?? true,
    durationMs: params.durationMs ?? 0,
    error: params.error,
    executedAt: params.executedAt ?? new Date().toISOString(),
  });
}

export function createSelector<S = unknown, R = unknown>(
  params: Partial<Selector<S, R>> & { name: string; select: (state: S) => R },
): Selector<S, R> {
  return Object.freeze({
    selectorId: params.selectorId ?? `sel_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    name: params.name,
    select: params.select,
  });
}

export function createSelectorResult<R = unknown>(
  params: Partial<SelectorResult<R>> & { value: R },
): SelectorResult<R> {
  return Object.freeze({
    value: params.value,
    memoized: params.memoized ?? false,
    durationMs: params.durationMs ?? 0,
    evaluatedAt: params.evaluatedAt ?? new Date().toISOString(),
  });
}

export function createStateHistory<T = unknown>(params: Partial<StateHistory<T>> = {}): StateHistory<T> {
  const snapshots = params.snapshots ?? [];
  return Object.freeze({
    snapshots: Object.freeze([...snapshots]),
    currentIndex: params.currentIndex ?? (snapshots.length > 0 ? snapshots.length - 1 : -1),
    maxSize: params.maxSize ?? 50,
  });
}

export function createUndoRecord<T = unknown>(
  params: Partial<UndoRecord<T>> & { previousState: T },
): UndoRecord<T> {
  return Object.freeze({
    undoId: params.undoId ?? `undo_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    previousState: params.previousState,
    undoneAt: params.undoneAt ?? new Date().toISOString(),
  });
}

export function createRedoRecord<T = unknown>(
  params: Partial<RedoRecord<T>> & { nextState: T },
): RedoRecord<T> {
  return Object.freeze({
    redoId: params.redoId ?? `redo_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    nextState: params.nextState,
    redoneAt: params.redoneAt ?? new Date().toISOString(),
  });
}

export function createPersistenceRecord(
  params: Partial<PersistenceRecord> & { containerId: string; key: string; version: number },
): PersistenceRecord {
  return Object.freeze({
    recordId: params.recordId ?? `prrec_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    containerId: params.containerId,
    key: params.key,
    version: params.version,
    persistedAt: params.persistedAt ?? new Date().toISOString(),
  });
}

export function createSynchronizationRecord(
  params: Partial<SynchronizationRecord> & { sourceContainerId: string; targetContainerId: string },
): SynchronizationRecord {
  return Object.freeze({
    syncId: params.syncId ?? `sync_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    sourceContainerId: params.sourceContainerId,
    targetContainerId: params.targetContainerId,
    conflictDetected: params.conflictDetected ?? false,
    resolved: params.resolved ?? true,
    syncedAt: params.syncedAt ?? new Date().toISOString(),
  });
}

export function createCertificationIssue(
  params: Partial<CertificationIssue> & { category: string; message: string },
): CertificationIssue {
  return Object.freeze({
    issueId: params.issueId ?? `issue_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    severity: params.severity ?? 'INFO',
    category: params.category,
    message: params.message,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}

export function createStateCertification(params: Partial<StateCertification> = {}): StateCertification {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    passedChecks: params.passedChecks ?? 10,
    failedChecks: params.failedChecks ?? 0,
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createStateCertificationSummary(params: Partial<StateCertificationSummary> = {}): StateCertificationSummary {
  return Object.freeze({
    certified: params.certified ?? true,
    score: params.score ?? 100,
    status: params.status ?? 'PASSED',
    certifiedAt: params.certifiedAt ?? new Date().toISOString(),
  });
}

export function createCertificationStatistics(params: Partial<CertificationStatistics> = {}): CertificationStatistics {
  return Object.freeze({
    totalCertifications: params.totalCertifications ?? 0,
    passedCertifications: params.passedCertifications ?? 0,
    failedCertifications: params.failedCertifications ?? 0,
    averageScore: params.averageScore ?? 100,
  });
}

export function createCertificationHealth(params: Partial<CertificationHealth> = {}): CertificationHealth {
  return Object.freeze({
    healthy: params.healthy ?? true,
    certified: params.certified ?? true,
    score: params.score ?? 100,
  });
}

export function createCertificationReport(
  params: Partial<CertificationReport> & { diagnostics: StateDiagnostics },
): CertificationReport {
  const issues = params.issues ?? [];
  const cert = params.certification ?? createStateCertification();
  const summary = params.summary ?? createStateCertificationSummary({ certified: cert.certified, score: cert.score });

  return Object.freeze({
    certification: cert,
    summary,
    issues: Object.freeze([...issues]),
    diagnostics: params.diagnostics,
    generatedAt: params.generatedAt ?? new Date().toISOString(),
  });
}

export function createStateConfiguration(params: Partial<StateConfiguration> = {}): StateConfiguration {
  return Object.freeze({
    runtimeName: params.runtimeName ?? 'Auralis State Runtime',
    version: params.version ?? '1.0.0',
    strictMode: params.strictMode ?? true,
    maxHistorySize: params.maxHistorySize ?? 50,
  });
}

export function createStateDiagnostics(params: Partial<StateDiagnostics> = {}): StateDiagnostics {
  return Object.freeze({
    health: params.health ?? createStateHealth(),
    statistics: params.statistics ?? createStateStatistics(),
    capabilities: params.capabilities ?? createStateCapabilities(),
    context: params.context ?? createStateContext(),
    containersCount: params.containersCount,
    actionsCount: params.actionsCount,
    reducersCount: params.reducersCount,
    middlewaresCount: params.middlewaresCount,
    selectorsCount: params.selectorsCount,
    historySize: params.historySize,
    persistenceStatus: params.persistenceStatus,
    certification: params.certification,
    certificationSummary: params.certificationSummary,
    timestamp: params.timestamp ?? new Date().toISOString(),
  });
}
