from __future__ import annotations

from code.data.models import Request
from code.decisions.plans import PlanCandidate


def rank_candidates(request: Request, candidates: tuple[PlanCandidate, ...]) -> PlanCandidate | None:
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda plan: (
            plan.payments[-1][0] > request.desired_completion_date,
            plan.spending_changes != "none",
            plan.total_payable,
            plan.first_payment_date,
            len(plan.payments),
            plan.payment_option_id or "",
        ),
    )
