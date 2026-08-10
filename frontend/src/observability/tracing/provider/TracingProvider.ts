import type { ITracingProvider, StartTraceOptions, StartSpanOptions } from '../interfaces/tracing-provider';
import type { ISpan } from '../interfaces/span';
import type { Trace } from '../models/trace';
import type { Span, SpanStatusValue } from '../models/span';
import type { TraceContext } from '../models/context';
import type { TracingStatistics, TracingDiagnostics } from '../models/statistics';
import { TracingRegistry } from '../registry/TracingRegistry';
import { SpanImpl } from './Span';
import {
  TracingStateError,
  TracingRuntimeError,
  TraceValidationError,
  TraceNotFoundError,
  SpanNotFoundError
} from '../errors/TracingErrors';
import {
  generateTraceId,
  generateSpanId,
  validateTraceId,
  validateSpanId,
  validateSpanName
} from '../factories/tracingFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class TracingProvider implements ITracingProvider {
  private lifecycleState = 'UNINITIALIZED';
  private readonly registry = new TracingRegistry();
  private readonly activeSpans = new Map<string, ISpan>();
  private readonly historyCapacity = 100;

  private traceCount = 0;
  private spanCount = 0;
  private completedSpanCount = 0;
  private errorSpanCount = 0;
  private totalDuration = 0;
  private maximumDuration = 0;
  private minimumDuration = 0;
  private eventCount = 0;

  private ensureReady(): void {
    if (this.lifecycleState !== 'READY') {
      throw new TracingStateError(`Tracing provider is not ready (current state: ${this.lifecycleState}).`);
    }
  }

  public async initialize(): Promise<void> {
    if (this.lifecycleState === 'READY') {
      return;
    }
    if (this.lifecycleState === 'INITIALIZING' || this.lifecycleState === 'STOPPING' || this.lifecycleState === 'STOPPED') {
      throw new TracingStateError(`Cannot initialize tracing provider from state: ${this.lifecycleState}`);
    }

    this.lifecycleState = 'INITIALIZING';
    try {
      this.lifecycleState = 'READY';
    } catch (err: any) {
      this.lifecycleState = 'ERROR';
      throw new TracingRuntimeError(`Failed to initialize tracing provider: ${err.message}`);
    }
  }

  public async shutdown(): Promise<void> {
    if (this.lifecycleState === 'STOPPED') {
      return;
    }
    if (this.lifecycleState === 'UNINITIALIZED') {
      throw new TracingStateError('Cannot shutdown tracing provider: it is not initialized.');
    }

    this.lifecycleState = 'STOPPING';
    try {
      for (const span of this.activeSpans.values()) {
        span.setEnabled(false);
      }
      this.activeSpans.clear();
    } finally {
      this.lifecycleState = 'STOPPED';
    }
  }

  public getState(): string {
    return this.lifecycleState;
  }

  public startTrace(name: string, options?: StartTraceOptions): ISpan {
    this.ensureReady();
    validateSpanName(name);

    const traceId = options?.traceId || generateTraceId();
    validateTraceId(traceId);

    if (this.registry.hasTrace(traceId)) {
      throw new TraceValidationError(`Trace with ID '${traceId}' is already registered.`);
    }

    const spanId = generateSpanId();
    const startTime = Date.now();

    const trace: Trace = {
      traceId,
      name,
      startTime,
      rootSpanId: spanId,
      status: 'UNSET',
      metadata: options?.metadata,
      spansCount: 1
    };

    this.registry.registerTrace(trace);
    this.traceCount += 1;

    const span = this.createSpanInstance(spanId, traceId, options?.parentSpanId, name, options?.kind || 'INTERNAL', startTime);
    this.registry.registerSpan(span.toModel());
    this.spanCount += 1;
    this.activeSpans.set(spanId, span);

    this.enforceCapacity();

    return span;
  }

  public startSpan(name: string, options: StartSpanOptions): ISpan {
    this.ensureReady();
    validateSpanName(name);

    const traceId = options.traceId;
    validateTraceId(traceId);

    const trace = this.registry.getTrace(traceId);
    if (!trace) {
      throw new TraceNotFoundError(`Cannot start span: parent trace with ID '${traceId}' not found.`, traceId);
    }

    if (options.parentSpanId) {
      validateSpanId(options.parentSpanId);
      const parentSpan = this.registry.getSpan(options.parentSpanId);
      if (!parentSpan) {
        throw new SpanNotFoundError(`Cannot start span: parent span with ID '${options.parentSpanId}' not found in registry.`, options.parentSpanId);
      }
    }

    const spanId = generateSpanId();
    const startTime = Date.now();

    const updatedTrace: Trace = {
      ...trace,
      spansCount: trace.spansCount + 1
    };
    this.registry.registerTrace(updatedTrace);

    const span = this.createSpanInstance(spanId, traceId, options.parentSpanId, name, options.kind || 'INTERNAL', startTime);
    this.registry.registerSpan(span.toModel());
    this.spanCount += 1;
    this.activeSpans.set(spanId, span);

    return span;
  }

  private createSpanInstance(
    spanId: string,
    traceId: string,
    parentSpanId: string | undefined,
    name: string,
    kind: 'INTERNAL' | 'SERVER' | 'CLIENT' | 'PRODUCER' | 'CONSUMER',
    startTime: number
  ): ISpan {
    return new SpanImpl(
      spanId,
      traceId,
      parentSpanId,
      name,
      kind,
      startTime,
      (updatedSpan) => this.handleSpanUpdated(updatedSpan),
      (endedSpan) => this.handleSpanEnded(endedSpan)
    );
  }

  private handleSpanUpdated(span: Span): void {
    if (this.lifecycleState !== 'READY') return;
    this.registry.registerSpan(span);
    this.updateTraceState(span.traceId);
  }

  private handleSpanEnded(span: Span): void {
    this.activeSpans.delete(span.spanId);
    this.completedSpanCount += 1;
    if (span.status === 'ERROR') {
      this.errorSpanCount += 1;
    }
    this.eventCount += span.events?.length || 0;

    this.registry.registerSpan(span);
    this.updateTraceState(span.traceId);
  }

  private updateTraceState(traceId: string): void {
    const trace = this.registry.getTrace(traceId);
    if (!trace) return;

    const traceSpans = this.registry.getSpansByTrace(traceId);
    
    let traceStatus: SpanStatusValue = 'UNSET';
    const hasError = traceSpans.some(s => s.status === 'ERROR');
    if (hasError) {
      traceStatus = 'ERROR';
    } else {
      const allCompleted = traceSpans.every(s => s.endTime !== undefined);
      if (allCompleted && traceSpans.length > 0) {
        traceStatus = 'OK';
      }
    }

    const rootSpan = traceSpans.find(s => s.spanId === trace.rootSpanId);
    let endTime: number | undefined;
    let duration: number | undefined;

    if (rootSpan && rootSpan.endTime !== undefined) {
      endTime = rootSpan.endTime;
      duration = rootSpan.duration;
    } else {
      const allCompleted = traceSpans.every(s => s.endTime !== undefined);
      if (allCompleted && traceSpans.length > 0) {
        const endTimes = traceSpans.map(s => s.endTime as number);
        endTime = Math.max(...endTimes);
        duration = Math.max(0, endTime - trace.startTime);
      }
    }

    const updatedTrace: Trace = {
      ...trace,
      status: traceStatus,
      endTime,
      duration
    };
    this.registry.registerTrace(updatedTrace);

    if (duration !== undefined && trace.duration === undefined) {
      this.totalDuration += duration;
      if (this.maximumDuration === 0 || duration > this.maximumDuration) {
        this.maximumDuration = duration;
      }
      if (this.minimumDuration === 0 || duration < this.minimumDuration) {
        this.minimumDuration = duration;
      }
    }
  }

  private enforceCapacity(): void {
    const tracesList = this.registry.listTraces();
    if (tracesList.length <= this.historyCapacity) {
      return;
    }

    let targetTraceId: string | null = null;
    for (let i = tracesList.length - 1; i >= 0; i--) {
      const t = tracesList[i];
      if (t.endTime !== undefined) {
        targetTraceId = t.traceId;
        break;
      }
    }

    if (!targetTraceId && tracesList.length > 0) {
      targetTraceId = tracesList[tracesList.length - 1].traceId;
    }

    if (targetTraceId) {
      this.registry.removeTrace(targetTraceId);
      this.enforceCapacity();
    }
  }

  public getTrace(traceId: string): Trace | null {
    this.ensureReady();
    return this.registry.getTrace(traceId);
  }

  public getSpan(spanId: string): Span | null {
    this.ensureReady();
    return this.registry.getSpan(spanId);
  }

  public getTraceSpans(traceId: string): ReadonlyArray<Span> {
    this.ensureReady();
    return this.registry.getSpansByTrace(traceId);
  }

  public getChildSpans(spanId: string): ReadonlyArray<Span> {
    this.ensureReady();
    return this.registry.getChildSpans(spanId);
  }

  public listRecentTraces(limit?: number): ReadonlyArray<Trace> {
    this.ensureReady();
    const list = this.registry.listTraces();
    const take = limit !== undefined ? Math.min(limit, list.length) : list.length;
    return list.slice(0, take);
  }

  public clearHistory(): void {
    this.ensureReady();
    this.activeSpans.clear();
    this.registry.clear();
    
    this.traceCount = 0;
    this.spanCount = 0;
    this.completedSpanCount = 0;
    this.errorSpanCount = 0;
    this.totalDuration = 0;
    this.maximumDuration = 0;
    this.minimumDuration = 0;
    this.eventCount = 0;
  }

  public getActiveSpans(): ReadonlyArray<ISpan> {
    this.ensureReady();
    return freezeDeepSafe(Array.from(this.activeSpans.values())) as ReadonlyArray<ISpan>;
  }

  public getActiveSpanCount(): number {
    this.ensureReady();
    return this.activeSpans.size;
  }

  public createContext(span: ISpan): TraceContext {
    this.ensureReady();
    return span.getContext();
  }

  public extractContext(context: TraceContext): TraceContext {
    this.ensureReady();
    return freezeDeepSafe({ ...context }) as TraceContext;
  }

  public injectContext(context: TraceContext): TraceContext {
    this.ensureReady();
    return freezeDeepSafe({ ...context }) as TraceContext;
  }

  public getStatistics(): TracingStatistics {
    this.ensureReady();
    const activeCount = this.activeSpans.size;
    const completedTraces = this.registry.listTraces().filter(t => t.endTime !== undefined);
    const average = completedTraces.length > 0 ? this.totalDuration / completedTraces.length : 0;

    return freezeDeepSafe({
      traceCount: this.traceCount,
      spanCount: this.spanCount,
      activeSpanCount: activeCount,
      completedSpanCount: this.completedSpanCount,
      errorSpanCount: this.errorSpanCount,
      averageDuration: average,
      totalDuration: this.totalDuration,
      maximumDuration: this.maximumDuration,
      minimumDuration: this.minimumDuration,
      eventCount: this.eventCount
    }) as TracingStatistics;
  }

  public getDiagnostics(): TracingDiagnostics {
    this.ensureReady();
    return freezeDeepSafe({
      runtimeState: this.lifecycleState,
      traceCount: this.registry.getTraceCount(),
      activeSpanCount: this.activeSpans.size,
      completedSpanCount: this.completedSpanCount,
      statistics: this.getStatistics(),
      historyCapacity: this.historyCapacity,
      generatedAt: Date.now()
    }) as TracingDiagnostics;
  }
}
