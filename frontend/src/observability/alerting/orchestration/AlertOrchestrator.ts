import { IAlertingProvider } from '../interfaces/alerting-provider';
import {
  AlertOrchestrationRequest,
  AlertOrchestrationResult,
  AlertOrchestrationStageResult,
  AlertOrchestrationStatusValue
} from '../models/orchestration';
import {
  AlertOrchestrationFailureError
} from '../errors/AlertingErrors';
import {
  createAlertOrchestrationResult,
  createAlertOrchestrationStageResult,
  createNotificationRequest
} from '../factories/alertingFactories';
import { freezeDeepSafe } from '../../models/monitoring';

export class AlertOrchestrator {
  private readonly _provider: IAlertingProvider;
  private readonly _history: AlertOrchestrationResult[] = [];
  private readonly _maxHistorySize: number;
  private readonly _inFlight = new Map<string, Promise<AlertOrchestrationResult>>();

  private _orchestrationsTotal = 0;
  private _orchestrationsSuccessful = 0;
  private _orchestrationsSkipped = 0;
  private _orchestrationsDuplicate = 0;
  private _orchestrationsSuppressed = 0;
  private _orchestrationsFailed = 0;
  private _totalOrchestrationDuration = 0;

  constructor(provider: IAlertingProvider, maxHistorySize = 1000) {
    this._provider = provider;
    this._maxHistorySize = maxHistorySize;
  }

