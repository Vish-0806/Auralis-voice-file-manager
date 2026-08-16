import { ICorrelationProvider } from '../interfaces/correlation-provider';
import {
  CorrelationContext,
  CorrelatedEvent,
  CorrelationLink,
  CorrelationQuery,
  CorrelationStatistics,
  CorrelationDiagnostics,
  CorrelationHealthStatus,
  generateCorrelationId,
  generateEventId
} from '../models';
import { CorrelationRegistry } from '../registry/CorrelationRegistry';
import {
  CorrelationStateError,
  CorrelationValidationError,
  CorrelationContextError,
  CorrelationEventError,
  CorrelationLinkError
} from '../errors/CorrelationErrors';
import { freezeDeepSafe } from '../../models/monitoring';

const SENSITIVE_KEYS = [
  'password',
  'token',
  'secret',
  'cookie',
  'authorization',
  'api_key',
  'apikey',
  'credential',
  'private',
  'privatekey',
  'private_key'
];

export function safeNormalizeAndRedact(value: any, seen = new Set<any>()): any {
  if (value === null || value === undefined) return value;
  if (typeof value === 'function') return '[FUNCTION]';
  if (typeof value !== 'object') return value;

  if (seen.has(value)) {
    return '[CIRCULAR]';
  }

  // React element check
  if (value.$$typeof) return '[REACT_ELEMENT]';

  // DOM node check
  if (typeof value.nodeType === 'number' && typeof value.nodeName === 'string') {
    return `[DOM_NODE_${value.nodeName}]`;
  }

  // Raw Error object
  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack
    };
  }

  seen.add(value);

  // Array
  if (Array.isArray(value)) {
    const arrResult = value.map(item => safeNormalizeAndRedact(item, seen));
    seen.delete(value);
    return arrResult;
  }

  // Plain objects
  const normalized: Record<string, any> = {};
  for (const [key, val] of Object.entries(value)) {
    const lowercaseKey = key.toLowerCase();
    const isSensitive = SENSITIVE_KEYS.some(k => lowercaseKey.includes(k));
    if (isSensitive) {
      normalized[key] = '[REDACTED]';
    } else {
      normalized[key] = safeNormalizeAndRedact(val, seen);
    }
  }
  seen.delete(value);
  return normalized;
}

export class CorrelationProvider implements ICorrelationProvider {
  private _state = 'UNINITIALIZED';
  private readonly _registry: CorrelationRegistry;
  private readonly _maxEventsCapacity: number;

  private _initPromise: Promise<void> | null = null;
  private _shutdownPromise: Promise<void> | null = null;

  // Stats
  private _contextsCreated = 0;
  private _eventsRecorded = 0;
  private _linksRecorded = 0;
  private _queriesExecuted = 0;
  private _queryMatches = 0;
  private _invalidContexts = 0;
  private _invalidEvents = 0;
  private _lifecycleOperations = 0;
  private _lifecycleFailures = 0;

  constructor(dependencies?: { maxEvents?: number; maxLinks?: number }) {
    const maxEvents = dependencies?.maxEvents ?? 1000;
    const maxLinks = dependencies?.maxLinks ?? 1000;
    this._maxEventsCapacity = maxEvents;
    this._registry = new CorrelationRegistry(maxEvents, maxLinks);
  }

  private ensureReady(): void {
    if (this._state !== 'READY') {
      throw new CorrelationStateError(`Correlation provider is not ready (state: ${this._state}).`);
    }
  }

  public initialize(): Promise<void> {
    if (this._state === 'READY') {
      return Promise.resolve();
    }
    if (this._state === 'INITIALIZING') {
      return this._initPromise || Promise.resolve();
    }
    if (this._state === 'STOPPING') {
      return Promise.reject(new CorrelationStateError('Cannot initialize while stopping.'));
    }

    this._state = 'INITIALIZING';
    this._lifecycleOperations++;

    this._initPromise = (async () => {
      await Promise.resolve();
      try {
        this._state = 'READY';
      } catch (err) {
        this._state = 'FAILED';
        this._lifecycleFailures++;
        throw err;
      } finally {
        this._initPromise = null;
      }
    })();

    return this._initPromise;
  }

  public shutdown(): Promise<void> {
    if (this._state === 'STOPPED' || this._state === 'UNINITIALIZED') {
      return Promise.resolve();
    }
    if (this._state === 'STOPPING') {
      return this._shutdownPromise || Promise.resolve();
    }

    this._state = 'STOPPING';
    this._lifecycleOperations++;

    this._shutdownPromise = (async () => {
      await Promise.resolve();
      try {
        this._registry.clear();
        this._state = 'STOPPED';
      } catch (err) {
        this._state = 'FAILED';
        this._lifecycleFailures++;
        throw err;
      } finally {
        this._shutdownPromise = null;
      }
    })();

    return this._shutdownPromise;
  }

