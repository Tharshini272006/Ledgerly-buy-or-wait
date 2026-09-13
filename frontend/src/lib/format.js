export const money = (value, currency = "ZAR") =>
  new Intl.NumberFormat("en-ZA", { style: "currency", currency, maximumFractionDigits: 2 }).format(value);

export const shortMoney = (value, currency = "ZAR") =>
  new Intl.NumberFormat("en-ZA", { style: "currency", currency, notation: "compact", maximumFractionDigits: 1 }).format(value);
