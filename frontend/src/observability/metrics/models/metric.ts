export const MetricType = {
  COUNTER: 'COUNTER',
  GAUGE: 'GAUGE',
  HISTOGRAM: 'HISTOGRAM',
  TIMER: 'TIMER'
} as const;

export type MetricTypeValue = typeof MetricType[keyof typeof MetricType];

export interface MetricDefinition {
  readonly name: string;
  readonly type: MetricTypeValue;
  readonly description?: string;
  readonly unit?: string;
  readonly labelKeys: ReadonlyArray<string>;
  readonly enabled: boolean;
}
