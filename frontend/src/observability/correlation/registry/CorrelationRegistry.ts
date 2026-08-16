import { CorrelatedEvent, CorrelationLink } from '../models';
import { freezeDeepSafe } from '../../models/monitoring';

export class CorrelationRegistry {
  private readonly _maxEvents: number;
  private readonly _maxLinks: number;

  // Events Indexes
  private readonly _events = new Map<string, CorrelatedEvent>(); // eventId -> Event
  private readonly _correlationIndex = new Map<string, CorrelatedEvent[]>(); // correlationId -> Events
  private readonly _traceIndex = new Map<string, CorrelatedEvent[]>(); // traceId -> Events
  private readonly _requestIndex = new Map<string, CorrelatedEvent[]>(); // requestId -> Events
  private readonly _operationIndex = new Map<string, CorrelatedEvent[]>(); // operationId -> Events
  private readonly _eventInsertionOrder: string[] = []; // EventIds in insertion order for FIFO eviction

  // Links Indexes
  private readonly _linksBySource = new Map<string, CorrelationLink[]>();
  private readonly _linksByTarget = new Map<string, CorrelationLink[]>();
  private readonly _linksList: CorrelationLink[] = []; // Links in insertion order

  private _evictedEventsCount = 0;
  private _evictedLinksCount = 0;

  constructor(maxEvents = 1000, maxLinks = 1000) {
    this._maxEvents = maxEvents;
    this._maxLinks = maxLinks;
  }

  public registerEvent(event: CorrelatedEvent): void {
    // Evict oldest if capacity exceeded
    if (this._events.size >= this._maxEvents) {
      this.evictOldestEvent();
    }

    const { eventId, context } = event;
    const { correlationId, traceId, requestId, operationId } = context;

    this._events.set(eventId, event);
    this._eventInsertionOrder.push(eventId);

    // 1. correlationId index
    if (!this._correlationIndex.has(correlationId)) {
      this._correlationIndex.set(correlationId, []);
    }
    this._correlationIndex.get(correlationId)!.push(event);

    // 2. traceId index
    if (traceId) {
      if (!this._traceIndex.has(traceId)) {
        this._traceIndex.set(traceId, []);
      }
      this._traceIndex.get(traceId)!.push(event);
    }

    // 3. requestId index
    if (requestId) {
      if (!this._requestIndex.has(requestId)) {
        this._requestIndex.set(requestId, []);
      }
      this._requestIndex.get(requestId)!.push(event);
    }

    // 4. operationId index
    if (operationId) {
      if (!this._operationIndex.has(operationId)) {
        this._operationIndex.set(operationId, []);
      }
      this._operationIndex.get(operationId)!.push(event);
    }
  }

  private evictOldestEvent(): void {
    const oldestEventId = this._eventInsertionOrder.shift();
    if (!oldestEventId) return;

    const event = this._events.get(oldestEventId);
    if (!event) return;

    this._events.delete(oldestEventId);
    this._evictedEventsCount++;

    const { context } = event;
    const { correlationId, traceId, requestId, operationId } = context;

    // Remove from correlationId index
    const corrList = this._correlationIndex.get(correlationId);
    if (corrList) {
      const idx = corrList.indexOf(event);
      if (idx !== -1) corrList.splice(idx, 1);
      if (corrList.length === 0) this._correlationIndex.delete(correlationId);
    }

    // Remove from traceId index
    if (traceId) {
      const traceList = this._traceIndex.get(traceId);
      if (traceList) {
        const idx = traceList.indexOf(event);
        if (idx !== -1) traceList.splice(idx, 1);
        if (traceList.length === 0) this._traceIndex.delete(traceId);
      }
    }

    // Remove from requestId index
    if (requestId) {
      const reqList = this._requestIndex.get(requestId);
      if (reqList) {
        const idx = reqList.indexOf(event);
        if (idx !== -1) reqList.splice(idx, 1);
        if (reqList.length === 0) this._requestIndex.delete(requestId);
      }
    }

    // Remove from operationId index
    if (operationId) {
      const opList = this._operationIndex.get(operationId);
      if (opList) {
        const idx = opList.indexOf(event);
        if (idx !== -1) opList.splice(idx, 1);
        if (opList.length === 0) this._operationIndex.delete(operationId);
      }
    }
  }

