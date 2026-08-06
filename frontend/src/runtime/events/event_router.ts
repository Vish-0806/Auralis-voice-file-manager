/**
 * Event Router Engine (Phase 16.4.4).
 *
 * Manages routing rules, topic pattern matching (exact, single-level wildcard '*', multi-level wildcard '**' / '#'),
 * predicate filtering, priority rule ordering, and telemetry reporting.
 */

import {
  createRoutingDecision,
  FrontendEvent,
  RoutingDecision,
  RoutingRule,
} from './models';
import { EventProviderException, EventValidationException } from './exceptions';
import { IEventRouter } from './interfaces';

export class EventRouter implements IEventRouter {
  private readonly _rules = new Map<string, RoutingRule>();

  private _rulesRegistered = 0;
  private _evaluations = 0;
  private _matches = 0;
  private _misses = 0;

  public registerRule(rule: RoutingRule): void {
    if (!rule) {
      throw new EventValidationException('Routing rule cannot be null or undefined.');
    }
    const name = rule.name ? rule.name.trim() : '';
    if (!name) {
      throw new EventValidationException('Routing rule name cannot be empty.');
    }
    const pattern = rule.topicPattern ? rule.topicPattern.trim() : '';
    if (!pattern) {
      throw new EventValidationException('Routing rule topic pattern cannot be empty.');
    }

    if (this._rules.has(rule.ruleId)) {
      throw new EventProviderException(`Routing rule ID '${rule.ruleId}' is already registered.`);
    }

    this._rules.set(rule.ruleId, rule);
    this._rulesRegistered++;
  }

  public removeRule(ruleId: string): boolean {
    const id = ruleId ? ruleId.trim() : '';
    return this._rules.delete(id);
  }

  public getRule(ruleId: string): RoutingRule | undefined {
    return this._rules.get(ruleId.trim());
  }

  public listRules(): ReadonlyArray<RoutingRule> {
    return Object.freeze(Array.from(this._rules.values()));
  }

  public route<T = unknown>(event: FrontendEvent<T>): RoutingDecision {
    this._evaluations++;
    const matchedRules: RoutingRule[] = [];

    for (const rule of this._rules.values()) {
      if (!rule.enabled) continue;

      if (this.matchTopic(rule.topicPattern, event.eventType)) {
        if (!rule.predicate || rule.predicate(event as any)) {
          matchedRules.push(rule);
        }
      }
    }

    // Sort descending by priority
    matchedRules.sort((a, b) => b.priority - a.priority);

    if (matchedRules.length > 0) {
      this._matches++;
    } else {
      this._misses++;
    }

    return createRoutingDecision({
      event: event as any,
      matchedRules: Object.freeze(matchedRules),
      matched: matchedRules.length > 0,
    });
  }

  public clearRules(): void {
    this._rules.clear();
  }

  public telemetry(): {
    rulesRegistered: number;
    evaluations: number;
    matches: number;
    misses: number;
  } {
    return Object.freeze({
      rulesRegistered: this._rulesRegistered,
      evaluations: this._evaluations,
      matches: this._matches,
      misses: this._misses,
    });
  }

  private matchTopic(pattern: string, topic: string): boolean {
    const p = pattern.trim();
    const t = topic.trim();

    if (p === '*' || p === '**' || p === '#' || p === t) {
      return true;
    }

    // Multi-level wildcard handling (e.g. "system.**" or "system.#")
    if (p.endsWith('.**') || p.endsWith('.#')) {
      const prefix = p.substring(0, p.lastIndexOf('.'));
      return t === prefix || t.startsWith(prefix + '.');
    }

    // Single-level wildcard handling (e.g. "user.*")
    const patternParts = p.split('.');
    const topicParts = t.split('.');

    if (patternParts.length !== topicParts.length) {
      return false;
    }

    for (let i = 0; i < patternParts.length; i++) {
      const pPart = patternParts[i];
      const tPart = topicParts[i];

      if (pPart === '*') continue;
      if (pPart !== tPart) return false;
    }

    return true;
  }
}
