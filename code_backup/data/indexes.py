from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from code.data.models import Dataset, FinancialEvent, ImageLink, Message, PaymentOption, Request, UserProfile


@dataclass(frozen=True)
class DatasetIndexes:
    profiles_by_user_id: dict[str, UserProfile]
    requests_by_request_id: dict[str, Request]
    requests_by_user_id: dict[str, tuple[Request, ...]]
    events_by_event_id: dict[str, FinancialEvent]
    events_by_user_id: dict[str, tuple[FinancialEvent, ...]]
    events_by_linked_event_id: dict[str, tuple[FinancialEvent, ...]]
    messages_by_request_id: dict[str, tuple[Message, ...]]
    messages_by_related_event_id: dict[str, tuple[Message, ...]]
    images_by_request_id: dict[str, tuple[ImageLink, ...]]
    images_by_related_event_id: dict[str, tuple[ImageLink, ...]]
    payment_options_by_request_id: dict[str, tuple[PaymentOption, ...]]


def _append_group(groups: dict[str, list], key: str | None, value) -> None:
    if key:
        groups[key].append(value)


def _freeze_groups(groups: dict[str, list]) -> dict[str, tuple]:
    return {key: tuple(values) for key, values in groups.items()}


def build_indexes(dataset: Dataset) -> DatasetIndexes:
    requests_by_user_id: dict[str, list[Request]] = defaultdict(list)
    events_by_user_id: dict[str, list[FinancialEvent]] = defaultdict(list)
    events_by_linked_event_id: dict[str, list[FinancialEvent]] = defaultdict(list)
    messages_by_request_id: dict[str, list[Message]] = defaultdict(list)
    messages_by_related_event_id: dict[str, list[Message]] = defaultdict(list)
    images_by_request_id: dict[str, list[ImageLink]] = defaultdict(list)
    images_by_related_event_id: dict[str, list[ImageLink]] = defaultdict(list)
    payment_options_by_request_id: dict[str, list[PaymentOption]] = defaultdict(list)

    for request in dataset.requests:
        requests_by_user_id[request.user_id].append(request)
    for event in dataset.events:
        events_by_user_id[event.user_id].append(event)
        _append_group(events_by_linked_event_id, event.linked_event_id, event)
    for message in dataset.messages:
        _append_group(messages_by_request_id, message.request_id, message)
        _append_group(messages_by_related_event_id, message.related_event_id, message)
    for image in dataset.images:
        _append_group(images_by_request_id, image.request_id, image)
        _append_group(images_by_related_event_id, image.related_event_id, image)
    for option in dataset.payment_options:
        payment_options_by_request_id[option.request_id].append(option)

    return DatasetIndexes(
        profiles_by_user_id={profile.user_id: profile for profile in dataset.profiles},
        requests_by_request_id={request.request_id: request for request in dataset.requests},
        requests_by_user_id=_freeze_groups(requests_by_user_id),
        events_by_event_id={event.event_id: event for event in dataset.events},
        events_by_user_id=_freeze_groups(events_by_user_id),
        events_by_linked_event_id=_freeze_groups(events_by_linked_event_id),
        messages_by_request_id=_freeze_groups(messages_by_request_id),
        messages_by_related_event_id=_freeze_groups(messages_by_related_event_id),
        images_by_request_id=_freeze_groups(images_by_request_id),
        images_by_related_event_id=_freeze_groups(images_by_related_event_id),
        payment_options_by_request_id=_freeze_groups(payment_options_by_request_id),
    )
