from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from code.data.models import ExchangeRate, FinancialEvent, UserProfile


@dataclass(frozen=True)
class FXConverter:
    rates: dict[tuple[date, str, str], Decimal]

    @classmethod
    def from_rates(cls, rates: tuple[ExchangeRate, ...]) -> "FXConverter":
        return cls(
            rates={
                (rate.rate_date, rate.from_currency, rate.to_currency): rate.rate
                for rate in rates
            }
        )

    def convert(self, amount: Decimal, from_currency: str, to_currency: str, rate_date: date) -> Decimal:
        if from_currency == to_currency:
            return amount
        key = (rate_date, from_currency, to_currency)
        try:
            rate = self.rates[key]
        except KeyError as exc:
            raise ValueError(
                f"Missing exact FX rate for {rate_date.isoformat()} {from_currency}->{to_currency}"
            ) from exc
        return amount * rate

    def event_amount_in_home_currency(self, event: FinancialEvent, profile: UserProfile) -> Decimal | None:
        if event.amount is None:
            return None
        rate_date = event.settlement_date or event.event_date
        return self.convert(event.amount, event.currency, profile.home_currency, rate_date)
