from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from code.data.models import PaymentOption, Request, UserProfile
from code.forecast.simulator import CashFlow, is_plan_safe


@dataclass(frozen=True)
class PlanCandidate:
    method: str
    status: str
    payments: tuple[tuple[object, Decimal], ...]
    total_payable: Decimal
    payment_option_id: str
    spending_changes: str = "none"

    @property
    def first_payment_date(self):
        return self.payments[0][0]


def option_schedule(option: PaymentOption) -> tuple[tuple[object, Decimal], ...]:
    frequency = option.payment_frequency_days or 0
    return tuple(
        (option.first_payment_date + timedelta(days=frequency * index), option.payment_amount)
        for index in range(option.number_of_payments)
    )


def generate_candidates(
    profile: UserProfile,
    request: Request,
    options: tuple[PaymentOption, ...],
    flows: tuple[CashFlow, ...],
    safe_now: Decimal,
    earliest_full,
) -> tuple[PlanCandidate, ...]:
    candidates: list[PlanCandidate] = []
    methods = set(profile.payment_methods)

    full_payments = ((request.request_date, request.requested_amount),)
    if "full_payment" in methods and is_plan_safe(profile, flows, full_payments, request.request_date):
        candidates.append(PlanCandidate("full_payment", "affordable_now", full_payments, request.requested_amount, ""))

    for option in options:
        if option.payment_method != "installments" or "installments" not in methods:
            continue
        if profile.max_installment_months is not None and option.number_of_payments > profile.max_installment_months:
            continue
        schedule = option_schedule(option)
        if schedule[-1][0] > request.desired_completion_date:
            continue
        if is_plan_safe(profile, flows, schedule, request.request_date):
            candidates.append(
                PlanCandidate("installments", "affordable_with_plan", schedule, option.total_payable_amount, option.payment_option_id)
            )

    if (
        request.allows_partial_payment
        and "partial_payment" in methods
        and Decimal("0") < safe_now < request.requested_amount
        and earliest_full is not None
        and earliest_full <= request.desired_completion_date
    ):
        remainder = request.requested_amount - safe_now
        schedule = ((request.request_date, safe_now), (earliest_full, remainder))
        if is_plan_safe(profile, flows, schedule, request.request_date):
            candidates.append(PlanCandidate("partial_payment", "affordable_with_plan", schedule, request.requested_amount, ""))

    if (
        "full_payment" in methods
        and earliest_full is not None
        and earliest_full > request.request_date
        and earliest_full <= request.desired_completion_date
    ):
        schedule = ((earliest_full, request.requested_amount),)
        candidates.append(PlanCandidate("wait", "affordable_later", schedule, request.requested_amount, ""))

    return tuple(candidates)
