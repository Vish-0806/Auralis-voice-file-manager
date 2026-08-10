import {
  type MonitoringComponent,
  type MonitoringCheck,
  type MonitoringResult,
  freezeDeepSafe,
  type MonitoringComponentTypeValue,
  MonitoringComponentType
} from '../models/monitoring';
import { MonitorStatus, type MonitorStatusValue } from '../models/health';
import { MonitoringValidationError } from '../errors/MonitoringErrors';

export function validateId(id: string, fieldName = 'id'): void {
  if (!id || typeof id !== 'string') {
    throw new MonitoringValidationError(`Required field '${fieldName}' is missing or not a string.`);
  }
  if (!id.trim()) {
    throw new MonitoringValidationError(`Field '${fieldName}' cannot be empty or whitespace only.`);
  }
}

export function validateName(name: string, fieldName = 'name'): void {
  if (!name || typeof name !== 'string') {
    throw new MonitoringValidationError(`Required field '${fieldName}' is missing or not a string.`);
  }
  if (!name.trim()) {
    throw new MonitoringValidationError(`Field '${fieldName}' cannot be empty or whitespace only.`);
  }
}

export function createMonitoringComponent(input: {
  id: string;
  name: string;
  type: MonitoringComponentTypeValue;
  status?: MonitorStatusValue;
  enabled?: boolean;
  registeredAt?: number;
  lastCheckedAt?: number;
  metadata?: Record<string, unknown>;
}): MonitoringComponent {
  validateId(input.id, 'id');
  validateName(input.name, 'name');
  
  if (!Object.values(MonitoringComponentType).includes(input.type)) {
    throw new MonitoringValidationError(`Invalid component type: ${input.type}`);
  }

  const status = input.status ?? MonitorStatus.UNKNOWN;
  if (!Object.values(MonitorStatus).includes(status)) {
    throw new MonitoringValidationError(`Invalid monitor status: ${status}`);
  }

  const component: MonitoringComponent = {
    id: input.id,
    name: input.name,
    type: input.type,
    status,
    enabled: input.enabled ?? true,
    registeredAt: input.registeredAt ?? Date.now(),
    lastCheckedAt: input.lastCheckedAt,
    metadata: input.metadata ?? {}
  };

  return freezeDeepSafe(component);
}

export function createMonitoringCheck(input: {
  id: string;
  componentId: string;
  name: string;
  description?: string;
  enabled?: boolean;
  executionOrder?: number;
  timeoutMs?: number;
  metadata?: Record<string, unknown>;
  execute: () => void | Promise<void>;
}): MonitoringCheck {
  validateId(input.id, 'id');
  validateId(input.componentId, 'componentId');
  validateName(input.name, 'name');

  if (typeof input.execute !== 'function') {
    throw new MonitoringValidationError('Check execution callback must be a function.');
  }

  const executionOrder = input.executionOrder ?? 0;
  if (typeof executionOrder !== 'number' || executionOrder < 0 || !Number.isInteger(executionOrder)) {
    throw new MonitoringValidationError(`Invalid execution order: ${executionOrder}. Must be a non-negative integer.`);
  }

  const timeoutMs = input.timeoutMs ?? 5000;
  if (typeof timeoutMs !== 'number' || timeoutMs < 0) {
    throw new MonitoringValidationError(`Invalid timeout: ${timeoutMs}. Must be a non-negative number.`);
  }

  const check: MonitoringCheck = {
    id: input.id,
    componentId: input.componentId,
    name: input.name,
    description: input.description,
    enabled: input.enabled ?? true,
    executionOrder,
    timeoutMs,
    metadata: input.metadata ?? {},
    execute: input.execute
  };

  return freezeDeepSafe(check);
}

export function createMonitoringResult(input: {
  checkId: string;
  componentId: string;
  status: MonitorStatusValue;
  startedAt: number;
  completedAt: number;
  durationMs: number;
  message?: string;
  details?: unknown;
  error?: Error;
}): MonitoringResult {
  validateId(input.checkId, 'checkId');
  validateId(input.componentId, 'componentId');

  if (!Object.values(MonitorStatus).includes(input.status)) {
    throw new MonitoringValidationError(`Invalid monitor status: ${input.status}`);
  }

  if (typeof input.startedAt !== 'number' || input.startedAt < 0) {
    throw new MonitoringValidationError(`Invalid startedAt: ${input.startedAt}`);
  }

  if (typeof input.completedAt !== 'number' || input.completedAt < 0) {
    throw new MonitoringValidationError(`Invalid completedAt: ${input.completedAt}`);
  }

  if (typeof input.durationMs !== 'number' || input.durationMs < 0) {
    throw new MonitoringValidationError(`Invalid durationMs: ${input.durationMs}`);
  }

  const result: MonitoringResult = {
    checkId: input.checkId,
    componentId: input.componentId,
    status: input.status,
    startedAt: input.startedAt,
    completedAt: input.completedAt,
    durationMs: input.durationMs,
    message: input.message,
    details: input.details,
    error: input.error
  };

  return freezeDeepSafe(result);
}
