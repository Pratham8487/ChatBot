"""
Minimal, safe implementation of the small `langgraph` API surface
expected by the project. This is intentionally lightweight: it stores nodes
and edges so other modules can construct graphs, and exposes a `compile()`
that returns a compiled graph object (here, the StateGraph itself). It is
designed to be non-invasive and compatible with the project's existing
usage in `conversation_graph.py`.
"""
from typing import Any, Callable, Dict, List, Tuple


# Sentinel used to mark an end/terminal target
class _EndSentinel:
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "END"


END = _EndSentinel()


class StateGraph:
    def __init__(self, state_cls: Any):
        self.state_cls = state_cls
        self._nodes: Dict[str, Callable] = {}
        self._entry: str | None = None
        self._edges: Dict[str, List[Any]] = {}
        self._conditional: Dict[str, Tuple[Callable[[Any], str], Dict[str, Any]]] = {}

    def add_node(self, name: str, handler: Callable) -> None:
        self._nodes[name] = handler

    def set_entry_point(self, name: str) -> None:
        self._entry = name

    def add_edge(self, src: str, dst: Any) -> None:
        self._edges.setdefault(src, []).append(dst)

    def add_conditional_edges(self, src: str, router: Callable[[Any], str], mapping: Dict[str, Any]) -> None:
        self._conditional[src] = (router, mapping)

    def compile(self) -> "StateGraph":
        # In the original library this likely builds an optimized runtime
        # structure. For our purposes returning self with stored metadata is
        # sufficient and minimally invasive.
        return self

    # Simple helpers to inspect the compiled graph in tests or runtime
    def nodes(self) -> Dict[str, Callable]:
        return dict(self._nodes)

    def entry_point(self) -> str | None:
        return self._entry

    def edges(self) -> Dict[str, List[Any]]:
        return {k: list(v) for k, v in self._edges.items()}

    def conditional_edges(self) -> Dict[str, Tuple[Callable[[Any], str], Dict[str, Any]]]:
        return dict(self._conditional)
