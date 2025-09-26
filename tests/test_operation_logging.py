"""Operation logging validations for the grid bot."""

from bot_ia_grid import GridBot


def test_trade_history_records_side_price_and_slippage(grid_bot_liquid, price_series_up_down) -> None:
    for price in price_series_up_down:
        grid_bot_liquid.process_price(price)

    trades = grid_bot_liquid.trade_history
    assert trades, "Expected at least one trade to be recorded"

    for trade in trades:
        assert trade.side in {"buy", "sell"}
        assert trade.quantity == grid_bot_liquid.quantity_per_order
        assert trade.fee_paid >= 0
        assert trade.executed_price > 0
        assert trade.slippage >= 0


def test_trade_history_preserves_execution_sequence(grid_bot_liquid) -> None:
    first_leg_price = next(order.price for order in grid_bot_liquid.iter_orders("buy"))
    second_leg_price = next(order.price for order in grid_bot_liquid.iter_orders("sell"))

    grid_bot_liquid.process_price(first_leg_price * 0.999)
    grid_bot_liquid.process_price(second_leg_price * 1.001)

    assert [trade.side for trade in grid_bot_liquid.trade_history] == ["buy", "sell"]

