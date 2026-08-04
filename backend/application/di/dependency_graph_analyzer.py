"""Dependency Graph Analyzer & Production Certification Engine (Phase 14.2.5).

Builds Directed Acyclic Graph (DAG) representations of registered services, inspects constructor
dependencies, detects circular dependency loops, missing dependencies, orphan services,
and invalid lifetime capture chains (e.g. Singleton depending on Scoped).
Supports Mermaid, DOT, Adjacency List, and Adjacency Map export formats, and produces
enterprise DependencyCertification reports.
"""

from datetime import datetime, timezone
import inspect
import json
import logging
from threading import RLock
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_args, get_origin

from backend.application.di.interfaces import IServiceCollection
from backend.application.di.models import (
    DependencyAnalysis,
    DependencyCertification,
    DependencyEdge,
    DependencyGraph,
    DependencyIssue,
    DependencyNode,
    GraphStatistics,
    ServiceLifetime,
)

logger = logging.getLogger(__name__)


class DependencyGraphAnalyzer:
    """Production dependency graph analysis and certification engine."""

    def __init__(self) -> None:
        """Initialize DependencyGraphAnalyzer with thread safety lock."""
        self._lock = RLock()

    def _type_name(self, target_type: Any) -> str:
        """Get string representation of a type or alias."""
        if isinstance(target_type, str):
            return target_type
        if hasattr(target_type, "__name__"):
            return target_type.__name__
        return str(target_type)

    def _unwrap_type(self, annotation: Any) -> Tuple[Any, bool]:
        """Unwrap Optional[T] or Union[T, None] annotations."""
        origin = get_origin(annotation)
        if origin is Union:
            args = get_args(annotation)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1:
                return non_none_args[0], True
        return annotation, False

    def build_graph(self, services: IServiceCollection) -> DependencyGraph:
        """Build a complete DependencyGraph by reflecting constructor parameter signatures.

        Args:
            services: Target ServiceCollection containing registered descriptors.

        Returns:
            DependencyGraph: Complete immutable graph model.
        """
        with self._lock:
            nodes_map: Dict[str, DependencyNode] = {}
            edges_list: List[DependencyEdge] = []
            descriptors = services.get_descriptors()

            # Map registered descriptor service names
            descriptor_map: Dict[str, Any] = {}
            for desc in descriptors:
                name = self._type_name(desc.service_type)
                descriptor_map[name] = desc

            # Step 1: Create Nodes
            dep_counts: Dict[str, int] = {self._type_name(d.service_type): 0 for d in descriptors}
            rev_counts: Dict[str, int] = {self._type_name(d.service_type): 0 for d in descriptors}

            # Step 2: Traverse Dependencies and create Edges
            for desc in descriptors:
                source_name = self._type_name(desc.service_type)
                impl_type = desc.implementation_type or desc.service_type

                if isinstance(impl_type, type) and desc.factory is None and desc.instance is None:
                    init_method = getattr(impl_type, "__init__", None)
                    if init_method is not None and init_method is not object.__init__:
                        try:
                            sig = inspect.signature(init_method)
                            params = [
                                p for name, p in sig.parameters.items()
                                if name != "self" and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                            ]

                            for param in params:
                                param_type, _ = self._unwrap_type(param.annotation)
                                target_name = self._type_name(param_type)

                                # Match target in registered descriptors or aliases
                                matched_target = None
                                if target_name in descriptor_map:
                                    matched_target = target_name
                                else:
                                    # Check by alias
                                    target_desc = services.get_descriptor_by_alias(target_name)
                                    if target_desc:
                                        matched_target = self._type_name(target_desc.service_type)

                                if matched_target:
                                    edges_list.append(
                                        DependencyEdge(
                                            source_id=source_name,
                                            target_id=matched_target,
                                            dependency_type="CONSTRUCTOR",
                                        )
                                    )
                                    dep_counts[source_name] = dep_counts.get(source_name, 0) + 1
                                    rev_counts[matched_target] = rev_counts.get(matched_target, 0) + 1
                        except Exception as exc:
                            logger.warning("Could not reflect signature for '%s': %s", source_name, exc)

            # Build Node objects
            for desc in descriptors:
                s_name = self._type_name(desc.service_type)
                impl_name = self._type_name(desc.implementation_type) if desc.implementation_type else None
                nodes_map[s_name] = DependencyNode(
                    node_id=s_name,
                    service_type=s_name,
                    implementation_type=impl_name,
                    aliases=desc.aliases,
                    tags=desc.tags,
                    lifetime=desc.lifetime,
                    dependency_count=dep_counts.get(s_name, 0),
                    reverse_dependency_count=rev_counts.get(s_name, 0),
                )

            return DependencyGraph(
                nodes=tuple(nodes_map.values()),
                edges=tuple(edges_list),
                created_at=datetime.now(timezone.utc),
            )

    def validate_graph(self, services: IServiceCollection, graph: DependencyGraph) -> Tuple[DependencyIssue, ...]:
        """Validate dependency graph for missing dependencies, cycles, lifetime violations, and orphans.

        Args:
            services: ServiceCollection container.
            graph: DependencyGraph to analyze.

        Returns:
            Tuple[DependencyIssue, ...]: Identified validation issues.
        """
        with self._lock:
            issues: List[DependencyIssue] = []
            descriptors = services.get_descriptors()
            node_map = {node.node_id: node for node in graph.nodes}

            # 1. Missing Dependency & Alias Conflict Checks
            alias_to_service: Dict[str, str] = {}
            for desc in descriptors:
                s_name = self._type_name(desc.service_type)
                for alias in desc.aliases:
                    if alias in alias_to_service and alias_to_service[alias] != s_name:
                        issues.append(
                            DependencyIssue(
                                issue_id=f"dup_alias_{alias}",
                                issue_type="DUPLICATE_ALIAS",
                                severity="ERROR",
                                message=f"Duplicate alias '{alias}' registered for '{alias_to_service[alias]}' and '{s_name}'.",
                                affected_services=(alias_to_service[alias], s_name),
                            )
                        )
                    else:
                        alias_to_service[alias] = s_name

                # Check constructor parameters for missing dependencies
                impl_type = desc.implementation_type or desc.service_type
                if isinstance(impl_type, type) and desc.factory is None and desc.instance is None:
                    init_method = getattr(impl_type, "__init__", None)
                    if init_method is not None and init_method is not object.__init__:
                        try:
                            sig = inspect.signature(init_method)
                            params = [
                                p for name, p in sig.parameters.items()
                                if name != "self" and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                            ]
                            for param in params:
                                param_type, is_optional = self._unwrap_type(param.annotation)
                                target_name = self._type_name(param_type)

                                is_registered = services.contains(param_type) or services.contains_alias(target_name)
                                has_default = param.default is not inspect.Parameter.empty

                                if not is_registered and not is_optional and not has_default and target_name != "inspect._empty":
                                    issues.append(
                                        DependencyIssue(
                                            issue_id=f"missing_dep_{s_name}_{param.name}",
                                            issue_type="MISSING_DEPENDENCY",
                                            severity="ERROR",
                                            message=f"Service '{s_name}' requires unregistered parameter '{param.name}' of type '{target_name}'.",
                                            affected_services=(s_name, target_name),
                                        )
                                    )
                        except Exception:
                            pass

            # 2. Lifetime Capture Violations (Singleton depending on Scoped)
            for edge in graph.edges:
                source_node = node_map.get(edge.source_id)
                target_node = node_map.get(edge.target_id)
                if source_node and target_node:
                    if (
                        source_node.lifetime == ServiceLifetime.SINGLETON
                        and target_node.lifetime == ServiceLifetime.SCOPED
                    ):
                        issues.append(
                            DependencyIssue(
                                issue_id=f"lifetime_violation_{edge.source_id}_{edge.target_id}",
                                issue_type="LIFETIME_VIOLATION",
                                severity="ERROR",
                                message=f"Singleton service '{edge.source_id}' cannot depend on Scoped service '{edge.target_id}' (Lifetime Capture).",
                                affected_services=(edge.source_id, edge.target_id),
                            )
                        )

            # 3. Cycle Detection via DFS
            adj: Dict[str, List[str]] = {node.node_id: [] for node in graph.nodes}
            for edge in graph.edges:
                adj[edge.source_id].append(edge.target_id)

            visited: Set[str] = set()
            rec_stack: Set[str] = set()
            cycle_path: List[str] = []

            def dfs(node_id: str, path: List[str]) -> bool:
                visited.add(node_id)
                rec_stack.add(node_id)
                path.append(node_id)

                for neighbor in adj.get(node_id, []):
                    if neighbor not in visited:
                        if dfs(neighbor, path):
                            return True
                    elif neighbor in rec_stack:
                        cycle_start_idx = path.index(neighbor)
                        cycle_path.extend(path[cycle_start_idx:] + [neighbor])
                        return True

                rec_stack.remove(node_id)
                path.pop()
                return False

            for node in graph.nodes:
                if node.node_id not in visited:
                    if dfs(node.node_id, []):
                        chain_str = " -> ".join(cycle_path)
                        issues.append(
                            DependencyIssue(
                                issue_id=f"cycle_{'_'.join(cycle_path)}",
                                issue_type="CIRCULAR_DEPENDENCY",
                                severity="ERROR",
                                message=f"Circular dependency loop detected: {chain_str}",
                                affected_services=tuple(set(cycle_path)),
                            )
                        )
                        break

            # 4. Orphan Detection (Standalone service with 0 dependencies and 0 reverse dependencies)
            if len(graph.nodes) > 1:
                for node in graph.nodes:
                    if node.dependency_count == 0 and node.reverse_dependency_count == 0:
                        issues.append(
                            DependencyIssue(
                                issue_id=f"orphan_{node.node_id}",
                                issue_type="ORPHAN_SERVICE",
                                severity="WARNING",
                                message=f"Service '{node.node_id}' is isolated with zero dependencies and zero reverse references.",
                                affected_services=(node.node_id,),
                            )
                        )

            return tuple(issues)

    def calculate_statistics(self, graph: DependencyGraph, issues: Tuple[DependencyIssue, ...]) -> GraphStatistics:
        """Calculate quantitative statistics from dependency graph and issues.

        Args:
            graph: DependencyGraph instance.
            issues: Identified DependencyIssue items.

        Returns:
            GraphStatistics: Graph metrics summary model.
        """
        with self._lock:
            total_nodes = len(graph.nodes)
            total_edges = len(graph.edges)

            root_nodes = [n for n in graph.nodes if n.reverse_dependency_count == 0]
            leaf_nodes = [n for n in graph.nodes if n.dependency_count == 0]
            orphan_nodes = [n for n in graph.nodes if n.dependency_count == 0 and n.reverse_dependency_count == 0]

            cycle_issues = [i for i in issues if i.issue_type == "CIRCULAR_DEPENDENCY"]

            # Compute depth using BFS/DFS from root nodes
            adj: Dict[str, List[str]] = {node.node_id: [] for node in graph.nodes}
            for edge in graph.edges:
                adj[edge.source_id].append(edge.target_id)

            depths: Dict[str, int] = {}

            def get_depth(node_id: str, visited: Set[str]) -> int:
                if node_id in depths:
                    return depths[node_id]
                if node_id in visited:
                    return 0
                visited.add(node_id)
                max_sub = 0
                for nxt in adj.get(node_id, []):
                    max_sub = max(max_sub, 1 + get_depth(nxt, visited.copy()))
                depths[node_id] = max_sub
                return max_sub

            for node in graph.nodes:
                get_depth(node.node_id, set())

            max_depth = max(depths.values()) if depths else 0
            avg_depth = sum(depths.values()) / total_nodes if total_nodes > 0 else 0.0

            return GraphStatistics(
                total_nodes=total_nodes,
                total_edges=total_edges,
                root_services_count=len(root_nodes),
                leaf_services_count=len(leaf_nodes),
                average_dependency_depth=round(avg_depth, 2),
                maximum_dependency_depth=max_depth,
                connected_components=len(root_nodes) if root_nodes else 1,
                cycle_count=len(cycle_issues),
                orphan_count=len(orphan_nodes),
                unreachable_count=0,
            )

    def analyze_graph(self, services: IServiceCollection) -> DependencyAnalysis:
        """Perform complete dependency graph analysis.

        Args:
            services: Target ServiceCollection instance.

        Returns:
            DependencyAnalysis: Complete graph analysis model.
        """
        with self._lock:
            graph = self.build_graph(services)
            issues = self.validate_graph(services, graph)
            stats = self.calculate_statistics(graph, issues)

            return DependencyAnalysis(
                graph=graph,
                issues=issues,
                statistics=stats,
                analyzed_at=datetime.now(timezone.utc),
            )

    def certify(self, services: IServiceCollection) -> DependencyCertification:
        """Certify container dependency structure for production deployment.

        Args:
            services: Target ServiceCollection instance.

        Returns:
            DependencyCertification: Enterprise certification report.
        """
        with self._lock:
            analysis = self.analyze_graph(services)
            errors = tuple(i.message for i in analysis.issues if i.severity == "ERROR")
            warnings = tuple(i.message for i in analysis.issues if i.severity == "WARNING")

            healthy = len(errors) == 0
            production_ready = len(errors) == 0
            summary = (
                "Certified Production Ready"
                if production_ready
                else f"Certification Failed: {len(errors)} error(s) identified."
            )

            return DependencyCertification(
                healthy=healthy,
                production_ready=production_ready,
                warnings=warnings,
                errors=errors,
                statistics=analysis.statistics,
                analysis_summary=summary,
                certified_at=datetime.now(timezone.utc),
            )

    def export_graph(self, graph: DependencyGraph, format_type: str = "mermaid") -> str:
        """Export dependency graph in specified representation format.

        Args:
            graph: DependencyGraph model.
            format_type: Output format string ("mermaid", "dot", "adjacency_list", "adjacency_map").

        Returns:
            str: Formatted graph representation string.
        """
        with self._lock:
            fmt = format_type.lower().strip()

            if fmt == "mermaid":
                lines = ["graph TD"]
                for node in graph.nodes:
                    lines.append(f'    {node.node_id}["{node.node_id} ({node.lifetime.value})"]')
                for edge in graph.edges:
                    lines.append(f"    {edge.source_id} --> {edge.target_id}")
                return "\n".join(lines)

            elif fmt == "dot":
                lines = ["digraph G {"]
                for node in graph.nodes:
                    lines.append(f'    "{node.node_id}" [label="{node.node_id} ({node.lifetime.value})"];')
                for edge in graph.edges:
                    lines.append(f'    "{edge.source_id}" -> "{edge.target_id}";')
                lines.append("}")
                return "\n".join(lines)

            elif fmt == "adjacency_list":
                adj_list = [[edge.source_id, edge.target_id] for edge in graph.edges]
                return json.dumps(adj_list, indent=2)

            elif fmt == "adjacency_map":
                adj_map: Dict[str, List[str]] = {node.node_id: [] for node in graph.nodes}
                for edge in graph.edges:
                    adj_map[edge.source_id].append(edge.target_id)
                return json.dumps(adj_map, indent=2)

            else:
                raise ValueError(
                    f"Unsupported export format '{format_type}'. Supported formats: mermaid, dot, adjacency_list, adjacency_map."
                )
