"""Geometric grid trading bot implementation for spot markets."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any, Dict, List

from . import utils
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

getcontext().prec = 28


@dataclass
class GridLevel:
    price: Decimal
    status: str = "quote"  # either "quote" or "base"
    quote_budget: Decimal = Decimal("0")
    base_position: Decimal = Decimal("0")
    last_action: str | None = None


@dataclass
class TradeLog:
    timestamp: datetime
    side: str
    level_price: Decimal
    execution_price: Decimal
    quantity: Decimal
    quote_amount: Decimal
    fee_paid: Decimal
    note: str


@dataclass
class GridTradingBotGeomSpot:
    """Spot market grid trading bot using geometrically spaced price levels."""

    base_asset: str
    quote_asset: str
    num_levels: int
    lower_price: Decimal
    upper_price: Decimal
    initial_price: Decimal
    base_balance: Decimal
    quote_balance: Decimal
    fee_rate: Decimal = Decimal("0")
    slippage_rate: Decimal = Decimal("0")
    price_precision: int = 2
    quantity_precision: int = 8
    eps: Decimal = Decimal("1e-9")
    levels: List[GridLevel] = field(default_factory=list)
    trade_history: List[TradeLog] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.eps = validate_eps(self.eps)
        self.lower_price, self.upper_price, self.initial_price = validate_bounds(
            self.lower_price, self.upper_price, self.num_levels, self.initial_price, self.eps
        )
        self.base_balance = validate_non_negative(self.base_balance, "base_balance", self.eps)
        self.quote_balance = validate_non_negative(self.quote_balance, "quote_balance", self.eps)
        self.fee_rate = validate_rate(self.fee_rate, "fee_rate")
        self.slippage_rate = validate_rate(self.slippage_rate, "slippage_rate")
        self.price_precision = validate_precision(self.price_precision, "price_precision")
        self.quantity_precision = validate_precision(self.quantity_precision, "quantity_precision")

        self._build_levels()

    # ------------------------------------------------------------------
    # Grid creation helpers
    # ------------------------------------------------------------------
    def _build_levels(self) -> None:
        ratio = (self.upper_price / self.lower_price) ** (Decimal(1) / Decimal(self.num_levels - 1))
        prices: List[Decimal] = []
        price = self.lower_price
        for _ in range(self.num_levels):
            prices.append(price)
            price = price * ratio

        base_levels = [p for p in prices if p <= self.initial_price + self.eps]
        quote_levels = [p for p in prices if p > self.initial_price + self.eps]

        remaining_base = self.base_balance
        remaining_quote = self.quote_balance
        base_allocations: Dict[Decimal, Decimal] = {}
        quote_allocations: Dict[Decimal, Decimal] = {}

        # Allocate base evenly for levels already below the initial price
        total_base_levels = len(base_levels)
        for index, level_price in enumerate(base_levels):
            if total_base_levels == 0:
                break
            levels_left = total_base_levels - index
            allocation = remaining_base / levels_left if levels_left else Decimal("0")
            allocation = utils.round_decimal(allocation, self.quantity_precision)
            allocation = min(allocation, remaining_base)
            remaining_base -= allocation
            base_allocations[level_price] = allocation

        # Allocate quote evenly for levels above the initial price
        total_quote_levels = len(quote_levels)
        for index, level_price in enumerate(quote_levels):
            if total_quote_levels == 0:
                break
            levels_left = total_quote_levels - index
            allocation = remaining_quote / levels_left if levels_left else Decimal("0")
            allocation = utils.round_decimal(allocation, self.price_precision)
            allocation = min(allocation, remaining_quote)
            remaining_quote -= allocation
            quote_allocations[level_price] = allocation

        self.levels = []
        for price in prices:
            level = GridLevel(price=utils.round_decimal(price, self.price_precision))
            if price <= self.initial_price + self.eps:
                level.status = "base"
                level.base_position = base_allocations.get(price, Decimal("0"))
            else:
                level.status = "quote"
                level.quote_budget = quote_allocations.get(price, Decimal("0"))
            self.levels.append(level)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def on_price_tick(self, price: float | Decimal) -> None:
        """Process a new market price and execute pending grid actions."""

        current_price = validate_positive(price, "market_price", self.eps)

        for level in self.levels:
            if level.status == "quote" and current_price <= level.price + self.eps:
                self._execute_buy(level)

        for level in reversed(self.levels):
            if level.status == "base" and current_price >= level.price - self.eps:
                self._execute_sell(level)

        ensure_non_negative_balance(self.base_balance, self.base_asset, self.eps)
        ensure_non_negative_balance(self.quote_balance, self.quote_asset, self.eps)

    def snapshot(self) -> Dict[str, Any]:
        """Return a structured snapshot of the bot's current state."""

        return {
            "base_balance": self.base_balance,
            "quote_balance": self.quote_balance,
            "levels": [
                {
                    "price": level.price,
                    "status": level.status,
                    "quote_budget": level.quote_budget,
                    "base_position": level.base_position,
                    "last_action": level.last_action,
                }
                for level in self.levels
            ],
            "trade_history": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "side": log.side,
                    "level_price": log.level_price,
                    "execution_price": log.execution_price,
                    "quantity": log.quantity,
                    "quote_amount": log.quote_amount,
                    "fee_paid": log.fee_paid,
                    "note": log.note,
                }
                for log in self.trade_history
            ],
        }

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------
    def _execute_buy(self, level: GridLevel) -> None:
        quote_amount = level.quote_budget
        if quote_amount <= self.eps:
            return

        ensure_sufficient_balance(self.quote_balance, quote_amount, self.quote_asset, self.eps)
        trade = utils.execute_buy(
            quote_amount=quote_amount,
            price=level.price,
            fee_rate=self.fee_rate,
            slippage_rate=self.slippage_rate,
            quantity_precision=self.quantity_precision,
            price_precision=self.price_precision,
        )
        ensure_trade_result(trade.quantity, self.base_asset, self.eps)

        self.quote_balance -= trade.quote_amount
        self.base_balance += trade.quantity
        level.base_position = trade.quantity
        level.quote_budget = Decimal("0")
        level.status = "base"
        level.last_action = "buy"

        self.trade_history.append(
            TradeLog(
                timestamp=datetime.utcnow(),
                side="buy",
                level_price=level.price,
                execution_price=trade.effective_price,
                quantity=trade.quantity,
                quote_amount=trade.quote_amount,
                fee_paid=trade.fee_paid,
                note=f"Bought {trade.quantity} {self.base_asset} using {trade.quote_amount} {self.quote_asset}",
            )
        )

    def _execute_sell(self, level: GridLevel) -> None:
        base_amount = level.base_position
        if base_amount <= self.eps:
            return

        ensure_sufficient_balance(self.base_balance, base_amount, self.base_asset, self.eps)
        trade = utils.execute_sell(
            base_amount=base_amount,
            price=level.price,
            fee_rate=self.fee_rate,
            slippage_rate=self.slippage_rate,
            quantity_precision=self.quantity_precision,
            price_precision=self.price_precision,
        )
        ensure_trade_result(trade.quote_amount, self.quote_asset, self.eps)

        self.base_balance -= trade.quantity
        self.quote_balance += trade.quote_amount
        level.base_position = Decimal("0")
        level.quote_budget = trade.quote_amount
        level.status = "quote"
        level.last_action = "sell"

        self.trade_history.append(
            TradeLog(
                timestamp=datetime.utcnow(),
                side="sell",
                level_price=level.price,
                execution_price=trade.effective_price,
                quantity=trade.quantity,
                quote_amount=trade.quote_amount,
                fee_paid=trade.fee_paid,
                note=f"Sold {trade.quantity} {self.base_asset} for {trade.quote_amount} {self.quote_asset}",
            )
        )
