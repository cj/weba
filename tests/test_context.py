from __future__ import annotations

import asyncio

import pytest

from weba import Component
from weba.context import Context


def test_context_creation():
    """Test that context is created and cached properly."""
    ctx = Context()
    assert ctx.context is ctx  # Should return self
    assert ctx.context is ctx.context  # Should be cached


class AppContext(Context):
    _msg: str = ""

    @property
    def msg(self) -> str:
        """returns msg"""
        return self.context._msg

    @msg.setter
    def msg(self, value: str):
        self.context._msg = value


class ContextComponent(Component, AppContext):
    html = "<h1>ContextComponent</h1>"

    def render(self):
        self.string = self.msg


@pytest.mark.asyncio
async def test_nested_setting_values_on_context():
    msg = "Hello, World!"

    async with AppContext() as ctx:
        ctx.msg = msg

        with ContextComponent() as html:
            assert msg in str(html)


@pytest.mark.asyncio
async def test_context_isolation():
    """Test that context doesn't leak between different async tasks"""

    async def task1():
        async with AppContext() as ctx:
            ctx.msg = "Task 1"

            await asyncio.sleep(0.1)  # Simulate some async work
            assert ctx.msg == "Task 1"

            return ctx.msg

    async def task2():
        async with AppContext() as ctx:
            ctx.msg = "Task 2"

            await asyncio.sleep(0.05)  # Different timing to interleave
            assert ctx.msg == "Task 2"
            return ctx.msg

    # Run both tasks concurrently
    results = await asyncio.gather(task1(), task2())

    assert results == ["Task 1", "Task 2"]
