import type { ISpan } from '../interfaces/span';
import type { Span as SpanModel, SpanKindValue, SpanStatusValue } from '../models/span';
import type { SpanEvent } from '../models/event';
import type { StructuredError } from '../../logging/models/log';
import type { TraceContext } from '../models/context';
import { SpanStateError, SpanValidationError } from '../errors/TracingErrors';
import { createStructuredError } from '../../logging/factories/loggingFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class SpanImpl implements ISpan {
  private _enabled = true;
  private _endTime?: number;
  private _duration?: number;
  private _status: SpanStatusValue = 'UNSET';
  private readonly _attributes: Record<string, unknown> = {};
  private readonly _events: SpanEvent[] = [];
  private _error?: StructuredError;

  constructor(
    public readonly spanId: string,
    public readonly traceId: string,
    public readonly parentSpanId: string | undefined,
    public readonly name: string,
    public readonly kind: SpanKindValue,
    public readonly startTime: number,
    private readonly onSpanUpdated: (span: SpanModel) => void,
    private readonly onSpanEnded: (span: SpanModel) => void
  ) {}

  public isEnabled(): boolean {
    return this._enabled;
  }

  public setEnabled(enabled: boolean): void {
    this._enabled = enabled;
  }

  public get endTime(): number | undefined {
    return this._endTime;
  }

  public get duration(): number | undefined {
    return this._duration;
  }

  public get status(): SpanStatusValue {
    return this._status;
  }

  public get attributes(): Record<string, unknown> {
    return freezeDeepSafe({ ...this._attributes }) as Record<string, unknown>;
  }

  public get events(): ReadonlyArray<SpanEvent> {
    return freezeDeepSafe([...this._events]) as ReadonlyArray<SpanEvent>;
  }

  public get error(): StructuredError | undefined {
    return this._error ? (freezeDeepSafe(this._error) as StructuredError) : undefined;
  }

  public setAttribute(key: string, value: unknown): void {
    this.ensureActive();
    if (!key || typeof key !== 'string' || !key.trim()) {
      throw new SpanValidationError('Attribute key must be a non-empty string.');
    }
    if (value === undefined || typeof value === 'function' || typeof value === 'symbol') {
      throw new SpanValidationError('Attribute value must be a primitive or serializable type.');
    }
    this._attributes[key] = typeof value === 'object' && value !== null ? JSON.parse(JSON.stringify(value)) : value;
    this.triggerUpdate();
  }

  public setAttributes(values: Record<string, unknown>): void {
    this.ensureActive();
    if (!values || typeof values !== 'object') {
      throw new SpanValidationError('Attributes input must be a valid key-value object.');
    }
    for (const [key, val] of Object.entries(values)) {
      this.setAttribute(key, val);
    }
  }

  public addEvent(name: string, attributes?: Record<string, unknown>): void {
    this.ensureActive();
    if (!name || !name.trim()) {
      throw new SpanValidationError('Event name cannot be empty.');
    }
    const eventAttrs: Record<string, unknown> = {};
    if (attributes) {
      for (const [key, val] of Object.entries(attributes)) {
        if (val === undefined || typeof val === 'function' || typeof val === 'symbol') {
          continue;
        }
        eventAttrs[key] = typeof val === 'object' && val !== null ? JSON.parse(JSON.stringify(val)) : val;
      }
    }

    const event: SpanEvent = {
      name: name.trim(),
      timestamp: Date.now(),
      attributes: Object.keys(eventAttrs).length > 0 ? eventAttrs : undefined
    };
    this._events.push(event);
    this.triggerUpdate();
  }

  public recordError(error: Error | unknown, metadata?: Record<string, unknown>): void {
    this.ensureActive();
    const normalized = createStructuredError(error);
    this._error = normalized;
    this._status = 'ERROR';
    
    const eventAttrs: Record<string, unknown> = {
      'exception.type': normalized.name,
      'exception.message': normalized.message
    };
    if (normalized.stack) {
      eventAttrs['exception.stacktrace'] = normalized.stack;
    }
    if (metadata) {
      Object.assign(eventAttrs, metadata);
    }
    this.addEvent('exception', eventAttrs);
  }

  public setStatus(status: SpanStatusValue): void {
    this.ensureActive();
    if (status !== 'UNSET' && status !== 'OK' && status !== 'ERROR') {
      throw new SpanValidationError(`Invalid status: ${status}`);
    }
    this._status = status;
    this.triggerUpdate();
  }

  public end(): void {
    if (this._endTime !== undefined) {
      throw new SpanStateError(`Span '${this.name}' has already ended.`);
    }
    this._endTime = Date.now();
    this._duration = Math.max(0, this._endTime - this.startTime);
    
    const model = this.toModel();
    this.onSpanEnded(model);
  }

  public toModel(): SpanModel {
    return freezeDeepSafe({
      spanId: this.spanId,
      traceId: this.traceId,
      parentSpanId: this.parentSpanId,
      name: this.name,
      kind: this.kind,
      startTime: this.startTime,
      endTime: this._endTime,
      duration: this._duration,
      status: this._status,
      attributes: Object.keys(this._attributes).length > 0 ? { ...this._attributes } : undefined,
      events: this._events.length > 0 ? [...this._events] : undefined,
      error: this._error
    }) as SpanModel;
  }

  public getContext(): TraceContext {
    return freezeDeepSafe({
      traceId: this.traceId,
      spanId: this.spanId,
      parentSpanId: this.parentSpanId
    }) as TraceContext;
  }

  private ensureActive(): void {
    if (this._endTime !== undefined) {
      throw new SpanStateError(`Cannot perform operation: span '${this.name}' has already ended.`);
    }
    if (!this._enabled) {
      throw new SpanStateError(`Cannot perform operation: span '${this.name}' is disabled.`);
    }
  }

  private triggerUpdate(): void {
    this.onSpanUpdated(this.toModel());
  }
}
