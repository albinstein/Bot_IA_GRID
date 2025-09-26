"""Spot trading behaviour tests ensuring balances remain non-negative."""

import pytest

from bot_ia_grid import InsufficientBalanceError


def test_balances_never_negative(grid_bot_liquid, price_series_up_down) -> None:
    for price in price_series_up_down:
        grid_bot_liquid.process_price(price)
        assert grid_bot_liquid.base_balance >= 0
        assert grid_bot_liquid.quote_balance >= 0

    assert grid_bot_liquid.trade_history, "No trades were executed in the scenario"


def test_execute_buy_requires_quote_balance(grid_bot_low_quote) -> None:
    buy_order = next(order for order in grid_bot_low_quote.iter_orders("buy"))

    with pytest.raises(InsufficientBalanceError):
        grid_bot_low_quote.process_price(buy_order.price)

    assert not grid_bot_low_quote.trade_history


def test_execute_sell_requires_base_balance(grid_bot_low_base) -> None:
    sell_order = next(order for order in grid_bot_low_base.iter_orders("sell"))

    with pytest.raises(InsufficientBalanceError):
        grid_bot_low_base.process_price(sell_order.price)

    assert not grid_bot_low_base.trade_history


def test_process_price_rejects_invalid_tick(grid_bot_liquid) -> None:
    with pytest.raises(ValueError):
        grid_bot_liquid.process_price(0)

