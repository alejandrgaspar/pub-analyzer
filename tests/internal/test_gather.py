"""Test the bounded concurrency helper from pub_analyzer/internal/report/builder.py."""

import asyncio

import pytest

from pub_analyzer.internal.report import builder


@pytest.mark.asyncio
async def test_gather_bounded_keeps_input_order() -> None:
    """Results follow the order the coroutines were given, not the order they finish."""

    async def produce(value: int, delay: float) -> int:
        await asyncio.sleep(delay)
        return value

    # The first coroutine is the slowest, so completion order is the reverse of input order.
    coroutines = [produce(value, delay=(3 - value) / 100) for value in range(4)]

    assert await builder._gather_bounded(coroutines) == [0, 1, 2, 3]


@pytest.mark.asyncio
async def test_gather_bounded_respects_the_limit() -> None:
    """No more than `limit` coroutines run at the same time."""
    running = 0
    high_water_mark = 0

    async def track() -> None:
        nonlocal running, high_water_mark
        running += 1
        high_water_mark = max(high_water_mark, running)
        await asyncio.sleep(0.01)
        running -= 1

    await builder._gather_bounded((track() for _ in range(20)), limit=3)

    assert high_water_mark == 3


@pytest.mark.asyncio
async def test_gather_bounded_raises_the_failure() -> None:
    """A failing coroutine surfaces its exception."""

    async def fail() -> None:
        raise ValueError("boom")

    async def succeed() -> None:
        return None

    with pytest.raises(ValueError, match="boom"):
        await builder._gather_bounded([succeed(), fail(), succeed()])


@pytest.mark.asyncio
async def test_gather_bounded_lets_everything_settle_before_raising() -> None:
    """Nothing is left running after a failure, so the client can close safely."""
    finished: list[int] = []

    async def fail_fast() -> None:
        raise ValueError("boom")

    async def finish_slowly(value: int) -> None:
        await asyncio.sleep(0.02)
        finished.append(value)

    with pytest.raises(ValueError):
        await builder._gather_bounded([fail_fast(), finish_slowly(1), finish_slowly(2)])

    assert sorted(finished) == [1, 2], "the slower coroutines should have been awaited"


@pytest.mark.asyncio
async def test_gather_bounded_with_nothing_to_do() -> None:
    """No coroutines, no results."""
    assert await builder._gather_bounded([]) == []