  public getEvent(eventId: string): CorrelatedEvent | null {
    const ev = this._events.get(eventId);
    return ev ? (freezeDeepSafe({ ...ev }) as CorrelatedEvent) : null;
  }

  public getEventsByCorrelationId(correlationId: string): ReadonlyArray<CorrelatedEvent> {
    const list = this._correlationIndex.get(correlationId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelatedEvent>;
  }

  public getEventsByTraceId(traceId: string): ReadonlyArray<CorrelatedEvent> {
    const list = this._traceIndex.get(traceId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelatedEvent>;
  }

  public getEventsByRequestId(requestId: string): ReadonlyArray<CorrelatedEvent> {
    const list = this._requestIndex.get(requestId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelatedEvent>;
  }

  public getEventsByOperationId(operationId: string): ReadonlyArray<CorrelatedEvent> {
    const list = this._operationIndex.get(operationId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelatedEvent>;
  }

  public listAllEvents(): ReadonlyArray<CorrelatedEvent> {
    return freezeDeepSafe(Array.from(this._events.values())) as ReadonlyArray<CorrelatedEvent>;
  }

  public registerLink(link: CorrelationLink): void {
    if (this._linksList.length >= this._maxLinks) {
      this.evictOldestLink();
    }

    this._linksList.push(link);

    // Source index
    if (!this._linksBySource.has(link.sourceId)) {
      this._linksBySource.set(link.sourceId, []);
    }
    this._linksBySource.get(link.sourceId)!.push(link);

    // Target index
    if (!this._linksByTarget.has(link.targetId)) {
      this._linksByTarget.set(link.targetId, []);
    }
    this._linksByTarget.get(link.targetId)!.push(link);
  }

  private evictOldestLink(): void {
    const oldestLink = this._linksList.shift();
    if (!oldestLink) return;

    this._evictedLinksCount++;

    // Remove from source index
    const srcList = this._linksBySource.get(oldestLink.sourceId);
    if (srcList) {
      const idx = srcList.indexOf(oldestLink);
      if (idx !== -1) srcList.splice(idx, 1);
      if (srcList.length === 0) this._linksBySource.delete(oldestLink.sourceId);
    }

    // Remove from target index
    const tgtList = this._linksByTarget.get(oldestLink.targetId);
    if (tgtList) {
      const idx = tgtList.indexOf(oldestLink);
      if (idx !== -1) tgtList.splice(idx, 1);
      if (tgtList.length === 0) this._linksByTarget.delete(oldestLink.targetId);
    }
  }

  public getLinksForSource(sourceId: string): ReadonlyArray<CorrelationLink> {
    const list = this._linksBySource.get(sourceId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelationLink>;
  }

  public getLinksForTarget(targetId: string): ReadonlyArray<CorrelationLink> {
    const list = this._linksByTarget.get(targetId) || [];
    return freezeDeepSafe([...list]) as ReadonlyArray<CorrelationLink>;
  }

  public getEventCount(): number {
    return this._events.size;
  }

  public getLinkCount(): number {
    return this._linksList.length;
  }

  public getCorrelationCount(): number {
    return this._correlationIndex.size;
  }

  public getEvictedEventsCount(): number {
    return this._evictedEventsCount;
  }

  public getEvictedLinksCount(): number {
    return this._evictedLinksCount;
  }

  public clear(): void {
    this._events.clear();
    this._correlationIndex.clear();
    this._traceIndex.clear();
    this._requestIndex.clear();
    this._operationIndex.clear();
    this._eventInsertionOrder.length = 0;

    this._linksBySource.clear();
    this._linksByTarget.clear();
    this._linksList.length = 0;

    this._evictedEventsCount = 0;
    this._evictedLinksCount = 0;
  }
}
