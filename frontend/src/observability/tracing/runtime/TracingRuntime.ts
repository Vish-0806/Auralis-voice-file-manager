import type { ITracingRuntime } from '../interfaces/tracing-runtime';
import type { ITracingProvider, StartTraceOptions, StartSpanOptions } from '../interfaces/tracing-provider';
import type { ISpan } from '../interfaces/span';
import type { Trace } from '../models/trace';
import type { Span } from '../models/span';
import type { TraceContext } from '../models/context';
import type { TracingStatistics, TracingDiagnostics } from '../models/statistics';
import { TracingProvider } from '../provider/TracingProvider';

export class TracingRuntime implements ITracingRuntime {
  private readonly _provider: ITracingProvider;

  constructor(provider?: ITracingProvider) {
    this._provider = provider || new TracingProvider();
  }

  public provider(): ITracingProvider {
    return this._provider;
  }

  public initialize(): Promise<void> {
    return this._provider.initialize();
  }

  public shutdown(): Promise<void> {
    return this._provider.shutdown();
  }

  public getState(): string {
    return this._provider.getState();
  }

  public startTrace(name: string, options?: StartTraceOptions): ISpan {
    return this._provider.startTrace(name, options);
  }

  public startSpan(name: string, options: StartSpanOptions): ISpan {
    return this._provider.startSpan(name, options);
  }

  public getTrace(traceId: string): Trace | null {
    return this._provider.getTrace(traceId);
  }

  public getSpan(spanId: string): Span | null {
    return this._provider.getSpan(spanId);
  }

  public getTraceSpans(traceId: string): ReadonlyArray<Span> {
    return this._provider.getTraceSpans(traceId);
  }

  public getChildSpans(spanId: string): ReadonlyArray<Span> {
    return this._provider.getChildSpans(spanId);
  }

  public listRecentTraces(limit?: number): ReadonlyArray<Trace> {
    return this._provider.listRecentTraces(limit);
  }

  public clearHistory(): void {
    this._provider.clearHistory();
  }

  public getActiveSpans(): ReadonlyArray<ISpan> {
    return this._provider.getActiveSpans();
  }

  public getActiveSpanCount(): number {
    return this._provider.getActiveSpanCount();
  }

  public createContext(span: ISpan): TraceContext {
    return this._provider.createContext(span);
  }

  public extractContext(context: TraceContext): TraceContext {
    return this._provider.extractContext(context);
  }

  public injectContext(context: TraceContext): TraceContext {
    return this._provider.injectContext(context);
  }

  public getStatistics(): TracingStatistics {
    return this._provider.getStatistics();
  }

  public getDiagnostics(): TracingDiagnostics {
    return this._provider.getDiagnostics();
  }
}
