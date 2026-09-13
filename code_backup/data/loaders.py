from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Iterable, Optional, TypeVar

from code.config import DATASET_DIR
from code.data.models import (
    Dataset,
    ExchangeRate,
    FinancialEvent,
    ImageLink,
    Message,
    PaymentOption,
    Request,
    UserProfile,
)

T = TypeVar("T")


REQUIRED_COLUMNS = {
    "financial_profiles.csv": {
        "user_id",
        "home_currency",
        "current_available_balance",
        "minimum_balance_to_keep",
        "financial_priorities",
        "expense_categories_to_protect",
        "expense_categories_user_is_willing_to_reduce",
        "expense_categories_user_is_willing_to_stop",
        "payment_methods_user_will_consider",
        "max_installment_months",
    },
    "financial_events.csv": {
        "event_id",
        "user_id",
        "event_type",
        "description",
        "category",
        "direction",
        "amount",
        "currency",
        "event_date",
        "settlement_date",
        "status",
        "linked_event_id",
        "flexibility",
        "minimum_allowed_amount",
    },
    "requests.csv": {
        "request_id",
        "user_id",
        "request_date",
        "request_type",
        "requested_amount",
        "desired_completion_date",
        "allows_partial_payment",
        "request_text",
    },
    "request_payment_options.csv": {
        "payment_option_id",
        "request_id",
        "payment_method",
        "payment_amount",
        "number_of_payments",
        "first_payment_date",
        "payment_frequency_days",
        "financing_fee",
        "total_payable_amount",
    },
    "messages.csv": {
        "message_id",
        "user_id",
        "request_id",
        "related_event_id",
        "sent_at",
        "source_type",
        "message_text",
    },
    "images.csv": {"image_id", "user_id", "request_id", "related_event_id"},
    "exchange_rates.csv": {"rate_date", "from_currency", "to_currency", "rate"},
}


def parse_optional(value: str) -> Optional[str]:
    stripped = value.strip()
    return stripped or None


