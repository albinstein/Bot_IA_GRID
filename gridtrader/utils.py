"""Utility helpers for the geometric spot grid trading bot.

These helpers keep every numerical operation consistent by using
:class:`decimal.Decimal` and by exposing a small set of focused functions
for price/quantity rounding, fee and slippage handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, getcontext
from typing import Literal

getcontext().prec = 28

Side = Literal["buy", "sell"]


def to_decimal(value: float | int | str | Decimal) -> Decimal:
    """Return a :class:`~decimal.Decimal` representation of ``value``.

    The helper converts the provided input using ``str`` in order to avoid
    inheriting floating point rounding errors.
    """

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_decimal(value: Decimal, precision: int) -> Decimal:
    """Round ``value`` **down** to the requested number of decimal places."""

    quant = Decimal("1").scaleb(-precision)
    return value.quantize(quant, rounding=ROUND_DOWN)


@dataclass(frozen=True)
class TradeBreakdown:
    """Structured representation of the result of a trade execution."""

    effective_price: Decimal
    quantity: Decimal
    fee_paid: Decimal
    quote_amount: Decimal


def apply_slippage(price: Decimal, slippage_rate: Decimal, side: Side) -> Decimal:
    """Apply slippage to ``price`` depending on the trade ``side``."""

    if slippage_rate <= Decimal("0"):
        return price

    factor = Decimal("1") + slippage_rate if side == "buy" else Decimal("1") - slippage_rate
    return price * factor


def calculate_fee(amount: Decimal, fee_rate: Decimal) -> Decimal:
    """Return the fee amount given a traded ``amount`` and ``fee_rate``."""

    if fee_rate <= Decimal("0"):
        return Decimal("0")
    return amount * fee_rate


def execute_buy(
    quote_amount: Decimal,
    price: Decimal,
    fee_rate: Decimal,
    slippage_rate: Decimal,
    quantity_precision: int,
    price_precision: int,
) -> TradeBreakdown:
    """Convert ``quote_amount`` into base asset units using ``price``.

    Slippage increases the paid price while fees reduce the amount of base
    obtained. The resulting base quantity is rounded down to keep balances
    from becoming negative because of rounding side-effects.
    """

    effective_price = apply_slippage(price, slippage_rate, side="buy")
    base_without_fee = quote_amount / effective_price
    fee_paid = calculate_fee(base_without_fee, fee_rate)
    base_after_fee = base_without_fee - fee_paid
    quantity = round_decimal(base_after_fee, quantity_precision)
    quote_consumed = round_decimal(quote_amount, price_precision)
    return TradeBreakdown(
        effective_price=round_decimal(effective_price, price_precision),
        quantity=quantity,
        fee_paid=round_decimal(fee_paid, quantity_precision),
        quote_amount=quote_consumed,
    )


def execute_sell(
    base_amount: Decimal,
    price: Decimal,
    fee_rate: Decimal,
    slippage_rate: Decimal,
    quantity_precision: int,
    price_precision: int,
) -> TradeBreakdown:
    """Convert ``base_amount`` into quote asset units using ``price``."""

    base_amount = round_decimal(base_amount, quantity_precision)
    effective_price = apply_slippage(price, slippage_rate, side="sell")
    quote_without_fee = base_amount * effective_price
    fee_paid = calculate_fee(quote_without_fee, fee_rate)
    quote_after_fee = quote_without_fee - fee_paid
    quote_amount = round_decimal(quote_after_fee, price_precision)
    return TradeBreakdown(
        effective_price=round_decimal(effective_price, price_precision),
        quantity=base_amount,
        fee_paid=round_decimal(fee_paid, price_precision),
        quote_amount=quote_amount,
    )
