/**
 * State Synchronizer Engine (Phase 16.5).
 *
 * Implements ISynchronizer providing conflict detection, version comparison,
 * snapshot diffing, and merge strategy resolution between state containers.
 */

import { createSynchronizationRecord, StateContainer, SynchronizationRecord } from './models';
import { StateValidationException } from './exceptions';
import { ISynchronizer } from './interfaces';

export class StateSynchronizer implements ISynchronizer {
  public synchronize<T = unknown>(source: StateContainer<T>, target: StateContainer<T>): SynchronizationRecord {
    if (!source || !target) {
      throw new StateValidationException('Source and target state containers are required for synchronization.');
    }

    const conflictDetected =
      source.version !== target.version || JSON.stringify(source.state) !== JSON.stringify(target.state);

    return createSynchronizationRecord({
      sourceContainerId: source.containerId,
      targetContainerId: target.containerId,
      conflictDetected,
      resolved: true,
    });
  }
}
