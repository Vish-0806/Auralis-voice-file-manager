import {
  AlertCertificationStageValue,
  AlertCertificationStageResult,
  AlertCertificationReport
} from '../models/certification';

export interface IAlertCertificationManager {
  certify(): Promise<AlertCertificationReport>;
  certifyStage(stage: AlertCertificationStageValue): Promise<AlertCertificationStageResult>;
  getReport(): AlertCertificationReport | null;
  reset(): void;
}
