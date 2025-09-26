"""Public API for the :mod:`gridtrader` package."""

from .grid_bot import GridTradingBotGeomSpot
from .utils import (
    TradeBreakdown,
    apply_slippage,
    calculate_fee,
    execute_buy,
    execute_sell,
    round_decimal,
    to_decimal,
)
from .validators import (
    ensure_non_negative_balance,
    ensure_sufficient_balance,
    ensure_trade_result,
    validate_bounds,
    validate_eps,
    validate_non_negative,
    validate_positive,
    validate_precision,
    validate_rate,
)

__all__ = [
    "GridTradingBotGeomSpot",
    "TradeBreakdown",
    "apply_slippage",
    "calculate_fee",
    "execute_buy",
    "execute_sell",
    "round_decimal",
    "to_decimal",
    "ensure_non_negative_balance",
    "ensure_sufficient_balance",
    "ensure_trade_result",
    "validate_bounds",
    "validate_eps",
    "validate_non_negative",
    "validate_positive",
    "validate_precision",
    "validate_rate",
]
