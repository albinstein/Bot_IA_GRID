"""Validation helpers for the geometric spot grid trading bot."""

from __future__ import annotations

from decimal import Decimal

from .utils import to_decimal


def validate_eps(eps: float | Decimal) -> Decimal:
    eps_dec = to_decimal(eps)
    if eps_dec <= Decimal("0"):
        raise ValueError("eps must be greater than zero")
    return eps_dec


def validate_positive(value: float | Decimal, name: str, eps: Decimal) -> Decimal:
    dec_value = to_decimal(value)
    if dec_value <= eps:
        raise ValueError(f"{name} must be greater than {eps}")
    return dec_value


def validate_non_negative(value: float | Decimal, name: str, eps: Decimal) -> Decimal:
    dec_value = to_decimal(value)
    if dec_value < -eps:
        raise ValueError(f"{name} cannot be negative (value={dec_value})")
    return dec_value


def validate_bounds(
    lower_price: float | Decimal,
    upper_price: float | Decimal,
    num_levels: int,
    initial_price: float | Decimal,
    eps: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    lower = validate_positive(lower_price, "lower_price", eps)
    upper = validate_positive(upper_price, "upper_price", eps)
    if num_levels < 2:
        raise ValueError("num_levels must be at least 2 to build a geometric grid")
    if lower >= upper:
        raise ValueError("lower_price must be strictly less than upper_price")
    init_price = validate_positive(initial_price, "initial_price", eps)
    if init_price < lower - eps or init_price > upper + eps:
        raise ValueError("initial_price must lie within the [lower_price, upper_price] range")
    return lower, upper, init_price


def validate_rate(value: float | Decimal, name: str) -> Decimal:
    dec_value = to_decimal(value)
    if dec_value < Decimal("0"):
        raise ValueError(f"{name} cannot be negative")
    if dec_value >= Decimal("1"):
        raise ValueError(f"{name} must be lower than 1")
    return dec_value


def validate_precision(precision: int, name: str) -> int:
    if precision < 0:
        raise ValueError(f"{name} must be non-negative")
    return precision


def ensure_sufficient_balance(balance: Decimal, required: Decimal, asset: str, eps: Decimal) -> None:
    if balance + eps < required:
        raise ValueError(
            f"Insufficient balance for {asset}: required {required}, available {balance}"
        )


def ensure_non_negative_balance(balance: Decimal, asset: str, eps: Decimal) -> None:
    if balance < -eps:
        raise ValueError(f"Balance for {asset} became negative: {balance}")


def ensure_trade_result(quantity: Decimal, asset: str, eps: Decimal) -> None:
    if quantity <= eps:
        raise ValueError(f"Trade on {asset} would result in a null or negative quantity ({quantity})")
