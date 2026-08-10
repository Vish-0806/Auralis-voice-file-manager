import { SpanKind } from '../models/span';
import { TraceValidationError, SpanValidationError } from '../errors/TracingErrors';

let traceIdCounter = 0;
let spanIdCounter = 0;

export function generateTraceId(): string {
  traceIdCounter += 1;
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID().replace(/-/g, '');
  }
  const rand = Math.random().toString(16).substring(2, 10) + Math.random().toString(16).substring(2, 10);
  return `trace${Date.now()}${traceIdCounter}${rand}`.substring(0, 32).padEnd(32, '0');
}

export function generateSpanId(): string {
  spanIdCounter += 1;
  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const arr = new Uint8Array(8);
    crypto.getRandomValues(arr);
    return Array.from(arr, b => b.toString(16).padStart(2, '0')).join('');
  }
  const rand = Math.random().toString(16).substring(2, 10);
  return `span${Date.now()}${spanIdCounter}${rand}`.substring(0, 16).padEnd(16, '0');
}

export function validateTraceId(traceId: string): void {
  if (!traceId || !traceId.trim()) {
    throw new TraceValidationError('Trace ID cannot be empty.');
  }
  if (traceId.length < 16) {
    throw new TraceValidationError(`Invalid Trace ID length: ${traceId.length}`);
  }
}

export function validateSpanId(spanId: string): void {
  if (!spanId || !spanId.trim()) {
    throw new SpanValidationError('Span ID cannot be empty.');
  }
  if (spanId.length < 8) {
    throw new SpanValidationError(`Invalid Span ID length: ${spanId.length}`);
  }
}

export function validateSpanKind(kind: string): void {
  if (!Object.values(SpanKind).includes(kind as any)) {
    throw new SpanValidationError(`Invalid span kind: ${kind}`);
  }
}

export function validateSpanName(name: string): void {
  if (!name || !name.trim()) {
    throw new SpanValidationError('Name cannot be empty or whitespace only.');
  }
}
