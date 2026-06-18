"""子 Agent 嵌套深度 — 通过 ContextVar 在委派调用链中传递。"""

from __future__ import annotations

from contextvars import ContextVar, Token

_subagent_depth: ContextVar[int] = ContextVar("subagent_depth", default=0)


def get_subagent_depth() -> int:
    return _subagent_depth.get()


class subagent_depth_scope:
    """进入子 Agent 图执行时 depth + 1。"""

    def __enter__(self) -> subagent_depth_scope:
        self._token: Token = _subagent_depth.set(_subagent_depth.get() + 1)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        _subagent_depth.reset(self._token)
