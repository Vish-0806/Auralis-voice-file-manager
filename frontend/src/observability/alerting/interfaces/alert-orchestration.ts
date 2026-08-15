import {
  AlertOrchestrationRequest,
  AlertOrchestrationResult
} from '../models/orchestration';

export interface IAlertOrchestrationManager {
  orchestrate(request: AlertOrchestrationRequest): Promise<AlertOrchestrationResult>;
  orchestrateMany(requests: ReadonlyArray<AlertOrchestrationRequest>): Promise<ReadonlyArray<AlertOrchestrationResult>>;
  getResult(orchestrationId: string): AlertOrchestrationResult | null;
  getHistory(): ReadonlyArray<AlertOrchestrationResult>;
}
