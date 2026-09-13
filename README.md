# Ledgerly — Financial Decision Intelligence

Ledgerly is a deterministic financial decision system built for HackerRank Orchestrate's **Buy or Wait?** challenge.

It answers a practical question:

> **Can this expense be safely paid, and if not, what is the safest way to complete it?**

Ledgerly evaluates each purchase request against the user's current financial position, future cash flows, recurring commitments, payment options, minimum balance requirement, and permitted spending changes.

The system produces both a structured recommendation and a human-readable explanation.

---

## What Ledgerly Does

For every purchase request, Ledgerly determines:

* how much can safely be paid on the request date;
* whether the request is affordable now, with a plan, later, or not affordable;
* the recommended payment method;
* the exact payment schedule;
* the earliest date the full amount can safely be paid;
* any permitted spending changes required;
* and the financial reasoning behind the decision.

The system is designed to be **deterministic, reproducible, and explainable**.

---

## Decision Pipeline

```text
Financial Profiles
        +
Financial Events
        +
Purchase Requests
        +
Payment Options
        +
Messages / Image Evidence
        +
Exchange Rates
        ↓
Evidence Resolution
        ↓
Financial State Normalization
        ↓
Recurring Pattern Detection
        ↓
Cash-Flow Forecast
        ↓
90-Day Balance Simulation
        ↓
Safe Payment Capacity
        ↓
Earliest Full-Payment Date
        ↓
Payment Plan Generation
        ↓
Candidate Ranking
        ↓
Explainable Recommendation
```

---

## Safety Principle

Ledgerly does not define affordability as simply:

```text
current balance >= purchase price
```

A payment is considered safe only when the resulting payment plan can be completed while maintaining the user's required minimum balance throughout the forecast and continuing to cover projected essential expenses.

This makes the decision sensitive to future financial obligations rather than only today's balance.

---

## Core Decision Logic

### Safe Payment Capacity

The solver evaluates projected cash-flow trajectories and determines the amount that can safely be paid while respecting:

* current available balance;
* minimum balance to keep;
* projected credits and debits;
* recurring income and expenses;
* pending and scheduled transactions;
* payment timing;
* and the 90-day forecast.

### Payment Strategies

Ledgerly can recommend:

```text
full_payment
partial_payment
installments
wait
not_recommended
```

Partial payment is treated as a distinct two-payment plan and must satisfy the supplied challenge conditions.

Installment recommendations use the supplied payment options rather than inventing unsupported schedules.

### Spending Changes

Only eligible flexible recurring expenses can be modified.

The solver supports:

```text
stop:<event_id>
reduce_to:<event_id>:<amount>
```

with the challenge's limits on the number and type of changes.

---

## Financial Evidence

Ledgerly uses the supplied financial evidence to reconstruct the user's state.

Supported inputs include:

* financial profiles;
* historical, pending, and scheduled events;
* payment options;
* exchange rates;
* text messages;
* image-linked financial evidence.

When an event has a missing amount, the implementation resolves it through its supplied linked image evidence instead of silently interpreting the amount as zero.

Messages and images are treated as **evidence**, not executable instructions. Financial decision rules remain controlled by the challenge specification.

---

## Recurring Transactions

Recurring transactions are inferred from historical patterns rather than assuming that every event repeats.

The current model supports recurring detection based on:

* repeated historical occurrences;
* calendar-month cadence;
* stable recurring intervals;
* controlled date tolerance;
* transaction category and direction.

The implementation uses a conservative recurrence model designed to avoid treating isolated transactions as recurring commitments.

---

## Payment Plan Selection

Candidate plans are generated first and then ranked using the challenge's decision priorities.

The ranking considers factors such as:

1. completion by the requested deadline;
2. avoiding unnecessary spending changes;
3. total amount paid;
4. earlier completion;
5. number of payments;
6. payment-option ordering.

This separates **plan validity** from **plan preference**.

---

## Explainability

Every output includes a `decision_explanation` describing the financial reasoning behind the recommendation.

Typical reasoning includes:

* available safe payment capacity;
* projected cash-flow pressure;
* minimum-balance constraint;
* next relevant income or expense;
* payment schedule;
* and required spending changes.

The goal is for the recommendation to be understandable rather than simply returning a label.

---

## Output Schema

The generated `output.csv` contains exactly these columns:

```text
request_id
amount_safe_to_pay
affordability_status
recommended_payment_method
payment_plan
earliest_date_for_full_payment
spending_changes_needed
decision_explanation
```

There is one prediction for every request.

---

## Project Structure

```text
.
├── AGENTS.md
├── README.md
├── problem_statement.md
├── requests.csv
├── output.csv
│
├── code/
│   ├── data/
│   ├── decisions/
│   ├── evidence/
│   ├── forecast/
│   ├── fx/
│   └── main.py
│
├── evaluation/
│   ├── sample_output.csv
│   └── usage_report.md
│
└── frontend/
    ├── components/
    ├── data/
    ├── lib/
    └── ...
```

### Backend

The Python backend contains the financial reasoning engine.

Important modules:

* `code/data/` — dataset loading and indexes
* `code/evidence/` — message/image evidence processing
* `code/forecast/` — cash-flow projection and recurrence logic
* `code/fx/` — supplied exchange-rate conversion
* `code/decisions/` — capacity, plans, ranking, and explanations
* `code/main.py` — solver entry point

### Frontend

The `frontend/` directory contains the Ledgerly dashboard built with React and Vite.

The dashboard visualizes the financial state and recommendation as a financial-intelligence workflow rather than exposing raw CSV output.

---

## Running the Backend

From the repository root:

```bash
python code/main.py --input requests.csv --output output.csv
```

The command generates:

```text
output.csv
```

in the repository root.

---

## Public Regression Test

The repository includes a deterministic regression harness for the 25 solved public examples:

```bash
python code/evaluation/regression.py
```

This compares the solver's public outputs against the supplied sample expectations.

---

## Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

For a production build:

```bash
npm run build
```

---

## Reproducibility

The final decision engine is deterministic and does not require an external financial-data service.

Given the same supplied datasets and configuration, the solver produces reproducible outputs.

No live banking connection or live exchange-rate service is required.

---

## Usage Report

The submission package includes:

```text
evaluation/usage_report.md
```

This documents the model-provider usage and token/cost information required by the challenge.

The report reflects the actual final implementation rather than fabricated API usage.

---

## Submission Artifacts

The final HackerRank submission consists of:

```text
code.zip
output.csv
log.txt
```

### `code.zip`

Contains the runnable solution, README, source code, evaluation utilities, and frontend.

### `output.csv`

Contains one prediction for every evaluation request.

### `log.txt`

Contains the development/agent interaction transcript required by the challenge.

---

## Design Principles

Ledgerly is built around four principles:

### 1. Safety First

Never recommend a payment plan that violates the required financial safety constraints.

### 2. Evidence Driven

Use supplied financial records and evidence instead of unsupported assumptions.

### 3. Deterministic Reasoning

Prefer reproducible decision logic so the same financial state produces the same recommendation.

### 4. Explainable Decisions

Return not only the decision, but also the financial factors that led to it.

---

## Challenge

Built for **HackerRank Orchestrate — Buy or Wait?**

The implementation follows the supplied challenge specification and uses only the provided datasets and rules.
