import type { Trace } from '../models/trace';
import type { Span } from '../models/span';
import { TraceNotFoundError, SpanNotFoundError, TraceValidationError } from '../errors/TracingErrors';
import { freezeDeepSafe } from '../../models/monitoring';

export class TracingRegistry {
  private readonly traces = new Map<string, Trace>();
  private readonly spans = new Map<string, Span>();
  private readonly spansByTrace = new Map<string, Map<string, Span>>();
  private readonly childSpans = new Map<string, Map<string, Span>>();

  public registerTrace(trace: Trace): void {
    if (!trace || !trace.traceId) {
      throw new TraceValidationError('Invalid trace definition.');
    }
    this.traces.set(trace.traceId, trace);
  }

  public getTrace(traceId: string): Trace | null {
    const trace = this.traces.get(traceId);
    return trace ? (freezeDeepSafe(trace) as Trace) : null;
  }

  public hasTrace(traceId: string): boolean {
    return this.traces.has(traceId);
  }

  public removeTrace(traceId: string): void {
    if (!this.traces.has(traceId)) {
      throw new TraceNotFoundError(`Trace with ID '${traceId}' not found.`, traceId);
    }
    this.traces.delete(traceId);
    
    const traceSpansMap = this.spansByTrace.get(traceId);
    if (traceSpansMap) {
      for (const spanId of traceSpansMap.keys()) {
        this.spans.delete(spanId);
        this.childSpans.delete(spanId);
      }
      this.spansByTrace.delete(traceId);
    }
  }

  public listTraces(): ReadonlyArray<Trace> {
    const list = Array.from(this.traces.values());
    list.sort((a, b) => b.startTime - a.startTime);
    return freezeDeepSafe(list) as ReadonlyArray<Trace>;
  }

  public registerSpan(span: Span): void {
    if (!span || !span.spanId) {
      throw new TraceValidationError('Invalid span definition.');
    }
    if (!this.traces.has(span.traceId)) {
      throw new TraceNotFoundError(`Cannot register span: parent trace with ID '${span.traceId}' does not exist.`, span.traceId);
    }

    this.spans.set(span.spanId, span);

    let traceMap = this.spansByTrace.get(span.traceId);
    if (!traceMap) {
      traceMap = new Map<string, Span>();
      this.spansByTrace.set(span.traceId, traceMap);
    }
    traceMap.set(span.spanId, span);

    if (span.parentSpanId) {
      let childMap = this.childSpans.get(span.parentSpanId);
      if (!childMap) {
        childMap = new Map<string, Span>();
        this.childSpans.set(span.parentSpanId, childMap);
      }
      childMap.set(span.spanId, span);
    }
  }

  public getSpan(spanId: string): Span | null {
    const span = this.spans.get(spanId);
    return span ? (freezeDeepSafe(span) as Span) : null;
  }

  public removeSpan(spanId: string): void {
    const span = this.spans.get(spanId);
    if (!span) {
      throw new SpanNotFoundError(`Span with ID '${spanId}' not found.`, spanId);
    }
    this.spans.delete(spanId);

    const traceMap = this.spansByTrace.get(span.traceId);
    if (traceMap) {
      traceMap.delete(spanId);
      if (traceMap.size === 0) {
        this.spansByTrace.delete(span.traceId);
      }
    }

    if (span.parentSpanId) {
      const childMap = this.childSpans.get(span.parentSpanId);
      if (childMap) {
        childMap.delete(spanId);
        if (childMap.size === 0) {
          this.childSpans.delete(span.parentSpanId);
        }
      }
    }
    this.childSpans.delete(spanId);
  }

  public getSpansByTrace(traceId: string): ReadonlyArray<Span> {
    const traceMap = this.spansByTrace.get(traceId);
    if (!traceMap) return [];
    const list = Array.from(traceMap.values());
    list.sort((a, b) => a.startTime - b.startTime);
    return freezeDeepSafe(list) as ReadonlyArray<Span>;
  }

  public getChildSpans(parentSpanId: string): ReadonlyArray<Span> {
    const childMap = this.childSpans.get(parentSpanId);
    if (!childMap) return [];
    const list = Array.from(childMap.values());
    list.sort((a, b) => a.startTime - b.startTime);
    return freezeDeepSafe(list) as ReadonlyArray<Span>;
  }

  public clear(): void {
    this.traces.clear();
    this.spans.clear();
    this.spansByTrace.clear();
    this.childSpans.clear();
  }

  public getTraceCount(): number {
    return this.traces.size;
  }

  public getSpanCount(): number {
    return this.spans.size;
  }
}
