"""Core logic for a simple geometric grid trading bot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Optional


Side = Literal["buy", "sell"]


class GridBotError(Exception):
    """Base exception for the grid bot module."""


class InsufficientBalanceError(GridBotError):
    """Raised when an order cannot be executed due to insufficient balance."""

    def __init__(self, side: Side, required: float, available: float) -> None:
        super().__init__(
            f"Insufficient {side} balance: required {required:.8f}, available {available:.8f}."
        )
        self.side = side
        self.required = required
        self.available = available


@dataclass
class GridOrder:
    """Represents an order placed on the grid."""

    side: Side
    price: float
    quantity: float
    executed: bool = False


@dataclass
class Trade:
    """Data captured after executing a trade."""

    side: Side
    price: float
    quantity: float
    fee_paid: float
    executed_price: float

    @property
    def slippage(self) -> float:
        """Return the absolute slippage applied to the order."""

        if self.side == "buy":
            return self.executed_price - self.price
        return self.price - self.executed_price


class GridBot:
    """Implements a very small grid trading strategy for spot markets."""

    def __init__(
        self,
        base_price: float,
        levels: int,
        ratio: float,
        quantity_per_order: float,
        base_balance: float,
        quote_balance: float,
        fee_rate: float = 0.001,
        slippage: float = 0.0,
    ) -> None:
        self._validate_inputs(
            base_price,
            levels,
            ratio,
            quantity_per_order,
            base_balance,
            quote_balance,
            fee_rate,
            slippage,
        )

        self.base_price = base_price
        self.levels = levels
        self.ratio = ratio
        self.quantity_per_order = quantity_per_order
        self.base_balance = base_balance
        self.quote_balance = quote_balance
        self.fee_rate = fee_rate
        self.slippage = slippage

        self.orders: List[GridOrder] = self._build_orders()
        self.trade_history: List[Trade] = []

    @staticmethod
    def _validate_inputs(
        base_price: float,
        levels: int,
        ratio: float,
        quantity_per_order: float,
        base_balance: float,
        quote_balance: float,
        fee_rate: float,
        slippage: float,
    ) -> None:
        if base_price <= 0:
            raise ValueError("base_price must be greater than zero.")
        if levels < 1:
            raise ValueError("levels must be at least one.")
        if ratio <= 1.0:
            raise ValueError("ratio must be greater than 1 to build a geometric grid.")
        if quantity_per_order <= 0:
            raise ValueError("quantity_per_order must be greater than zero.")
        if base_balance < 0:
            raise ValueError("base_balance cannot be negative.")
        if quote_balance < 0:
            raise ValueError("quote_balance cannot be negative.")
        if fee_rate < 0:
            raise ValueError("fee_rate cannot be negative.")
        if slippage < 0:
            raise ValueError("slippage cannot be negative.")

    def _build_orders(self) -> List[GridOrder]:
        orders: List[GridOrder] = []
        for level in range(1, self.levels + 1):
            buy_price = self.base_price / (self.ratio**level)
            sell_price = self.base_price * (self.ratio**level)
            orders.append(GridOrder("buy", buy_price, self.quantity_per_order))
            orders.append(GridOrder("sell", sell_price, self.quantity_per_order))
        # Keep buy orders sorted descending (closest to base price first)
        buy_orders = sorted((o for o in orders if o.side == "buy"), key=lambda o: o.price, reverse=True)
        sell_orders = sorted((o for o in orders if o.side == "sell"), key=lambda o: o.price)
        return buy_orders + sell_orders

    def iter_orders(self, side: Optional[Side] = None) -> Iterable[GridOrder]:
        """Yield orders filtered by side while preserving configured ordering."""

        if side is None:
            yield from self.orders
        else:
            yield from (order for order in self.orders if order.side == side)

    def process_price(self, price: float) -> List[Trade]:
        """Process a market tick, executing any orders that become eligible."""

        if price <= 0:
            raise ValueError("price must be greater than zero for processing.")

        trades: List[Trade] = []
        for order in self.orders:
            if order.executed:
                continue
            if order.side == "buy" and price <= order.price:
                trades.append(self._execute_order(order))
            elif order.side == "sell" and price >= order.price:
                trades.append(self._execute_order(order))
        return trades

    def _execute_order(self, order: GridOrder) -> Trade:
        quantity = order.quantity
        if order.side == "buy":
            executed_price = order.price * (1 + self.slippage)
            gross_cost = executed_price * quantity
            fee_paid = gross_cost * self.fee_rate
            total_cost = gross_cost + fee_paid
            if total_cost - self.quote_balance > 1e-12:
                raise InsufficientBalanceError("buy", total_cost, self.quote_balance)
            self.quote_balance -= total_cost
            self.base_balance += quantity
        else:
            executed_price = order.price * (1 - self.slippage)
            if quantity - self.base_balance > 1e-12:
                raise InsufficientBalanceError("sell", quantity, self.base_balance)
            gross_proceeds = executed_price * quantity
            fee_paid = gross_proceeds * self.fee_rate
            self.base_balance -= quantity
            self.quote_balance += gross_proceeds - fee_paid

        order.executed = True
        trade = Trade(order.side, order.price, quantity, fee_paid, executed_price)
        self.trade_history.append(trade)
        return trade

    def outstanding_orders(self, side: Optional[Side] = None) -> List[GridOrder]:
        """Return a snapshot of outstanding (non executed) orders."""

        if side is None:
            return [order for order in self.orders if not order.executed]
        return [order for order in self.orders if order.side == side and not order.executed]

    def reset(self) -> None:
        """Reset order execution flags and clear trade history."""

        for order in self.orders:
            order.executed = False
        self.trade_history.clear()

