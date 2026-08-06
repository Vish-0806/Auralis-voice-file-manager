/**
 * Frontend Provider Implementation (Phase 16.1).
 *
 * Provider owning configuration, capabilities, context, telemetry, and health
 * evaluation snapshots with constructor dependency injection.
 */

import {
  createFrontendCapabilities,
  createFrontendConfiguration,
  createFrontendContext,
  createFrontendDiagnostics,
  createFrontendHealth,
  createFrontendState,
  createFrontendStatistics,
  FrontendCapabilities,
  FrontendConfiguration,
  FrontendContext,
  FrontendDiagnostics,
  FrontendHealth,
  FrontendRuntimeState,
  FrontendState,
  FrontendStatistics,
} from './models';
import { IFrontendProvider } from './interfaces';

export class FrontendProvider implements IFrontendProvider {
  private _status: FrontendRuntimeState = FrontendRuntimeState.UNINITIALIZED;
  private readonly _config: FrontendConfiguration;
  private readonly _capabilities: FrontendCapabilities;
  private readonly _context: FrontendContext;

  private _startTime: Date | null = null;
  private _initializationsCount = 0;
  private _shutdownsCount = 0;
  private _restartsCount = 0;
  private _totalOperationsCount = 0;
  private _failedOperationsCount = 0;
  private _errorCount = 0;
  private _lastError: string | null = null;

  constructor(
    config?: FrontendConfiguration,
    capabilities?: FrontendCapabilities,
    context?: FrontendContext,
  ) {
    this._config = config ?? createFrontendConfiguration();
    this._capabilities = capabilities ?? createFrontendCapabilities();
    this._context = context ?? createFrontendContext();
  }

  public initialize(): FrontendHealth {
    if (
      this._status === FrontendRuntimeState.INITIALIZING ||
      this._status === FrontendRuntimeState.READY ||
      this._status === FrontendRuntimeState.RUNNING
    ) {
      return this.health();
    }

    this._status = FrontendRuntimeState.INITIALIZING;
    this._status = FrontendRuntimeState.READY;
    this._initializationsCount++;
    if (!this._startTime) {
      this._startTime = new Date();
    }
    return this.health();
  }

  public shutdown(): FrontendHealth {
    if (this._status === FrontendRuntimeState.STOPPED) {
      return this.health();
    }

    this._status = FrontendRuntimeState.STOPPING;
    this._status = FrontendRuntimeState.STOPPED;
    this._shutdownsCount++;
    return this.health();
  }

  public restart(): FrontendHealth {
    this.shutdown();
    this.initialize();
    this._restartsCount++;
    return this.health();
  }

  public health(): FrontendHealth {
    const healthy =
      this._status === FrontendRuntimeState.READY || this._status === FrontendRuntimeState.RUNNING;
    return createFrontendHealth({
      healthy,
      status: this._status,
      details: {
        appName: this._config.appName,
        environment: this._config.environment,
        uptimeSeconds: this.calculateUptimeSeconds(),
        errorCount: this._errorCount,
      },
      timestamp: new Date().toISOString(),
    });
  }

  public statistics(): FrontendStatistics {
    return createFrontendStatistics({
      initializations: this._initializationsCount,
      shutdowns: this._shutdownsCount,
      restarts: this._restartsCount,
      totalOperations: this._totalOperationsCount,
      failedOperations: this._failedOperationsCount,
      uptimeSeconds: this.calculateUptimeSeconds(),
    });
  }

  public capabilities(): FrontendCapabilities {
    return this._capabilities;
  }

  public diagnostics(): FrontendDiagnostics {
    return createFrontendDiagnostics({
      state: this.state(),
      health: this.health(),
      statistics: this.statistics(),
      capabilities: this.capabilities(),
      context: this._context,
      timestamp: new Date().toISOString(),
    });
  }

  public status(): FrontendRuntimeState {
    return this._status;
  }

  public state(): FrontendState {
    return createFrontendState({
      status: this._status,
      initialized:
        this._status === FrontendRuntimeState.READY || this._status === FrontendRuntimeState.RUNNING,
      startTime: this._startTime ? this._startTime.toISOString() : null,
      restartCount: this._restartsCount,
      errorCount: this._errorCount,
      lastError: this._lastError,
    });
  }

  public configuration(): FrontendConfiguration {
    return this._config;
  }

  public context(): FrontendContext {
    return this._context;
  }

  private calculateUptimeSeconds(): number {
    if (!this._startTime || this._status === FrontendRuntimeState.STOPPED) {
      return 0;
    }
    const diffMs = Date.now() - this._startTime.getTime();
    return Math.max(0, Math.floor(diffMs / 1000));
  }
}
