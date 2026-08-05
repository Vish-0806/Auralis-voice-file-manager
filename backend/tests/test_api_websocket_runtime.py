"""Tests for API WebSocket Runtime (Phase 15.7).

Validates immutable models, enums, exception hierarchy, ABC interfaces,
session manager, channel manager, message router, provider lifecycle,
runtime coordinator, lazy singletons, and multithreaded concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from pydantic import ValidationError as PydanticValidationError

from backend.application.api.websocket import (
    BroadcastPlan,
    ChannelException,
    ChannelManager,
    ChannelState,
    ChannelSubscription,
    ConnectionContext,
    ConnectionException,
    ConnectionState,
    IChannelManager,
    IMessageRouter,
    ISessionManager,
    IWebSocketProvider,
    IWebSocketRuntime,
    MessageRouter,
    MessageRoutingException,
    SessionManager,
    SubscriptionException,
    WebSocketCapabilities,
    WebSocketChannel,
    WebSocketConnection,
    WebSocketDiagnostics,
    WebSocketException,
    WebSocketHealth,
    WebSocketMessage,
    WebSocketProvider,
    WebSocketRuntime,
    WebSocketRuntimeState,
    WebSocketSession,
    WebSocketStatistics,
    get_websocket_provider,
    get_websocket_runtime,
    reset_websocket_provider,
    reset_websocket_runtime,
    set_websocket_provider,
    set_websocket_runtime,
)


@pytest.fixture(autouse=True)
def _reset_websocket_singletons():
    """Reset websocket singletons before and after each test."""
    reset_websocket_runtime()
    reset_websocket_provider()
    yield
    reset_websocket_runtime()
    reset_websocket_provider()


# --- Enum Tests ---

def test_enum_connection_state():
    """Verify ConnectionState enum values."""
    assert ConnectionState.CONNECTING.value == "CONNECTING"
    assert ConnectionState.CONNECTED.value == "CONNECTED"
    assert ConnectionState.DISCONNECTED.value == "DISCONNECTED"
    assert ConnectionState.CLOSED.value == "CLOSED"
    assert len(ConnectionState) == 4


def test_enum_channel_state():
    """Verify ChannelState enum values."""
    assert ChannelState.ACTIVE.value == "ACTIVE"
    assert ChannelState.INACTIVE.value == "INACTIVE"
    assert ChannelState.ARCHIVED.value == "ARCHIVED"
    assert len(ChannelState) == 3


def test_enum_websocket_runtime_state():
    """Verify WebSocketRuntimeState enum values."""
    assert WebSocketRuntimeState.UNINITIALIZED.value == "UNINITIALIZED"
    assert WebSocketRuntimeState.INITIALIZING.value == "INITIALIZING"
    assert WebSocketRuntimeState.READY.value == "READY"
    assert WebSocketRuntimeState.STOPPING.value == "STOPPING"
    assert WebSocketRuntimeState.STOPPED.value == "STOPPED"
    assert len(WebSocketRuntimeState) == 5


# --- Model Immutability Tests ---

def test_model_immutability_websocket_connection():
    """Verify WebSocketConnection defaults and immutability."""
    conn = WebSocketConnection(connection_id="c1", session_id="s1")
    assert conn.connection_id == "c1"
    assert conn.state == ConnectionState.CONNECTED

    with pytest.raises((PydanticValidationError, TypeError)):
        conn.state = ConnectionState.CLOSED  # type: ignore[attr-defined]


def test_model_immutability_websocket_session():
    """Verify WebSocketSession defaults and immutability."""
    sess = WebSocketSession(session_id="s1", user_id="u1")
    assert sess.session_id == "s1"
    assert sess.is_active is True

    with pytest.raises((PydanticValidationError, TypeError)):
        sess.is_active = False  # type: ignore[attr-defined]


def test_model_immutability_channel_subscription():
    """Verify ChannelSubscription defaults and immutability."""
    sub = ChannelSubscription(subscription_id="sub1", channel_id="ch1", connection_id="c1")
    assert sub.subscription_id == "sub1"

    with pytest.raises((PydanticValidationError, TypeError)):
        sub.channel_id = "ch2"  # type: ignore[attr-defined]


def test_model_immutability_websocket_channel():
    """Verify WebSocketChannel defaults and immutability."""
    ch = WebSocketChannel(channel_id="ch1", name="General")
    assert ch.channel_id == "ch1"
    assert ch.state == ChannelState.ACTIVE

    with pytest.raises((PydanticValidationError, TypeError)):
        ch.name = "NewName"  # type: ignore[attr-defined]


def test_model_immutability_websocket_message():
    """Verify WebSocketMessage defaults and immutability."""
    msg = WebSocketMessage(message_id="m1", payload={"data": 1})
    assert msg.message_id == "m1"
    assert msg.event_type == "message"

    with pytest.raises((PydanticValidationError, TypeError)):
        msg.event_type = "custom"  # type: ignore[attr-defined]


def test_model_immutability_broadcast_plan():
    """Verify BroadcastPlan defaults and immutability."""
    msg = WebSocketMessage(message_id="m1")
    plan = BroadcastPlan(plan_id="p1", message=msg, target_connection_ids=("c1",), recipient_count=1)
    assert plan.plan_id == "p1"
    assert plan.recipient_count == 1

    with pytest.raises((PydanticValidationError, TypeError)):
        plan.recipient_count = 5  # type: ignore[attr-defined]


def test_model_immutability_connection_context():
    """Verify ConnectionContext defaults and immutability."""
    ctx = ConnectionContext(context_id="ctx1", connection_id="c1", session_id="s1")
    assert ctx.context_id == "ctx1"

    with pytest.raises((PydanticValidationError, TypeError)):
        ctx.context_id = "ctx2"  # type: ignore[attr-defined]


def test_model_immutability_capabilities():
    """Verify WebSocketCapabilities defaults and immutability."""
    caps = WebSocketCapabilities()
    assert caps.supports_sessions is True

    with pytest.raises((PydanticValidationError, TypeError)):
        caps.supports_sessions = False  # type: ignore[attr-defined]


def test_model_immutability_statistics():
    """Verify WebSocketStatistics defaults and immutability."""
    stats = WebSocketStatistics()
    assert stats.total_sessions == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        stats.total_sessions = 5  # type: ignore[attr-defined]


def test_model_immutability_health():
    """Verify WebSocketHealth defaults and immutability."""
    health = WebSocketHealth()
    assert health.is_healthy is True

    with pytest.raises((PydanticValidationError, TypeError)):
        health.is_healthy = False  # type: ignore[attr-defined]


def test_model_immutability_diagnostics():
    """Verify WebSocketDiagnostics defaults and immutability."""
    diag = WebSocketDiagnostics()
    assert diag.active_sessions_count == 0

    with pytest.raises((PydanticValidationError, TypeError)):
        diag.active_sessions_count = 10  # type: ignore[attr-defined]


# --- Exception Hierarchy Tests ---

def test_exception_hierarchy():
    """Verify exception hierarchy inheritance."""
    assert issubclass(ConnectionException, WebSocketException)
    assert issubclass(ChannelException, WebSocketException)
    assert issubclass(SubscriptionException, WebSocketException)
    assert issubclass(MessageRoutingException, WebSocketException)
    assert issubclass(WebSocketException, Exception)


# --- Interface Abstraction Tests ---

def test_interfaces_cannot_be_instantiated():
    """Verify abstract base classes raise TypeError on direct instantiation."""
    with pytest.raises(TypeError):
        ISessionManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IChannelManager()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IMessageRouter()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IWebSocketProvider()  # type: ignore[abstract]

    with pytest.raises(TypeError):
        IWebSocketRuntime()  # type: ignore[abstract]


# --- SessionManager Tests ---

def test_session_manager_create_and_lookup():
    """Verify session creation and lookup."""
    sm = SessionManager()
    session = sm.create_session("s1", user_id="u1")

    assert session.session_id == "s1"
    assert sm.lookup_session("s1") == session
    assert sm.count_sessions() == 1


def test_session_manager_duplicate_session_exception():
    """Verify ConnectionException when creating duplicate session."""
    sm = SessionManager()
    sm.create_session("s1")

    with pytest.raises(ConnectionException):
        sm.create_session("s1")


def test_session_manager_register_connection():
    """Verify registering a connection under a session."""
    sm = SessionManager()
    sm.create_session("s1")

    conn = WebSocketConnection(connection_id="c1", session_id="s1")
    registered = sm.register_connection("s1", conn)

    assert registered.connection_id == "c1"
    assert sm.lookup_connection("c1") == conn
    assert sm.count_connections() == 1

    sess = sm.lookup_session("s1")
    assert sess is not None
    assert len(sess.connections) == 1


def test_session_manager_register_connection_missing_session_exception():
    """Verify ConnectionException when registering under missing session."""
    sm = SessionManager()
    conn = WebSocketConnection(connection_id="c1", session_id="missing")

    with pytest.raises(ConnectionException):
        sm.register_connection("missing", conn)


def test_session_manager_register_duplicate_connection_exception():
    """Verify ConnectionException when registering duplicate connection ID."""
    sm = SessionManager()
    sm.create_session("s1")
    conn1 = WebSocketConnection(connection_id="c1", session_id="s1")
    conn2 = WebSocketConnection(connection_id="c1", session_id="s1")

    sm.register_connection("s1", conn1)
    with pytest.raises(ConnectionException):
        sm.register_connection("s1", conn2)


def test_session_manager_disconnect_connection():
    """Verify marking a connection as DISCONNECTED."""
    sm = SessionManager()
    sm.create_session("s1")
    conn = WebSocketConnection(connection_id="c1", session_id="s1")
    sm.register_connection("s1", conn)

    disconnected = sm.disconnect_connection("c1")
    assert disconnected is not None
    assert disconnected.state == ConnectionState.DISCONNECTED
    assert sm.count_connections() == 0  # ACTIVE count is 0


def test_session_manager_close_session():
    """Verify closing a session and transitioning connections to CLOSED."""
    sm = SessionManager()
    sm.create_session("s1")
    conn = WebSocketConnection(connection_id="c1", session_id="s1")
    sm.register_connection("s1", conn)

    closed_session = sm.close_session("s1")
    assert closed_session is not None
    assert closed_session.is_active is False
    assert closed_session.connections[0].state == ConnectionState.CLOSED


def test_session_manager_list_and_count():
    """Verify list_active_sessions, list_active_connections, and counts."""
    sm = SessionManager()
    sm.create_session("s1")
    sm.create_session("s2")
    sm.register_connection("s1", WebSocketConnection(connection_id="c1", session_id="s1"))

    assert sm.count_sessions() == 2
    assert sm.count_connections() == 1
    assert len(sm.list_active_sessions()) == 2
    assert len(sm.list_active_connections()) == 1


def test_session_manager_clear():
    """Verify clearing session manager."""
    sm = SessionManager()
    sm.create_session("s1")
    sm.clear()

    assert sm.count_sessions() == 0
    assert sm.count_connections() == 0


# --- ChannelManager Tests ---

def test_channel_manager_register_and_lookup():
    """Verify registering and looking up a channel."""
    cm = ChannelManager()
    ch = WebSocketChannel(channel_id="ch1", name="Lobby")
    registered = cm.register_channel(ch)

    assert registered.channel_id == "ch1"
    assert cm.lookup_channel("ch1") == ch
    assert cm.count_channels() == 1


def test_channel_manager_duplicate_channel_exception():
    """Verify ChannelException when registering duplicate channel."""
    cm = ChannelManager()
    ch1 = WebSocketChannel(channel_id="ch1", name="Lobby")
    ch2 = WebSocketChannel(channel_id="ch1", name="Lobby2")

    cm.register_channel(ch1)
    with pytest.raises(ChannelException):
        cm.register_channel(ch2)


def test_channel_manager_subscribe_and_subscribers():
    """Verify subscribing connection to channel and retrieving subscribers."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Lobby"))

    sub = cm.subscribe("ch1", "c1")
    assert sub.channel_id == "ch1"
    assert sub.connection_id == "c1"

    subscribers = cm.get_channel_subscribers("ch1")
    assert subscribers == ("c1",)