  public orchestrate(request: AlertOrchestrationRequest): Promise<AlertOrchestrationResult> {
    const existing = this._inFlight.get(request.orchestrationId);
    if (existing) {
      return existing;
    }

    const execution = (async () => {
      this._orchestrationsTotal++;
      const attemptedAt = Date.now();
      const stageResults: AlertOrchestrationStageResult[] = [];

      let alertId: string | undefined;
      let fingerprint: string | undefined;
      let status: AlertOrchestrationStatusValue = 'RUNNING';

      let evaluationResult: any;
      let generationResult: any;
      let deduplicationDecision: any;
      let suppressionDecision: any;
      let lifecycleResult: any;
      let notificationResult: any;
      let finalError: any;

      const rule = this._provider.getRule(request.ruleId);
      if (!rule) {
        this._orchestrationsFailed++;
        const finished = Date.now();
        const finalResult = createAlertOrchestrationResult({
          orchestrationId: request.orchestrationId,
          ruleId: request.ruleId,
          status: 'FAILED',
          stageResults: [
            createAlertOrchestrationStageResult({
              stage: 'EVALUATION',
              status: 'FAILED',
              timestamp: attemptedAt,
              duration: 0,
              error: { name: 'RuleNotFoundError', message: `Rule with ID ${request.ruleId} not found` }
            })
          ],
          attemptedAt,
          completedAt: finished,
          duration: finished - attemptedAt
        });
        this.logResult(finalResult);
        throw new AlertOrchestrationFailureError(`Rule with ID ${request.ruleId} not found`);
      }

      // STEP 1 — RULE EVALUATION
      const evalStart = Date.now();
      try {
        evaluationResult = this._provider.evaluateRule(rule, request.context);
        const evalDuration = Date.now() - evalStart;

        if (evaluationResult.status === 'NOT_MATCHED' || evaluationResult.status === 'SKIPPED') {
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'EVALUATION',
              status: 'SKIPPED',
              timestamp: evalStart,
              duration: evalDuration
            })
          );
          status = 'SKIPPED';
        } else if (evaluationResult.status === 'ERROR') {
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'EVALUATION',
              status: 'FAILED',
              timestamp: evalStart,
              duration: evalDuration,
              error: evaluationResult.error
            })
          );
          status = 'FAILED';
        } else {
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'EVALUATION',
              status: 'SUCCESS',
              timestamp: evalStart,
              duration: evalDuration
            })
          );
        }
      } catch (err: any) {
        const evalDuration = Date.now() - evalStart;
        finalError = {
          name: err.name || 'EvaluationError',
          message: err.message || 'Error occurred during evaluation',
          stack: err.stack
        };
        stageResults.push(
          createAlertOrchestrationStageResult({
            stage: 'EVALUATION',
            status: 'FAILED',
            timestamp: evalStart,
            duration: evalDuration,
            error: finalError
          })
        );
        status = 'FAILED';
      }

      // STEP 2 — ALERT GENERATION
      if (status === 'RUNNING') {
        const genStart = Date.now();
        try {
          generationResult = this._provider.generateAlert(rule, evaluationResult);
          alertId = generationResult.id;
          fingerprint = generationResult.fingerprint;
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'GENERATION',
              status: 'SUCCESS',
              timestamp: genStart,
              duration: Date.now() - genStart
            })
          );
        } catch (err: any) {
          finalError = {
            name: err.name || 'GenerationError',
            message: err.message || 'Error occurred during generation',
            stack: err.stack
          };
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'GENERATION',
              status: 'FAILED',
              timestamp: genStart,
              duration: Date.now() - genStart,
              error: finalError
            })
          );
          status = 'FAILED';
        }
      }

      // STEP 3 — DEDUPLICATION
      if (status === 'RUNNING' && generationResult) {
        const dedupStart = Date.now();
        try {
          deduplicationDecision = this._provider.checkDeduplication(generationResult, dedupStart);
          const dedupDuration = Date.now() - dedupStart;

          if (deduplicationDecision.duplicate || deduplicationDecision.cooldownSuppressed) {
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'DEDUPLICATION',
                status: 'DUPLICATE',
                timestamp: dedupStart,
                duration: dedupDuration
              })
            );
            status = 'DUPLICATE';
          } else {
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'DEDUPLICATION',
                status: 'SUCCESS',
                timestamp: dedupStart,
                duration: dedupDuration
              })
            );
          }
        } catch (err: any) {
          finalError = {
            name: err.name || 'DeduplicationError',
            message: err.message || 'Error occurred during deduplication',
            stack: err.stack
          };
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'DEDUPLICATION',
              status: 'FAILED',
              timestamp: dedupStart,
              duration: Date.now() - dedupStart,
              error: finalError
            })
          );
          status = 'FAILED';
        }
      }

      // STEP 4 — SUPPRESSION
      if (status === 'RUNNING' && generationResult) {
        const suppStart = Date.now();
        try {
          suppressionDecision = this._provider.evaluateSuppression(generationResult, suppStart);
          const suppDuration = Date.now() - suppStart;

          if (suppressionDecision.suppressed) {
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'SUPPRESSION',
                status: 'SUPPRESSED',
                timestamp: suppStart,
                duration: suppDuration
              })
            );
            status = 'SUPPRESSED';
          } else {
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'SUPPRESSION',
                status: 'SUCCESS',
                timestamp: suppStart,
                duration: suppDuration
              })
            );
          }
        } catch (err: any) {
          finalError = {
            name: err.name || 'SuppressionError',
            message: err.message || 'Error occurred during suppression',
            stack: err.stack
          };
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'SUPPRESSION',
              status: 'FAILED',
              timestamp: suppStart,
              duration: Date.now() - suppStart,
              error: finalError
            })
          );
          status = 'FAILED';
        }
      }

      // STEP 5 — LIFECYCLE
      if (status === 'RUNNING' && generationResult) {
        const lifeStart = Date.now();
        try {
          lifecycleResult = this._provider.initializeAlertLifecycle(generationResult.id, generationResult.fingerprint, lifeStart);
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'LIFECYCLE',
              status: 'SUCCESS',
              timestamp: lifeStart,
              duration: Date.now() - lifeStart
            })
          );
        } catch (err: any) {
          finalError = {
            name: err.name || 'LifecycleError',
            message: err.message || 'Error occurred during lifecycle initialization',
            stack: err.stack
          };
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'LIFECYCLE',
              status: 'FAILED',
              timestamp: lifeStart,
              duration: Date.now() - lifeStart,
              error: finalError
            })
          );
          status = 'FAILED';
        }
      }

      // STEP 6 — NOTIFICATION
      if (status === 'RUNNING' && generationResult && request.channelId && request.recipient) {
        const notifStart = Date.now();
        try {
          const notifReq = createNotificationRequest({
            id: `notif-${request.orchestrationId}`,
            alertId: generationResult.id,
            fingerprint: generationResult.fingerprint,
            channelId: request.channelId,
            payload: {
              title: generationResult.title,
              message: generationResult.message,
              severity: generationResult.severity,
              metadata: generationResult.metadata
            },
            priority: request.priority || 'NORMAL',
            channelType: request.channelType || 'CUSTOM',
            recipient: request.recipient,
            createdAt: notifStart,
            correlationId: request.correlationId
          });

          notificationResult = await this._provider.dispatchNotification(notifReq);
          const notifDuration = Date.now() - notifStart;

          if (notificationResult.status === 'DELIVERED') {
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'NOTIFICATION',
                status: 'SUCCESS',
                timestamp: notifStart,
                duration: notifDuration
              })
            );
            status = 'SUCCESS';
          } else {
            const notifStatus = notificationResult.status === 'SKIPPED' ? 'SKIPPED' : 'FAILED';
            stageResults.push(
              createAlertOrchestrationStageResult({
                stage: 'NOTIFICATION',
                status: notifStatus,
                timestamp: notifStart,
                duration: notifDuration,
                error: notificationResult.error
              })
            );
            status = notificationResult.status === 'SKIPPED' ? 'SKIPPED' : 'COMPLETED';
          }
        } catch (err: any) {
          const notifDuration = Date.now() - notifStart;
          finalError = {
            name: err.name || 'NotificationDispatchError',
            message: err.message || 'Error occurred during notification dispatch',
            stack: err.stack
          };
          stageResults.push(
            createAlertOrchestrationStageResult({
              stage: 'NOTIFICATION',
              status: 'FAILED',
              timestamp: notifStart,
              duration: notifDuration,
              error: finalError
            })
          );
          status = 'COMPLETED';
        }
      } else if (status === 'RUNNING') {
        status = 'SUCCESS';
      }

      const totalDuration = Date.now() - attemptedAt;
      this._totalOrchestrationDuration += totalDuration;

      if (status === 'SUCCESS') {
        this._orchestrationsSuccessful++;
      } else if (status === 'SKIPPED') {
        this._orchestrationsSkipped++;
      } else if (status === 'DUPLICATE') {
        this._orchestrationsDuplicate++;
      } else if (status === 'SUPPRESSED') {
        this._orchestrationsSuppressed++;
      } else if (status === 'FAILED') {
        this._orchestrationsFailed++;
      }

      const finalResult = createAlertOrchestrationResult({
        orchestrationId: request.orchestrationId,
        alertId,
        ruleId: request.ruleId,
        fingerprint,
        status,
        stageResults,
        evaluationResult,
        generationResult,
        deduplicationDecision,
        suppressionDecision,
        lifecycleResult,
        notificationResult,
        attemptedAt,
        completedAt: Date.now(),
        duration: totalDuration
      });

      this.logResult(finalResult);

      if (status === 'FAILED' && finalError) {
        throw new AlertOrchestrationFailureError(finalError.message || 'Orchestration failed');
      }

      return finalResult;
    })();

    this._inFlight.set(request.orchestrationId, execution);

    execution.catch(() => {}).finally(() => {
      this._inFlight.delete(request.orchestrationId);
    });

    return execution;
  }

  public async orchestrateMany(
    requests: ReadonlyArray<AlertOrchestrationRequest>
  ): Promise<ReadonlyArray<AlertOrchestrationResult>> {
    if (!requests) {
      return [];
    }

    const promises = requests.map(req => {
      return this.orchestrate(req).catch(err => {
        return (
          this.getResult(req.orchestrationId) ||
          createAlertOrchestrationResult({
            orchestrationId: req.orchestrationId,
            ruleId: req.ruleId,
            status: 'FAILED',
            stageResults: [
              createAlertOrchestrationStageResult({
                stage: 'COMPLETED',
                status: 'FAILED',
                timestamp: Date.now(),
                duration: 0,
                error: { name: err.name || 'OrchestrationError', message: err.message || 'Orchestration batch task failure' }
              })
            ],
            attemptedAt: Date.now(),
            completedAt: Date.now(),
            duration: 0
          })
        );
      });
    });

    return Promise.all(promises);
  }

  public getResult(orchestrationId: string): AlertOrchestrationResult | null {
    return this._history.find(r => r.orchestrationId === orchestrationId) || null;
  }

  public getHistory(): ReadonlyArray<AlertOrchestrationResult> {
    return freezeDeepSafe(this._history);
  }

  public getStats() {
    const averageOrchestrationDuration = this._orchestrationsTotal > 0 ? this._totalOrchestrationDuration / this._orchestrationsTotal : 0;
    return {
      orchestrationsTotal: this._orchestrationsTotal,
      orchestrationsSuccessful: this._orchestrationsSuccessful,
      orchestrationsSkipped: this._orchestrationsSkipped,
      orchestrationsDuplicate: this._orchestrationsDuplicate,
      orchestrationsSuppressed: this._orchestrationsSuppressed,
      orchestrationsFailed: this._orchestrationsFailed,
      averageOrchestrationDuration,
      activeOrchestrations: this._inFlight.size
    };
  }

  public clear(): void {
    this._history.length = 0;
    this._inFlight.clear();
    this._orchestrationsTotal = 0;
    this._orchestrationsSuccessful = 0;
    this._orchestrationsSkipped = 0;
    this._orchestrationsDuplicate = 0;
    this._orchestrationsSuppressed = 0;
    this._orchestrationsFailed = 0;
    this._totalOrchestrationDuration = 0;
  }

  private logResult(result: AlertOrchestrationResult): void {
    this._history.push(result);
    if (this._history.length > this._maxHistorySize) {
      this._history.shift();
    }
  }
}