def parse_date(value: str, *, field: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid date for {field}: {value!r}") from exc


def parse_optional_date(value: str, *, field: str) -> Optional[date]:
    parsed = parse_optional(value)
    return parse_date(parsed, field=field) if parsed is not None else None


def parse_decimal(value: str, *, field: str) -> Decimal:
    try:
        return Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid decimal for {field}: {value!r}") from exc


def parse_optional_decimal(value: str, *, field: str) -> Optional[Decimal]:
    parsed = parse_optional(value)
    return parse_decimal(parsed, field=field) if parsed is not None else None


def parse_optional_int(value: str, *, field: str) -> Optional[int]:
    parsed = parse_optional(value)
    if parsed is None:
        return None
    try:
        return int(parsed)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {field}: {value!r}") from exc


def parse_bool(value: str, *, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"Invalid boolean for {field}: {value!r}")


def parse_pipe_list(value: str) -> tuple[str, ...]:
    parsed = parse_optional(value)
    if parsed is None:
        return ()
    return tuple(part.strip() for part in parsed.split("|") if part.strip())


def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} is missing a header row")
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def _ensure_unique(items: Iterable[T], key: Callable[[T], str], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        item_key = key(item)
        if item_key in seen:
            duplicates.add(item_key)
        seen.add(item_key)
    if duplicates:
        raise ValueError(f"Duplicate {label}: {sorted(duplicates)}")


def load_profiles(dataset_dir: Path = DATASET_DIR) -> tuple[UserProfile, ...]:
    rows = _read_csv(dataset_dir / "financial_profiles.csv", REQUIRED_COLUMNS["financial_profiles.csv"])
    profiles = tuple(
        UserProfile(
            user_id=row["user_id"],
            home_currency=row["home_currency"],
            current_available_balance=parse_decimal(row["current_available_balance"], field="current_available_balance"),
            minimum_balance_to_keep=parse_decimal(row["minimum_balance_to_keep"], field="minimum_balance_to_keep"),
            financial_priorities=parse_pipe_list(row["financial_priorities"]),
            protected_categories=parse_pipe_list(row["expense_categories_to_protect"]),
            reducible_categories=parse_pipe_list(row["expense_categories_user_is_willing_to_reduce"]),
            stoppable_categories=parse_pipe_list(row["expense_categories_user_is_willing_to_stop"]),
            payment_methods=parse_pipe_list(row["payment_methods_user_will_consider"]),
            max_installment_months=parse_optional_int(row["max_installment_months"], field="max_installment_months"),
        )
        for row in rows
    )
    _ensure_unique(profiles, lambda profile: profile.user_id, "user_id in financial_profiles.csv")
    return profiles


def load_events(dataset_dir: Path = DATASET_DIR) -> tuple[FinancialEvent, ...]:
    rows = _read_csv(dataset_dir / "financial_events.csv", REQUIRED_COLUMNS["financial_events.csv"])
    events = tuple(
        FinancialEvent(
            event_id=row["event_id"],
            user_id=row["user_id"],
            event_type=row["event_type"],
            description=row["description"],
            category=row["category"],
            direction=row["direction"],
            amount=parse_optional_decimal(row["amount"], field="amount"),
            currency=row["currency"],
            event_date=parse_date(row["event_date"], field="event_date"),
            settlement_date=parse_optional_date(row["settlement_date"], field="settlement_date"),
            status=row["status"],
            linked_event_id=parse_optional(row["linked_event_id"]),
            flexibility=parse_optional(row["flexibility"]),
            minimum_allowed_amount=parse_optional_decimal(row["minimum_allowed_amount"], field="minimum_allowed_amount"),
        )
        for row in rows
    )
    _ensure_unique(events, lambda event: event.event_id, "event_id in financial_events.csv")
    return events


def load_requests(dataset_dir: Path = DATASET_DIR, filename: str = "requests.csv") -> tuple[Request, ...]:
    rows = _read_csv(dataset_dir / filename, REQUIRED_COLUMNS["requests.csv"])
    requests = tuple(
        Request(
            request_id=row["request_id"],
            user_id=row["user_id"],
            request_date=parse_date(row["request_date"], field="request_date"),
            request_type=row["request_type"],
            requested_amount=parse_decimal(row["requested_amount"], field="requested_amount"),
            desired_completion_date=parse_date(row["desired_completion_date"], field="desired_completion_date"),
            allows_partial_payment=parse_bool(row["allows_partial_payment"], field="allows_partial_payment"),
            request_text=row["request_text"],
        )
        for row in rows
    )
    _ensure_unique(requests, lambda request: request.request_id, f"request_id in {filename}")
    return requests


def load_payment_options(dataset_dir: Path = DATASET_DIR) -> tuple[PaymentOption, ...]:
    rows = _read_csv(dataset_dir / "request_payment_options.csv", REQUIRED_COLUMNS["request_payment_options.csv"])
    options = tuple(
        PaymentOption(
            payment_option_id=row["payment_option_id"],
            request_id=row["request_id"],
            payment_method=row["payment_method"],
            payment_amount=parse_decimal(row["payment_amount"], field="payment_amount"),
            number_of_payments=int(row["number_of_payments"]),
            first_payment_date=parse_date(row["first_payment_date"], field="first_payment_date"),
            payment_frequency_days=parse_optional_int(row["payment_frequency_days"], field="payment_frequency_days"),
            financing_fee=parse_decimal(row["financing_fee"], field="financing_fee"),
            total_payable_amount=parse_decimal(row["total_payable_amount"], field="total_payable_amount"),
        )
        for row in rows
    )
    _ensure_unique(options, lambda option: option.payment_option_id, "payment_option_id in request_payment_options.csv")
    return options


def load_messages(dataset_dir: Path = DATASET_DIR) -> tuple[Message, ...]:
    rows = _read_csv(dataset_dir / "messages.csv", REQUIRED_COLUMNS["messages.csv"])
    messages = tuple(
        Message(
            message_id=row["message_id"],
            user_id=row["user_id"],
            request_id=parse_optional(row["request_id"]),
            related_event_id=parse_optional(row["related_event_id"]),
            sent_at=row["sent_at"],
            source_type=row["source_type"],
            message_text=row["message_text"],
        )
        for row in rows
    )
    _ensure_unique(messages, lambda message: message.message_id, "message_id in messages.csv")
    return messages


def load_images(dataset_dir: Path = DATASET_DIR) -> tuple[ImageLink, ...]:
    rows = _read_csv(dataset_dir / "images.csv", REQUIRED_COLUMNS["images.csv"])
    images = tuple(
        ImageLink(
            image_id=row["image_id"],
            user_id=row["user_id"],
            request_id=parse_optional(row["request_id"]),
            related_event_id=parse_optional(row["related_event_id"]),
        )
        for row in rows
    )
    _ensure_unique(images, lambda image: image.image_id, "image_id in images.csv")
    return images


def load_exchange_rates(dataset_dir: Path = DATASET_DIR) -> tuple[ExchangeRate, ...]:
    rows = _read_csv(dataset_dir / "exchange_rates.csv", REQUIRED_COLUMNS["exchange_rates.csv"])
    rates = tuple(
        ExchangeRate(
            rate_date=parse_date(row["rate_date"], field="rate_date"),
            from_currency=row["from_currency"],
            to_currency=row["to_currency"],
            rate=parse_decimal(row["rate"], field="rate"),
        )
        for row in rows
    )
    _ensure_unique(
        rates,
        lambda rate: f"{rate.rate_date}|{rate.from_currency}|{rate.to_currency}",
        "exchange-rate key in exchange_rates.csv",
    )
    return rates


def load_dataset(dataset_dir: Path = DATASET_DIR, request_filename: str = "requests.csv") -> Dataset:
    return Dataset(
        profiles=load_profiles(dataset_dir),
        events=load_events(dataset_dir),
        requests=load_requests(dataset_dir, request_filename),
        payment_options=load_payment_options(dataset_dir),
        messages=load_messages(dataset_dir),
        images=load_images(dataset_dir),
        exchange_rates=load_exchange_rates(dataset_dir),
    )