  public getState(): string {
    return this._state;
  }

  public createContext(options?: {
    traceId?: string;
    spanId?: string;
    parentCorrelationId?: string;
    requestId?: string;
    operationId?: string;
    source?: string;
    metadata?: Record<string, unknown>;
  }): CorrelationContext {
    this.ensureReady();

    const correlationId = generateCorrelationId();
    const timestamp = Date.now();
    const metadata = options?.metadata ? safeNormalizeAndRedact(options.metadata) : undefined;

    const context: CorrelationContext = {
      correlationId,
      traceId: options?.traceId,
      spanId: options?.spanId,
      parentCorrelationId: options?.parentCorrelationId,
      requestId: options?.requestId,
      operationId: options?.operationId,
      source: options?.source,
      timestamp,
      metadata
    };

    try {
      this.validateContext(context);
    } catch (err) {
      this._invalidContexts++;
      throw err;
    }

    this._contextsCreated++;

    return freezeDeepSafe(context) as CorrelationContext;
  }

  public childContext(
    parentContext: CorrelationContext,
    overrides?: Partial<CorrelationContext>
  ): CorrelationContext {
    this.ensureReady();
    this.validateContext(parentContext);

    const metadata = overrides?.metadata
      ? safeNormalizeAndRedact({ ...parentContext.metadata, ...overrides.metadata })
      : parentContext.metadata;

    const context: CorrelationContext = {
      correlationId: parentContext.correlationId,
      parentCorrelationId: parentContext.correlationId,
      traceId: overrides?.traceId ?? parentContext.traceId,
      spanId: overrides?.spanId ?? parentContext.spanId,
      requestId: overrides?.requestId ?? parentContext.requestId,
      operationId: overrides?.operationId ?? parentContext.operationId,
      source: overrides?.source ?? parentContext.source,
      timestamp: overrides?.timestamp ?? Date.now(),
      metadata
    };

    try {
      this.validateContext(context);
    } catch (err) {
      this._invalidContexts++;
      throw err;
    }

    return freezeDeepSafe(context) as CorrelationContext;
  }

  public validateContext(context: CorrelationContext): void {
    if (!context) {
      throw new CorrelationValidationError('Context object is required.');
    }
    if (!context.correlationId || typeof context.correlationId !== 'string' || context.correlationId.trim() === '') {
      throw new CorrelationContextError('Correlation ID is missing or invalid.');
    }
    if (!context.timestamp || typeof context.timestamp !== 'number' || context.timestamp <= 0) {
      throw new CorrelationValidationError('Correlation timestamp must be a valid number.');
    }
  }

  public recordEvent(eventInput: {
    eventId?: string;
    eventType: string;
    context: CorrelationContext;
    sourceSubsystem: string;
    metadata?: Record<string, unknown>;
    payload?: Record<string, unknown>;
  }): CorrelatedEvent {
    this.ensureReady();

    // 1. Validate context
    try {
      this.validateContext(eventInput.context);
    } catch (err) {
      this._invalidEvents++;
      throw err;
    }

    // 2. Validate input fields
    if (eventInput.eventId !== undefined && (typeof eventInput.eventId !== 'string' || eventInput.eventId.trim() === '')) {
      this._invalidEvents++;
      throw new CorrelationEventError('Provided event ID must be a non-empty string.');
    }
    if (!eventInput.eventType || typeof eventInput.eventType !== 'string' || eventInput.eventType.trim() === '') {
      this._invalidEvents++;
      throw new CorrelationEventError('Event type is missing or invalid.');
    }
    if (!eventInput.sourceSubsystem || typeof eventInput.sourceSubsystem !== 'string' || eventInput.sourceSubsystem.trim() === '') {
      this._invalidEvents++;
      throw new CorrelationEventError('Source subsystem is missing or invalid.');
    }

    // 3. Normalize / Redact metadata and payload
    const normalizedMetadata = eventInput.metadata ? safeNormalizeAndRedact(eventInput.metadata) : undefined;
    const normalizedPayload = eventInput.payload ? safeNormalizeAndRedact(eventInput.payload) : undefined;

    const eventId = eventInput.eventId || generateEventId();
    const event: CorrelatedEvent = {
      eventId,
      eventType: eventInput.eventType,
      timestamp: Date.now(),
      context: eventInput.context,
      sourceSubsystem: eventInput.sourceSubsystem,
      metadata: normalizedMetadata,
      payload: normalizedPayload
    };

    // 4. Storing in Registry
    this._registry.registerEvent(event);

    this._eventsRecorded++;

    return freezeDeepSafe(event) as CorrelatedEvent;
  }

