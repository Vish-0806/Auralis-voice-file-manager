import { ObservabilityCompositionStateValue } from './state';
import { ObservabilitySubsystemState } from './subsystem';
import { ObservabilityCompositionHealth } from './health';
import { ObservabilityCompositionStatistics } from './statistics';

export interface ObservabilityCompositionDiagnostics {
  readonly compositionState: ObservabilityCompositionStateValue;
  readonly subsystemStates: ReadonlyArray<ObservabilitySubsystemState>;
  readonly health: ObservabilityCompositionHealth;
  readonly statistics: ObservabilityCompositionStatistics;
  readonly generatedAt: number;
}
