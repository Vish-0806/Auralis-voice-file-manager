import { MonitorStatusValue } from '../../models/health';
import { ObservabilitySubsystemValue } from './subsystem';

export interface ObservabilitySubsystemHealth {
  readonly subsystem: ObservabilitySubsystemValue;
  readonly status: MonitorStatusValue;
  readonly message?: string;
}

export interface ObservabilityCompositionHealth {
  readonly status: MonitorStatusValue;
  readonly subsystemHealths: ReadonlyArray<ObservabilitySubsystemHealth>;
  readonly unhealthySubsystemCount: number;
  readonly degradedSubsystemCount: number;
  readonly healthySubsystemCount: number;
  readonly generatedAt: number;
}