  public getEvent(eventId: string): CorrelatedEvent | null {
    this.ensureReady();
    return this._registry.getEvent(eventId);
  }

  public query(query: CorrelationQuery): ReadonlyArray<CorrelatedEvent> {
    this.ensureReady();
    this._queriesExecuted++;

    let candidates: ReadonlyArray<CorrelatedEvent> = [];

    if (query.correlationId) {
      candidates = this._registry.getEventsByCorrelationId(query.correlationId);
    } else if (query.traceId) {
      candidates = this._registry.getEventsByTraceId(query.traceId);
    } else if (query.requestId) {
      candidates = this._registry.getEventsByRequestId(query.requestId);
    } else if (query.operationId) {
      candidates = this._registry.getEventsByOperationId(query.operationId);
    } else {
      candidates = this._registry.listAllEvents();
    }

    const filtered = candidates.filter(ev => {
      if (query.eventType && ev.eventType !== query.eventType) {
        return false;
      }
      if (query.source && ev.sourceSubsystem !== query.source && ev.context.source !== query.source) {
        return false;
      }
      if (query.startTime !== undefined && ev.timestamp < query.startTime) {
        return false;
      }
      if (query.endTime !== undefined && ev.timestamp > query.endTime) {
        return false;
      }
      return true;
    });

    const sorted = [...filtered].sort((a, b) => a.timestamp - b.timestamp);

    this._queryMatches += sorted.length;

    return freezeDeepSafe(sorted) as ReadonlyArray<CorrelatedEvent>;
  }

  public addLink(link: {
    sourceId: string;
    targetId: string;
    kind: string;
    metadata?: Record<string, unknown>;
  }): CorrelationLink {
    this.ensureReady();

    if (!link.sourceId || typeof link.sourceId !== 'string' || link.sourceId.trim() === '') {
      throw new CorrelationLinkError('Source ID is missing or invalid.');
    }
    if (!link.targetId || typeof link.targetId !== 'string' || link.targetId.trim() === '') {
      throw new CorrelationLinkError('Target ID is missing or invalid.');
    }
    if (!link.kind || typeof link.kind !== 'string' || link.kind.trim() === '') {
      throw new CorrelationLinkError('Link kind is missing or invalid.');
    }

    const normalizedMetadata = link.metadata ? safeNormalizeAndRedact(link.metadata) : undefined;

    const linkObj: CorrelationLink = {
      sourceId: link.sourceId,
      targetId: link.targetId,
      kind: link.kind as any,
      metadata: normalizedMetadata
    };

    this._registry.registerLink(linkObj);

    this._linksRecorded++;

    return freezeDeepSafe(linkObj) as CorrelationLink;
  }

  public getLinksForSource(sourceId: string): ReadonlyArray<CorrelationLink> {
    this.ensureReady();
    return this._registry.getLinksForSource(sourceId);
  }

  public getLinksForTarget(targetId: string): ReadonlyArray<CorrelationLink> {
    this.ensureReady();
    return this._registry.getLinksForTarget(targetId);
  }

  public getDiagnostics(): CorrelationDiagnostics {
    const stats = this.getStatistics();
    const health = this.getHealth();

    return freezeDeepSafe({
      runtimeState: this._state,
      eventCount: this._registry.getEventCount(),
      linkCount: this._registry.getLinkCount(),
      correlationCount: this._registry.getCorrelationCount(),
      statistics: stats,
      configuredCapacity: this._maxEventsCapacity,
      generatedAt: Date.now(),
      healthStatus: health
    }) as CorrelationDiagnostics;
  }

  public getStatistics(): CorrelationStatistics {
    return freezeDeepSafe({
      contextsCreated: this._contextsCreated,
      eventsRecorded: this._eventsRecorded,
      linksRecorded: this._linksRecorded,
      queriesExecuted: this._queriesExecuted,
      queryMatches: this._queryMatches,
      invalidContexts: this._invalidContexts,
      invalidEvents: this._invalidEvents,
      evictedEvents: this._registry.getEvictedEventsCount(),
      evictedLinks: this._registry.getEvictedLinksCount(),
      lifecycleOperations: this._lifecycleOperations,
      lifecycleFailures: this._lifecycleFailures
    }) as CorrelationStatistics;
  }

  public getHealth(): CorrelationHealthStatus {
    if (this._state === 'UNINITIALIZED') {
      return 'UNKNOWN';
    }
    if (this._state === 'FAILED') {
      return 'UNHEALTHY';
    }
    if (this._state === 'READY') {
      const currentEvents = this._registry.getEventCount();
      if (currentEvents >= this._maxEventsCapacity) {
        return 'DEGRADED';
      }
      return 'HEALTHY';
    }
    return 'UNKNOWN';
  }
}
