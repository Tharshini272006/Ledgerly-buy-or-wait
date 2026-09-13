export const profile = {
  userId: "user_27",
  name: "Tharshini",
  currency: "ZAR",
  balance: 93141.8,
  minimum: 20500,
  priorities: ["education", "emergency_savings"],
  protected: ["rent", "groceries", "transport"],
  flexible: [],
  stop: ["delivery_membership"],
};

export const requests = [
  { id: "request_27", title: "New laptop", type: "Purchase", amount: 6670, due: "21 Aug 2026", date: "2026-07-05", status: "affordable_now", method: "full_payment", safe: 6670, balance: 93141.8, minimum: 20500, currency: "ZAR", earliest: "2026-07-05", plan: "2026-07-05:6,670", explanation: "Pay ZAR 6670 today while staying above the ZAR 20500 minimum over 90 days." },
  { id: "request_26", title: "Family transfer", type: "Family transfer", amount: 15656000, due: "07 Oct 2025", date: "2025-08-03", status: "affordable_now", method: "full_payment", safe: 15656000, balance: 100845250, minimum: 24768300, currency: "IDR", earliest: "2025-08-03", plan: "2025-08-03:15,656,000", explanation: "Pay IDR 15656000 today while staying above the IDR 24768300 minimum over 90 days." },
  { id: "request_28", title: "Investment contribution", type: "Investment", amount: 310.7, due: "15 Jun 2024", date: "2024-06-07", status: "not_affordable", method: "not_recommended", safe: 310.7, balance: 1789.4, minimum: 1100, currency: "EUR", earliest: "", plan: "none", explanation: "Only EUR 310.7 is safe on 2024-06-07, and no allowed plan keeps the balance above the EUR 1100 minimum within 90 days." },
];

export const cashFlow = [
  { month: "Jul", income: 18, spending: 12, balance: 72 },
  { month: "Aug", income: 25, spending: 16, balance: 78 },
  { month: "Sep", income: 22, spending: 19, balance: 74 },
  { month: "Oct", income: 30, spending: 17, balance: 86 },
  { month: "Nov", income: 23, spending: 21, balance: 82 },
  { month: "Dec", income: 28, spending: 18, balance: 91 },
];

export const history = [
  { id: "request_01", title: "Laptop purchase", type: "Purchase", amount: "ZAR 25,256", date: "03 Mar 2024", status: "Approved", tone: "good" },
  { id: "request_02", title: "Family trip", type: "Travel", amount: "IDR 46,018,000", date: "05 Aug 2025", status: "Installments", tone: "plan" },
  { id: "request_03", title: "Professional course", type: "Education", amount: "IDR 5,491,000", date: "03 Sep 2019", status: "Wait", tone: "wait" },
  { id: "request_04", title: "Family transfer", type: "Transfer", amount: "IDR 12,693,000", date: "04 Jun 2024", status: "Wait", tone: "wait" },
];
