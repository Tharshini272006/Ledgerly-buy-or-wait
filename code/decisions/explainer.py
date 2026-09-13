from __future__ import annotations

from datetime import date
from decimal import Decimal

from code.data.models import Request, UserProfile
from code.decisions.plans import PlanCandidate


def format_money(amount: Decimal) -> str:
    normalized = amount.quantize(Decimal("0.01"))
    text = f"{normalized:f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


def format_plan(payments: tuple[tuple[date, Decimal], ...]) -> str:
    return "|".join(f"{payment_date.isoformat()}:{format_money(amount)}" for payment_date, amount in payments)


def explain(profile: UserProfile, request: Request, plan: PlanCandidate | None, safe_now: Decimal, earliest_full) -> str:
    currency = profile.home_currency
    minimum = format_money(profile.minimum_balance_to_keep)
    requested = format_money(request.requested_amount)
    safe = format_money(safe_now)
    if plan is None:
        return (
            f"Only {currency} {safe} is safe on {request.request_date.isoformat()}, and no allowed plan keeps the "
            f"balance above the {currency} {minimum} minimum within 90 days."
        )
    if plan.method == "full_payment":
        return f"Pay {currency} {requested} today while staying above the {currency} {minimum} minimum over 90 days."
    if plan.method == "installments":
        return (
            f"Use the supplied installment option starting {plan.first_payment_date.isoformat()}; the schedule stays "
            f"above the {currency} {minimum} minimum."
        )
    if plan.method == "partial_payment":
        return (
            f"Pay {currency} {safe} now and the remainder on {earliest_full.isoformat()}; both payments stay above "
            f"the {currency} {minimum} minimum."
        )
    return (
        f"Wait until {plan.first_payment_date.isoformat()} to pay {currency} {requested} in full; paying earlier "
        f"would risk the {currency} {minimum} minimum."
    )
