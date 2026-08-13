import { DiagnosticCheck } from '../models/check';
import { DiagnosticResult, NormalizedErrorInfo } from '../models/result';
import { DiagnosticStatus, DiagnosticStatusValue } from '../models/diagnostic';
import { DiagnosticTimeoutError } from '../errors/DiagnosticsErrors';
import { createDiagnosticResult } from '../factories/diagnosticsFactories';

export class DiagnosticsExecutor {
  public async execute(check: DiagnosticCheck): Promise<DiagnosticResult> {
    const startTime = Date.now();
    const timestamp = startTime;

    if (!check.enabled) {
      return createDiagnosticResult({
        checkId: check.id,
        sourceId: check.sourceId,
        status: DiagnosticStatus.DISABLED,
        severity: check.severity,
        message: `Diagnostic check '${check.id}' is disabled.`,
        duration: 0,
        timestamp,
        metadata: {}
      });
    }

    let status: DiagnosticStatusValue = DiagnosticStatus.HEALTHY;
    let message = `Diagnostic check '${check.id}' executed successfully.`;
    let errorInfo: NormalizedErrorInfo | undefined = undefined;
    let timerId: any = null;

    try {
      const timeoutMs = check.timeout;
      const executePromise = (async () => {
        const res = await check.execute();
        return res;
      })();

      let resultValue: any;
      if (timeoutMs !== undefined && timeoutMs > 0) {
        const timeoutPromise = new Promise<never>((_, reject) => {
          timerId = setTimeout(() => {
            reject(new DiagnosticTimeoutError(`Diagnostic check execution timed out after ${timeoutMs}ms.`));
          }, timeoutMs);
        });

        try {
          resultValue = await Promise.race([executePromise, timeoutPromise]);
        } finally {
          if (timerId) {
            clearTimeout(timerId);
          }
        }
      } else {
        resultValue = await executePromise;
      }

      // If the callback returns a status, use it
      if (typeof resultValue === 'string' && Object.values(DiagnosticStatus).includes(resultValue as any)) {
        status = resultValue as DiagnosticStatusValue;
      } else {
        status = DiagnosticStatus.HEALTHY;
      }
    } catch (err: any) {
      const isTimeout = err instanceof DiagnosticTimeoutError;
      
      // Determine status from the error status property if available
      if (err && typeof err === 'object' && 'status' in err && Object.values(DiagnosticStatus).includes(err.status)) {
        status = err.status;
      } else {
        status = DiagnosticStatus.UNHEALTHY;
      }

      const errorObj = err instanceof Error ? err : new Error(String(err));
      errorInfo = {
        name: errorObj.name || (isTimeout ? 'DiagnosticTimeoutError' : 'Error'),
        message: errorObj.message || String(err),
        stack: errorObj.stack
      };

      message = errorObj.message || String(err);
    }

    const endTime = Date.now();
    const duration = endTime - startTime;

    return createDiagnosticResult({
      checkId: check.id,
      sourceId: check.sourceId,
      status,
      severity: check.severity,
      message,
      duration,
      timestamp,
      metadata: {},
      error: errorInfo
    });
  }
}
