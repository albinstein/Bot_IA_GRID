"""Pytest fixtures for grid bot testing."""

from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bot_ia_grid import GridBot


@pytest.fixture
def grid_bot_liquid() -> GridBot:
    """Bot with enough balances to cover both buy and sell operations."""

    return GridBot(
        base_price=100.0,
        levels=3,
        ratio=1.05,
        quantity_per_order=0.2,
        base_balance=1.5,
        quote_balance=2000.0,
        fee_rate=0.001,
        slippage=0.002,
    )


@pytest.fixture
def price_series_up_down() -> list[float]:
    """Synthetic series with alternating dips and spikes."""

    return [102.0, 96.0, 107.0, 93.0, 111.0]


@pytest.fixture
def grid_bot_low_quote() -> GridBot:
    """Bot that cannot execute buy orders due to lack of quote balance."""

    return GridBot(
        base_price=100.0,
        levels=1,
        ratio=1.04,
        quantity_per_order=0.5,
        base_balance=0.5,
        quote_balance=10.0,
        fee_rate=0.001,
        slippage=0.001,
    )


@pytest.fixture
def grid_bot_low_base() -> GridBot:
    """Bot that cannot execute sell orders due to lack of base balance."""

    return GridBot(
        base_price=100.0,
        levels=1,
        ratio=1.04,
        quantity_per_order=1.0,
        base_balance=0.2,
        quote_balance=500.0,
        fee_rate=0.001,
        slippage=0.001,
    )

