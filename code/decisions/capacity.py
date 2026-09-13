from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from code.config import CURRENCY_PRECISION, FORECAST_DAYS
from code.data.models import Request, UserProfile
from code.forecast.simulator import CashFlow, is_plan_safe


CENT = Decimal("1").scaleb(-CURRENCY_PRECISION)


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT)


def amount_safe_to_pay(profile: UserProfile, request: Request, flows: tuple[CashFlow, ...]) -> Decimal:
    low = Decimal("0")
    high = request.requested_amount
    while high - low > CENT:
        mid = quantize_money((low + high) / Decimal("2"))
        if is_plan_safe(profile, flows, ((request.request_date, mid),), request.request_date):
            low = mid
        else:
            high = mid - CENT
    if is_plan_safe(profile, flows, ((request.request_date, high),), request.request_date):
        return quantize_money(min(high, request.requested_amount))
    return quantize_money(max(Decimal("0"), low))


def earliest_full_payment_date(profile: UserProfile, request: Request, flows: tuple[CashFlow, ...]):
    for offset in range(FORECAST_DAYS + 1):
        candidate = request.request_date + timedelta(days=offset)
        if is_plan_safe(profile, flows, ((candidate, request.requested_amount),), request.request_date):
            return candidate
    return None