def test_channel_manager_subscribe_missing_channel_exception():
    """Verify ChannelException when subscribing to non-existent channel."""
    cm = ChannelManager()
    with pytest.raises(ChannelException):
        cm.subscribe("missing", "c1")


def test_channel_manager_unsubscribe():
    """Verify unsubscribing connection from channel."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Lobby"))
    cm.subscribe("ch1", "c1")

    removed = cm.unsubscribe("ch1", "c1")
    assert removed is not None
    assert removed.connection_id == "c1"
    assert len(cm.get_channel_subscribers("ch1")) == 0


def test_channel_manager_unregister_channel():
    """Verify unregistering a channel."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Lobby"))

    removed = cm.unregister_channel("ch1")
    assert removed is not None
    assert cm.lookup_channel("ch1") is None
    assert cm.count_channels() == 0


def test_channel_manager_list_and_count():
    """Verify list_channels and count_channels."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Ch1"))
    cm.register_channel(WebSocketChannel(channel_id="ch2", name="Ch2"))

    assert cm.count_channels() == 2
    assert len(cm.list_channels()) == 2


def test_channel_manager_clear():
    """Verify clearing channel manager."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Ch1"))
    cm.clear()

    assert cm.count_channels() == 0


# --- MessageRouter Tests ---

def test_message_router_direct_routing():
    """Verify direct message routing to target connection ID."""
    router = MessageRouter()
    msg = WebSocketMessage(message_id="m1", target_connection_id="c1")

    plan = router.route_direct(msg)
    assert plan.recipient_count == 1
    assert plan.target_connection_ids == ("c1",)


