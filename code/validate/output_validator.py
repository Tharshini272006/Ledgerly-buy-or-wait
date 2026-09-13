from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from code.config import OUTPUT_COLUMNS
from code.data.models import Request


ALLOWED_STATUS = {"affordable_now", "affordable_with_plan", "affordable_later", "not_affordable"}
ALLOWED_METHODS = {"full_payment", "partial_payment", "installments", "wait", "not_recommended"}


def validate_output(path: Path, requests: tuple[Request, ...]) -> list[str]:
    errors: list[str] = []
    request_by_id = {request.request_id: request for request in requests}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != OUTPUT_COLUMNS:
            errors.append(f"Output columns differ from required order: {reader.fieldnames}")
            return errors
        rows = list(reader)

    seen: set[str] = set()
    for row in rows:
        request_id = row["request_id"]
        if request_id in seen:
            errors.append(f"Duplicate output row for {request_id}")
        seen.add(request_id)
        request = request_by_id.get(request_id)
        if request is None:
            errors.append(f"Unknown request_id {request_id}")
            continue
        try:
            safe = Decimal(row["amount_safe_to_pay"])
        except Exception:
            errors.append(f"Invalid amount_safe_to_pay for {request_id}")
            continue
        if safe < 0 or safe > request.requested_amount:
            errors.append(f"amount_safe_to_pay out of bounds for {request_id}")
        if row["affordability_status"] not in ALLOWED_STATUS:
            errors.append(f"Invalid affordability_status for {request_id}")
        if row["recommended_payment_method"] not in ALLOWED_METHODS:
            errors.append(f"Invalid recommended_payment_method for {request_id}")
        if row["payment_plan"] != "none":
            for part in row["payment_plan"].split("|"):
                pieces = part.split(":")
                if len(pieces) != 2:
                    errors.append(f"Invalid payment_plan entry for {request_id}: {part}")

    missing = set(request_by_id) - seen
    extra = seen - set(request_by_id)
    if missing:
        errors.append(f"Missing output rows: {sorted(missing)[:10]}")
    if extra:
        errors.append(f"Extra output rows: {sorted(extra)[:10]}")
    return errors
