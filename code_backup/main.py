from __future__ import annotations

import csv
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import OUTPUT_COLUMNS, REPO_ROOT
from code.data.indexes import build_indexes
from code.data.loaders import load_dataset
from code.decisions.capacity import amount_safe_to_pay, earliest_full_payment_date
from code.decisions.explainer import explain, format_money, format_plan
from code.decisions.plans import PlanCandidate, generate_candidates
from code.decisions.ranker import rank_candidates
from code.evidence.images import resolve_image_amounts
from code.forecast.simulator import all_projected_flows, recurring_flows
from code.fx.converter import FXConverter
from code.validate.output_validator import validate_output


def decide_rows(request_filename: str = "requests.csv") -> list[dict[str, str]]:
    dataset = load_dataset(request_filename=request_filename)
    dataset = type(dataset)(
        profiles=dataset.profiles,
        events=resolve_image_amounts(dataset.events, dataset.images),
        requests=dataset.requests,
        payment_options=dataset.payment_options,
        messages=dataset.messages,
        images=dataset.images,
        exchange_rates=dataset.exchange_rates,
    )
    indexes = build_indexes(dataset)
    fx = FXConverter.from_rates(dataset.exchange_rates)
    rows: list[dict[str, str]] = []

    for request in dataset.requests:
        profile = indexes.profiles_by_user_id[request.user_id]
        user_events = indexes.events_by_user_id.get(request.user_id, ())
        flows = all_projected_flows(user_events, profile, fx, request.request_date)
        safe_now = amount_safe_to_pay(profile, request, flows)
        earliest_full = earliest_full_payment_date(profile, request, flows)
        options = indexes.payment_options_by_request_id.get(request.request_id, ())
        candidates = list(generate_candidates(profile, request, options, flows, safe_now, earliest_full))

        if "full_payment" in profile.payment_methods:
            recurring = recurring_flows(user_events, profile, fx, request.request_date)
            recurring_stop_ids = set()
            for flow in recurring:
                if flow.amount >= 0 or not flow.source_id.startswith("recurring:"):
                    continue
                event_id = flow.source_id.removeprefix("recurring:")
                event = indexes.events_by_event_id.get(event_id)
                if (
                    event is not None
                    and event.flexibility == "stoppable"
                    and event.category in profile.stoppable_categories
                    and event.category not in profile.protected_categories
                ):
                    recurring_stop_ids.add(event_id)
            for event_id in sorted(recurring_stop_ids):
                changed_flows = all_projected_flows(
                    user_events,
                    profile,
                    fx,
                    request.request_date,
                    stopped_event_ids=frozenset({event_id}),
                )
                changed_safe = amount_safe_to_pay(profile, request, changed_flows)
                if changed_safe >= request.requested_amount:
                    candidates.append(
                        PlanCandidate(
                            "full_payment",
                            "affordable_with_plan",
                            ((request.request_date, request.requested_amount),),
                            request.requested_amount,
                            "",
                            f"stop:{event_id}",
                        )
                    )
        selected = rank_candidates(request, tuple(candidates))

        if selected is None:
            status = "not_affordable"
            method = "not_recommended"
            payment_plan = "none"
            spending_changes = "none"
        else:
            status = selected.status
            method = selected.method
            payment_plan = format_plan(selected.payments)
            spending_changes = selected.spending_changes

        rows.append(
            {
                "request_id": request.request_id,
                "amount_safe_to_pay": format_money(safe_now),
                "affordability_status": status,
                "recommended_payment_method": method,
                "payment_plan": payment_plan,
                "earliest_date_for_full_payment": earliest_full.isoformat() if earliest_full else "",
                "spending_changes_needed": spending_changes,
                "decision_explanation": explain(profile, request, selected, safe_now, earliest_full),
            }
        )
    return rows


def write_output(rows: list[dict[str, str]], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows = decide_rows("requests.csv")
    output_path = REPO_ROOT / "output.csv"
    write_output(rows, output_path)
    dataset = load_dataset()
    errors = validate_output(output_path, dataset.requests)
    if errors:
        for error in errors:
            print(f"VALIDATION: {error}")
        return 1
    print(f"Wrote {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
