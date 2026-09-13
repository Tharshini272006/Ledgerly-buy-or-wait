from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from code.data.loaders import load_dataset
from code.data.indexes import build_indexes
from code.evidence.images import resolve_image_amounts
from code.fx.converter import FXConverter
from code.forecast.simulator import recurring_flows


def main() -> None:
    dataset = load_dataset(request_filename="sample_requests.csv")

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

    interesting = [
        "request_01",
        "request_03",
        "request_05",
        "request_10",
        "request_11",
        "request_20",
        "request_23",
        "request_25",
    ]

    for request_id in interesting:
        request = indexes.requests_by_request_id[request_id]
        profile = indexes.profiles_by_user_id[request.user_id]
        events = indexes.events_by_user_id.get(request.user_id, ())

        flows = recurring_flows(
            events,
            profile,
            fx,
            request.request_date,
        )

        print("\n" + "=" * 80)
        print(
            request_id,
            request.user_id,
            "| request date:",
            request.request_date,
            "| expected safe:",
            next(
                r["amount_safe_to_pay"]
                for r in __import__("csv").DictReader(
                    open(ROOT / "dataset" / "sample_requests.csv", encoding="utf-8")
                )
                if r["request_id"] == request_id
            ),
        )

        if not flows:
            print("NO RECURRING FLOWS")
            continue

        for flow in flows:
            print(
                flow.flow_date,
                f"{flow.amount:+}",
                flow.source_id,
            )


if __name__ == "__main__":
    main()