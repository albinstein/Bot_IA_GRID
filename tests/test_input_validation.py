"""Input validation tests for the GridBot."""

import pytest

from bot_ia_grid import GridBot


@pytest.mark.parametrize(
    "base_price, levels, ratio, quantity, base_balance, quote_balance, fee_rate, slippage, error_message",
    [
        (0, 1, 1.02, 0.1, 1, 100, 0.001, 0.0, "base_price"),
        (100, 0, 1.02, 0.1, 1, 100, 0.001, 0.0, "levels"),
        (100, 1, 1.0, 0.1, 1, 100, 0.001, 0.0, "ratio"),
        (100, 1, 1.02, 0.0, 1, 100, 0.001, 0.0, "quantity_per_order"),
        (100, 1, 1.02, 0.1, -1, 100, 0.001, 0.0, "base_balance"),
        (100, 1, 1.02, 0.1, 1, -10, 0.001, 0.0, "quote_balance"),
        (100, 1, 1.02, 0.1, 1, 100, -0.001, 0.0, "fee_rate"),
        (100, 1, 1.02, 0.1, 1, 100, 0.001, -0.1, "slippage"),
    ],
)
def test_constructor_validates_inputs(
    base_price,
    levels,
    ratio,
    quantity,
    base_balance,
    quote_balance,
    fee_rate,
    slippage,
    error_message,
) -> None:
    with pytest.raises(ValueError) as exc:
        GridBot(
            base_price=base_price,
            levels=levels,
            ratio=ratio,
            quantity_per_order=quantity,
            base_balance=base_balance,
            quote_balance=quote_balance,
            fee_rate=fee_rate,
            slippage=slippage,
        )

    assert error_message in str(exc.value)


def test_reset_clears_trade_history(grid_bot_liquid, price_series_up_down) -> None:
    for price in price_series_up_down:
        grid_bot_liquid.process_price(price)

    assert grid_bot_liquid.trade_history
    assert any(order.executed for order in grid_bot_liquid.orders)

    grid_bot_liquid.reset()

    assert not grid_bot_liquid.trade_history
    assert all(not order.executed for order in grid_bot_liquid.orders)

