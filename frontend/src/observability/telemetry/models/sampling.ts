export interface SamplingConfig {
  readonly enabled: boolean;
  readonly samplingRate: number;
  readonly keepErrors: boolean;
}
