# Event Bus Subsystem

## Event-Driven Architecture (EDA)
Auralis uses an Event-Driven Architecture (EDA) to coordinate events and status notifications asynchronously. Instead of tightly coupling sub-systems (for example, having the voice parser directly call the file search engine, or the file system directly updating the UI state), components communicate by publishing and subscribing to standardized event payloads over a central **Event Bus**.

### Benefits of EDA
- **Loose Coupling:** Sub-systems function independently. A publisher does not need to know who is listening to its events or how they are processed.
- **Asynchronous Execution:** Slow operations (such as indexing folders or generating speech summaries) run in the background, preventing system bottlenecks.
- **Scalability:** New features (e.g. custom plugins or notifications) can listen to existing events without changing original code modules.
- **Extensibility:** Facilitates the integration of background processes and multi-step macro automations.

---

## Publish/Subscribe Model
The system uses the publish/subscribe pattern to route events. Components register their interest in specific topics (e.g., `voice.wake_word_detected`) or wildcard scopes (e.g., `voice.*`) with the central Subscription Registry. When an event is published, the Event Bus matches the topic and dispatches the event asynchronously to all matching subscribers.

```mermaid
graph TD
    %% Emitters
    subgraph Emitters [Event Publishers]
        Voice[Voice Engine]
        Brain[AI Brain]
        OSAL[OSAL Adapters]
    end

    %% Bus
    subgraph Broker [Event Bus Broker]
        Bus[Event Bus]
        Reg[Subscription Registry]
        Disp[Asynchronous Dispatcher]
        
        Bus -->|1. Lookup| Reg
        Reg -->|2. Get Subscribers| Disp
    end

    %% Listeners
    subgraph Listeners [Event Subscribers]
        UI[UI Gateway Service]
        Logger[Audit Log Service]
        Auto[Automation Engine]
    end

    %% Flows
    Voice -->|Publish| Bus
    Brain -->|Publish| Bus
    OSAL -->|Publish| Bus
    
    Disp -->|Async Dispatch| UI
    Disp -->|Async Dispatch| Logger
    Disp -->|Async Dispatch| Auto
```

---

## Future Event Lifecycle

The diagram below illustrates the lifecycle of a system event, from the initial trigger to asynchronous delivery:

```mermaid
sequenceDiagram
    autonumber
    participant Pub as Publisher (Voice STT)
    participant Bus as Event Bus Broker
    participant Registry as Subscription Registry
    participant Dispatcher as Dispatcher Queue
    participant Sub1 as Subscriber (UI Gateway)
    participant Sub2 as Subscriber (Automation Manager)

    Pub->>Bus: publish(STT_TRANSCRIBED, payload)
    Note over Bus: EventEnvelope created & correlation ID attached
    
    Bus->>Registry: get_subscribers_for_topic("voice.stt_transcribed")
    Registry-->>Bus: return [UI Gateway, Automation Manager]
    
    Bus->>Dispatcher: dispatch(envelope, subscribers)
    Note over Dispatcher: Enqueued in non-blocking thread queue
    
    par Async Dispatch Worker 1
        Dispatcher->>Sub1: on_event(envelope)
        Note over Sub1: Update UI console
    and Async Dispatch Worker 2
        Dispatcher->>Sub2: on_event(envelope)
        Note over Sub2: Check trigger condition rules
    end
```
