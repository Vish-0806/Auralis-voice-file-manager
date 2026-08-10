import type {
  PluginCertificationReport,
  PluginCertificationStatistics,
  PluginCertificationHealth,
  PluginCertificationDiagnostics,
  PluginCertificationResult
} from '../models/certification';

export interface IPluginCertificationManager {
  certify(): Promise<PluginCertificationReport>;
  certifyPlugin(pluginId: string): Promise<PluginCertificationResult>;
  certifyAll(): Promise<ReadonlyArray<PluginCertificationResult>>;
  getLastReport(): PluginCertificationReport | null;
  getStatistics(): PluginCertificationStatistics;
  getHealth(): PluginCertificationHealth;
  getDiagnostics(): PluginCertificationDiagnostics;
  reset(): void;
}