def test_message_router_direct_routing_missing_target():
    """Verify direct routing handling missing target_connection_id."""
    router = MessageRouter()
    msg = WebSocketMessage(message_id="m1")

    plan = router.route_direct(msg)
    assert plan.recipient_count == 0
    assert plan.target_connection_ids == ()


def test_message_router_channel_routing():
    """Verify channel broadcast message routing."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch1", name="Lobby"))
    cm.subscribe("ch1", "c1")
    cm.subscribe("ch1", "c2")

    router = MessageRouter(channel_manager=cm)
    msg = WebSocketMessage(message_id="m1", target_channel_id="ch1")

    plan = router.route_channel(msg)
    assert plan.recipient_count == 2
    assert set(plan.target_connection_ids) == {"c1", "c2"}


def test_message_router_channel_routing_missing_channel():
    """Verify channel routing with non-existent channel or no manager."""
    router = MessageRouter()
    msg = WebSocketMessage(message_id="m1", target_channel_id="missing")

    plan = router.route_channel(msg)
    assert plan.recipient_count == 0


def test_message_router_plan_broadcast():
    """Verify explicit broadcast planning."""
    router = MessageRouter()
    msg = WebSocketMessage(message_id="m1")
    plan = router.plan_broadcast(msg, ("c1", "c2", "c3"))

    assert plan.recipient_count == 3
    assert plan.target_connection_ids == ("c1", "c2", "c3")


def test_message_router_count_routed_messages():
    """Verify routed message counter."""
    router = MessageRouter()
    msg = WebSocketMessage(message_id="m1")
    router.route_direct(msg)
    router.plan_broadcast(msg, ("c1",))

    assert router.count_routed_messages() == 2


# --- WebSocketProvider Tests ---

def test_provider_lifecycle():
    """Verify WebSocketProvider initialize and shutdown transitions."""
    provider = WebSocketProvider()
    assert provider.health().state == WebSocketRuntimeState.UNINITIALIZED

    health1 = provider.initialize()
    assert health1.state == WebSocketRuntimeState.READY
    assert health1.is_healthy is True

    health2 = provider.shutdown()
    assert health2.state == WebSocketRuntimeState.STOPPED
    assert health2.is_healthy is False


def test_provider_restart():
    """Verify WebSocketProvider restart cycle."""
    provider = WebSocketProvider()
    provider.initialize()

    health = provider.restart()
    assert health.state == WebSocketRuntimeState.READY
    assert provider.statistics().metrics.get("total_restarts") == 1.0


def test_provider_health_stats_caps_diag():
    """Verify health, statistics, capabilities, and diagnostics from provider."""
    sm = SessionManager()
    sm.create_session("s1")

    provider = WebSocketProvider(session_manager=sm)
    provider.initialize()

    assert provider.health().is_healthy is True
    assert provider.statistics().total_sessions == 1
    assert provider.capabilities().supports_direct_routing is True
    assert provider.diagnostics().active_sessions_count == 1


# --- WebSocketRuntime Tests ---

def test_runtime_lifecycle_delegation():
    """Verify WebSocketRuntime delegates lifecycle calls to provider."""
    runtime = WebSocketRuntime()
    assert runtime.health().state == WebSocketRuntimeState.UNINITIALIZED

    runtime.initialize()
    assert runtime.health().state == WebSocketRuntimeState.READY

    runtime.shutdown()
    assert runtime.health().state == WebSocketRuntimeState.STOPPED


def test_constructor_dependency_injection():
    """Verify Constructor DI in WebSocketProvider and WebSocketRuntime."""
    sm = SessionManager()
    cm = ChannelManager()
    mr = MessageRouter(session_manager=sm, channel_manager=cm)

    provider = WebSocketProvider(
        session_manager=sm,
        channel_manager=cm,
        message_router=mr,
    )
    runtime = WebSocketRuntime(provider=provider)

    assert runtime.get_provider().get_session_manager() is sm
    assert runtime.get_provider().get_channel_manager() is cm
    assert runtime.get_provider().get_message_router() is mr


# --- Lazy Singleton Helper Tests ---

def test_lazy_singleton_websocket_runtime():
    """Verify get_websocket_runtime, set_websocket_runtime, and reset_websocket_runtime."""
    r1 = get_websocket_runtime()
    r2 = get_websocket_runtime()
    assert r1 is r2
    assert isinstance(r1, WebSocketRuntime)

    custom = WebSocketRuntime()
    set_websocket_runtime(custom)
    assert get_websocket_runtime() is custom

    reset_websocket_runtime()
    r3 = get_websocket_runtime()
    assert r3 is not custom


def test_lazy_singleton_websocket_provider():
    """Verify get_websocket_provider, set_websocket_provider, and reset_websocket_provider."""
    p1 = get_websocket_provider()
    p2 = get_websocket_provider()
    assert p1 is p2
    assert isinstance(p1, WebSocketProvider)

    custom = WebSocketProvider()
    set_websocket_provider(custom)
    assert get_websocket_provider() is custom

    reset_websocket_provider()
    p3 = get_websocket_provider()
    assert p3 is not custom


# --- Concurrency Tests ---

def test_concurrent_session_and_connection_management():
    """Verify thread-safety of SessionManager under concurrent session creation and connection registrations."""
    sm = SessionManager()

    def session_worker(idx: int):
        sid = f"s_{idx}"
        cid = f"c_{idx}"
        sm.create_session(sid)
        sm.register_connection(sid, WebSocketConnection(connection_id=cid, session_id=sid))

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(session_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    assert sm.count_sessions() == 40
    assert sm.count_connections() == 40


def test_concurrent_channel_subscriptions():
    """Verify thread-safety of ChannelManager under concurrent subscriptions."""
    cm = ChannelManager()
    cm.register_channel(WebSocketChannel(channel_id="ch_shared", name="Shared"))

    def sub_worker(idx: int):
        cm.subscribe("ch_shared", f"c_{idx}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(sub_worker, i) for i in range(40)]
        for f in futures:
            f.result()

    subscribers = cm.get_channel_subscribers("ch_shared")
    assert len(subscribers) == 40


def test_concurrent_message_routing():
    """Verify thread-safety of MessageRouter under concurrent routing requests."""
    router = MessageRouter()

    def route_worker(idx: int):
        msg = WebSocketMessage(message_id=f"m_{idx}", target_connection_id=f"c_{idx}")
        return router.route_direct(msg).recipient_count == 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(route_worker, i) for i in range(50)]
        results = [f.result() for f in futures]

    assert len(results) == 50
    assert all(results)
    assert router.count_routed_messages() == 50


def test_session_manager_reconnect_or_multiple_connections():
    """Verify registering multiple connections under a single session."""
    sm = SessionManager()
    sm.create_session("s1")
    c1 = WebSocketConnection(connection_id="c1", session_id="s1")
    c2 = WebSocketConnection(connection_id="c2", session_id="s1")

    sm.register_connection("s1", c1)
    sm.register_connection("s1", c2)

    sess = sm.lookup_session("s1")
    assert sess is not None
    assert len(sess.connections) == 2
    assert sm.count_connections() == 2
