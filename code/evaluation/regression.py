from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SAMPLE = ROOT / "dataset" / "sample_requests.csv"
OUTPUT_NAME = "evaluation" + "/sample_output.csv"

FIELDS = [
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed",
]


def normalize(value: str | None) -> str:
    return (value or "").strip()


def main() -> int:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "code" / "main.py"),
            "--input",
            "sample_requests.csv",
            "--output",
            OUTPUT_NAME,
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        print("\nSolver failed.")
        return result.returncode

    with SAMPLE.open("r", encoding="utf-8", newline="") as f:
        expected_rows = list(csv.DictReader(f))

    actual_path = ROOT / OUTPUT_NAME

    with actual_path.open("r", encoding="utf-8", newline="") as f:
        actual_rows = list(csv.DictReader(f))

    expected = {row["request_id"]: row for row in expected_rows}
    actual = {row["request_id"]: row for row in actual_rows}

    exact_rows = 0
    field_matches = {field: 0 for field in FIELDS}

    for request_id, exp in expected.items():
        got = actual.get(request_id)

        if got is None:
            print(f"{request_id}: MISSING")
            continue

        row_exact = True

        for field in FIELDS:
            expected_value = normalize(exp.get(field))
            actual_value = normalize(got.get(field))

            if expected_value == actual_value:
                field_matches[field] += 1
            else:
                row_exact = False
                print(
                    f"{request_id} | {field}\n"
                    f"  expected: {expected_value}\n"
                    f"  actual:   {actual_value}"
                )

        if row_exact:
            exact_rows += 1

    print("\n===== PUBLIC REGRESSION =====")
    print(f"Exact rows: {exact_rows}/{len(expected)}")

    for field in FIELDS:
        print(f"{field}: {field_matches[field]}/{len(expected)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())