from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from code.config import FORECAST_DAYS
from code.data.models import FinancialEvent, UserProfile
from code.fx.converter import FXConverter


@dataclass(frozen=True)
class CashFlow:
    flow_date: date
    amount: Decimal
    source_id: str


def event_cash_flow(
    event: FinancialEvent,
    profile: UserProfile,
    fx: FXConverter,
) -> CashFlow | None:
    if event.amount is None:
        return None

    if (
        event.status in {"cancelled", "failed", "unrealized"}
        or event.event_type == "non_cash"
    ):
        return None

    cash_date = event.settlement_date

    if cash_date is None:
        return None

    # Pending debits are obligations, but pending credits are not
    # safe to count as available cash.
    if event.status == "pending" and event.direction != "debit":
        return None

    if event.status not in {"settled", "scheduled", "pending"}:
        return None

    signed = (
        event.amount
        if event.direction == "credit"
        else -event.amount
    )

    converted = fx.convert(
        signed,
        event.currency,
        profile.home_currency,
        cash_date,
    )

    return CashFlow(
        cash_date,
        converted,
        event.event_id,
    )


def projected_flows(
    events: tuple[FinancialEvent, ...],
    profile: UserProfile,
    fx: FXConverter,
    start: date,
    horizon_days: int = FORECAST_DAYS,
) -> tuple[CashFlow, ...]:
    end = start + timedelta(days=horizon_days)

    flows: list[CashFlow] = []

    for event in events:
        flow = event_cash_flow(event, profile, fx)

        if flow is not None and start <= flow.flow_date <= end:
            flows.append(flow)

    return tuple(
        sorted(
            flows,
            key=lambda flow: (flow.flow_date, flow.source_id),
        )
    )


def _add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _next_monthly_date(value: date) -> date:
    return _add_months(value, 1)


def _monthly_gap(dates: list[date]) -> int | None:
    if len(dates) < 3:
        return None

    month_steps = [
        (curr.year - prev.year) * 12 + (curr.month - prev.month)
        for prev, curr in zip(dates, dates[1:])
    ]

    if not month_steps or any(step != 1 for step in month_steps):
        return None

    day_deltas = [
        abs((curr.day - prev.day))
        for prev, curr in zip(dates, dates[1:])
    ]

    if max(day_deltas) > 3:
        return None

    return 1


