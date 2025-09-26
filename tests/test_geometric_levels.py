"""Tests for geometric grid level generation."""

import math

from bot_ia_grid import GridBot


def test_geometric_progression_structure() -> None:
    bot = GridBot(
        base_price=25000.0,
        levels=4,
        ratio=1.03,
        quantity_per_order=0.05,
        base_balance=2.0,
        quote_balance=50000.0,
        fee_rate=0.0005,
        slippage=0.001,
    )

    buy_prices = [order.price for order in bot.iter_orders("buy")]
    sell_prices = [order.price for order in bot.iter_orders("sell")]

    assert buy_prices == sorted(buy_prices, reverse=True)
    assert sell_prices == sorted(sell_prices)

    for previous, current in zip(buy_prices, buy_prices[1:]):
        ratio = previous / current
        assert math.isclose(ratio, bot.ratio, rel_tol=1e-9)

    for previous, current in zip(sell_prices, sell_prices[1:]):
        ratio = current / previous
        assert math.isclose(ratio, bot.ratio, rel_tol=1e-9)

    assert buy_prices[-1] < bot.base_price < sell_prices[0]


def test_geometric_levels_remain_constant_after_processing(grid_bot_liquid) -> None:
    initial_buy_prices = [order.price for order in grid_bot_liquid.iter_orders("buy")]

    grid_bot_liquid.process_price(90.0)
    grid_bot_liquid.process_price(120.0)

    post_buy_prices = [order.price for order in grid_bot_liquid.iter_orders("buy")]

    assert initial_buy_prices == post_buy_prices

