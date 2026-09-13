from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from code.config import FORECAST_DAYS
from code.data.models import FinancialEvent, UserProfile
from code.fx.converter import FXConverter


@dataclass(frozen=True)
class CashFlow:
    flow_date: date
    amount: Decimal
    source_id: str


def event_cash_flow(event: FinancialEvent, profile: UserProfile, fx: FXConverter) -> CashFlow | None:
    if event.amount is None:
        return None
    if event.status in {"cancelled", "failed", "unrealized"} or event.event_type == "non_cash":
        return None
    cash_date = event.settlement_date
    if cash_date is None:
        return None
    if event.status == "pending" and event.direction != "debit":
        return None
    if event.status not in {"settled", "scheduled", "pending"}:
        return None
    signed = event.amount if event.direction == "credit" else -event.amount
    converted = fx.convert(signed, event.currency, profile.home_currency, cash_date)
    return CashFlow(cash_date, converted, event.event_id)


def projected_flows(
    events: tuple[FinancialEvent, ...],
    profile: UserProfile,
    fx: FXConverter,
    start: date,
    horizon_days: int = FORECAST_DAYS,
) -> tuple[CashFlow, ...]:
    end = start + timedelta(days=horizon_days)
    flows = []
    for event in events:
        flow = event_cash_flow(event, profile, fx)
        if flow is not None and start <= flow.flow_date <= end:
            flows.append(flow)
    return tuple(sorted(flows, key=lambda flow: (flow.flow_date, flow.source_id)))


def _median_gap(dates: list[date]) -> int | None:
    if len(dates) < 3:
        return None
    gaps = sorted((dates[index] - dates[index - 1]).days for index in range(1, len(dates)))
    mid = len(gaps) // 2
    return gaps[mid]


def _stable_gap(dates: list[date]) -> int | None:
    gap = _median_gap(dates)
    if gap is None or gap < 5 or gap > 35:
        return None
    gaps = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
    close = sum(1 for item in gaps if abs(item - gap) <= 3)
    return gap if close >= max(2, len(gaps) - 1) else None


def recurring_flows(
    events: tuple[FinancialEvent, ...],
    profile: UserProfile,
    fx: FXConverter,
    start: date,
    horizon_days: int = FORECAST_DAYS,
    stopped_event_ids: frozenset[str] = frozenset(),
) -> tuple[CashFlow, ...]:
    end = start + timedelta(days=horizon_days)
    groups: dict[tuple[str, str, str, str], list[FinancialEvent]] = {}
    variable_categories = {"groceries", "transport", "dining", "utilities", "shopping", "healthcare"}
    for event in events:
        if event.amount is None or event.settlement_date is None:
            continue
        if event.settlement_date >= start and not (event.category == "salary" and event.status == "scheduled"):
            continue
        if event.status not in {"settled", "scheduled"} or event.event_type == "non_cash" or event.direction not in {"debit", "credit"}:
            continue
        is_essential = event.category in profile.protected_categories or event.category == "salary"
        is_stoppable = event.flexibility == "stoppable" and event.category in profile.stoppable_categories
        if not (is_essential or is_stoppable):
            continue
        if event.category == "salary":
            key = (event.direction, event.category, "*", event.currency)
        elif event.event_type in {"subscription"} or event.flexibility in {"stoppable", "fixed"}:
            key = (event.direction, event.category, event.description.lower(), event.currency)
        elif event.category in variable_categories:
            key = (event.direction, event.category, "*", event.currency)
        else:
            continue
        groups.setdefault(key, []).append(event)

    flows: list[CashFlow] = []
    for key, group in groups.items():
        group = sorted(group, key=lambda event: event.settlement_date or event.event_date)
        dates = [event.settlement_date for event in group if event.settlement_date is not None]
        gap = _stable_gap(dates)
        if gap is None:
            continue
        last = group[-1]
        if last.event_id in stopped_event_ids:
            continue
        recent = group[-min(4, len(group)) :]
        amounts = [event.amount for event in recent if event.amount is not None]
        if not amounts:
            continue
        amount = max(amounts) if key[0] == "debit" else amounts[-1]
        signed = amount if key[0] == "credit" else -amount
        historical_rate_date = last.settlement_date or last.event_date
        converted_signed = fx.convert(signed, last.currency, profile.home_currency, historical_rate_date)
        next_date = (last.settlement_date or last.event_date) + timedelta(days=gap)
        while next_date <= start:
            next_date += timedelta(days=gap)
        while next_date <= end:
            flows.append(CashFlow(next_date, converted_signed, f"recurring:{last.event_id}"))
            next_date += timedelta(days=gap)
    return tuple(sorted(flows, key=lambda flow: (flow.flow_date, flow.source_id)))


def all_projected_flows(
    events: tuple[FinancialEvent, ...],
    profile: UserProfile,
    fx: FXConverter,
    start: date,
    horizon_days: int = FORECAST_DAYS,
    stopped_event_ids: frozenset[str] = frozenset(),
) -> tuple[CashFlow, ...]:
    return tuple(
        sorted(
            projected_flows(events, profile, fx, start, horizon_days)
            + recurring_flows(events, profile, fx, start, horizon_days, stopped_event_ids),
            key=lambda flow: (flow.flow_date, flow.source_id),
        )
    )


def is_plan_safe(
    profile: UserProfile,
    flows: tuple[CashFlow, ...],
    payments: tuple[tuple[date, Decimal], ...],
    start: date,
    horizon_days: int = FORECAST_DAYS,
) -> bool:
    end = start + timedelta(days=horizon_days)
    dated: dict[date, Decimal] = {}
    for flow in flows:
        if start <= flow.flow_date <= end:
            dated[flow.flow_date] = dated.get(flow.flow_date, Decimal("0")) + flow.amount
    for payment_date, amount in payments:
        if start <= payment_date <= end:
            dated[payment_date] = dated.get(payment_date, Decimal("0")) - amount

    balance = profile.current_available_balance
    for current_date in sorted(dated):
        balance += dated[current_date]
        if balance < profile.minimum_balance_to_keep:
            return False
    return balance >= profile.minimum_balance_to_keep
