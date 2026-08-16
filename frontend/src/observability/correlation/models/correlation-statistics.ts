export interface CorrelationStatistics {
  readonly contextsCreated: number;
  readonly eventsRecorded: number;
  readonly linksRecorded: number;
  readonly queriesExecuted: number;
  readonly queryMatches: number;
  readonly invalidContexts: number;
  readonly invalidEvents: number;
  readonly evictedEvents: number;
  readonly evictedLinks: number;
  readonly lifecycleOperations: number;
  readonly lifecycleFailures: number;
}