def _median_gap(dates: list[date]) -> int | None:
    if len(dates) < 3:
        return None

    gaps = sorted(
        (dates[index] - dates[index - 1]).days
        for index in range(1, len(dates))
    )

    return gaps[len(gaps) // 2]


def _stable_gap(dates: list[date]) -> int | None:
    gap = _median_gap(dates)

    if gap is None or gap < 5 or gap > 35:
        return None

    gaps = [
        (dates[index] - dates[index - 1]).days
        for index in range(1, len(dates))
    ]

    close = sum(
        1
        for item in gaps
        if abs(item - gap) <= 3
    )

    return (
        gap
        if close >= max(2, len(gaps) - 1)
        else None
    )


def recurring_flows(
    events: tuple[FinancialEvent, ...],
    profile: UserProfile,
    fx: FXConverter,
    start: date,
    horizon_days: int = FORECAST_DAYS,
    stopped_event_ids: frozenset[str] = frozenset(),
) -> tuple[CashFlow, ...]:
    end = start + timedelta(days=horizon_days)

    groups: dict[
        tuple[str, str, str, str],
        list[FinancialEvent],
    ] = {}

    variable_categories = {
        "groceries",
        "transport",
        "dining",
        "utilities",
        "shopping",
        "healthcare",
    }

    for event in events:
        if event.amount is None or event.settlement_date is None:
            continue

        # Historical events only.
        # A scheduled salary after the request date is handled
        # through the recurring stream.
        if event.settlement_date >= start and not (
            event.category == "salary"
            and event.status == "scheduled"
        ):
            continue

        if event.status not in {"settled", "scheduled", "pending"}:
            continue

        if event.event_type == "non_cash":
            continue

        if event.direction not in {"debit", "credit"}:
            continue

        # IMPORTANT:
        # Do NOT use protected/stoppable profile categories to decide
        # whether a recurring expense exists.
        #
        # Those profile fields describe what the user permits us
        # to CHANGE later. They do not define baseline cash reality.

        if event.category == "salary":
            key = (
                event.direction,
                event.category,
                "*",
                event.currency,
            )

        elif (
            event.event_type == "subscription"
            or event.flexibility in {"stoppable", "fixed"}
        ):
            key = (
                event.direction,
                event.category,
                event.description.lower(),
                event.currency,
            )

        elif event.category in variable_categories:
            key = (
                event.direction,
                event.category,
                "*",
                event.currency,
            )

        else:
            # Only ignore event types/categories that cannot be
            # established as recurring by the current recurrence model.
            continue

        groups.setdefault(key, []).append(event)

    flows: list[CashFlow] = []

    for key, group in groups.items():
        group = sorted(
            group,
            key=lambda event: (
                event.settlement_date
                or event.event_date
            ),
        )

        dates = [
            event.settlement_date
            for event in group
            if event.settlement_date is not None
        ]

        monthly_gap = _monthly_gap(dates)

        if monthly_gap is not None:
            gap_days = None
            month_step = 1
        else:
            gap_days = _stable_gap(dates)
            month_step = 0

        if gap_days is None and monthly_gap is None:
            continue

        last = group[-1]

        if last.event_id in stopped_event_ids:
            continue

        recent = group[-min(4, len(group)):]

        amounts = [
            event.amount
            for event in recent
            if event.amount is not None
        ]

        if not amounts:
            continue

        # Conservative recurring debit estimate.
        # For income, use the latest observed amount.
        amount = (
            max(amounts)
            if key[0] == "debit"
            else amounts[-1]
        )

        signed = (
            amount
            if key[0] == "credit"
            else -amount
        )

        historical_rate_date = (
            last.settlement_date
            or last.event_date
        )

        converted_signed = fx.convert(
            signed,
            last.currency,
            profile.home_currency,
            historical_rate_date,
        )

        if month_step:
            next_date = _next_monthly_date(historical_rate_date)
            while next_date <= start:
                next_date = _next_monthly_date(next_date)
            while next_date <= end:
                flows.append(
                    CashFlow(
                        next_date,
                        converted_signed,
                        f"recurring:{last.event_id}",
                    )
                )
                next_date = _next_monthly_date(next_date)
            continue

        next_date = (
            historical_rate_date
            + timedelta(days=gap_days)
        )

        while next_date <= start:
            next_date += timedelta(days=gap_days)

        while next_date <= end:
            flows.append(
                CashFlow(
                    next_date,
                    converted_signed,
                    f"recurring:{last.event_id}",
                )
            )

            next_date += timedelta(days=gap_days)

    return tuple(
        sorted(
            flows,
            key=lambda flow: (
                flow.flow_date,
                flow.source_id,
            ),
        )
    )


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
            projected_flows(
                events,
                profile,
                fx,
                start,
                horizon_days,
            )
            + recurring_flows(
                events,
                profile,
                fx,
                start,
                horizon_days,
                stopped_event_ids,
            ),
            key=lambda flow: (
                flow.flow_date,
                flow.source_id,
            ),
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
            dated[flow.flow_date] = (
                dated.get(flow.flow_date, Decimal("0"))
                + flow.amount
            )

    for payment_date, amount in payments:
        if start <= payment_date <= end:
            dated[payment_date] = (
                dated.get(payment_date, Decimal("0"))
                - amount
            )

    balance = profile.current_available_balance

    for current_date in sorted(dated):
        balance += dated[current_date]

        if balance < profile.minimum_balance_to_keep:
            return False

    return (
        balance
        >= profile.minimum_balance_to_keep
    )