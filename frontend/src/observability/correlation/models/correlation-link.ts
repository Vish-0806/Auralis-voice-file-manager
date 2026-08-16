export const CorrelationLinkKind = {
  EVENT_TO_EVENT: 'EVENT_TO_EVENT',
  EVENT_TO_TRACE: 'EVENT_TO_TRACE',
  EVENT_TO_SPAN: 'EVENT_TO_SPAN',
  EVENT_TO_ALERT: 'EVENT_TO_ALERT',
  EVENT_TO_REQUEST: 'EVENT_TO_REQUEST',
  EVENT_TO_OPERATION: 'EVENT_TO_OPERATION'
} as const;

export type CorrelationLinkKindValue = typeof CorrelationLinkKind[keyof typeof CorrelationLinkKind];

export interface CorrelationLink {
  readonly sourceId: string;
  readonly targetId: string;
  readonly kind: CorrelationLinkKindValue;
  readonly metadata?: Record<string, unknown>;
}
