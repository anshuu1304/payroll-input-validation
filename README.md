# Payroll Input Validation & Reconciliation (Reconstructed)

A deterministic synthetic payroll-validation demo using Python's standard library and SQLite. This is a reconstruction, not the original Claude project or its claimed audit results.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m payroll.run --size small
python -m payroll.run --size full
pytest -q
```

Full mode generates 3,000 employees across three pay periods. It creates more than 100,000 source transactions (time, allowance, deduction). The default seed is `20261022`.

## Validation rules

- **R01:** time entry exceeds 80 hours.
- **R02:** duplicate allowance type for an employee/pay period.
- **R03:** unapproved time entry.
- **R04:** duplicate leave deduction linked to the same leave record.
- **R05:** payroll gross, deductions, or net differs from an independent aggregate of source tables.

The ground-truth labels are written separately to `reports/ground_truth.json`. The validation module does not read them. Exceptions remain blocking while open; only clean payroll inputs are approved and exported. A unique constraint prevents duplicate exports per payroll input.

## Scope and limitations

This is synthetic demonstration software, not a legal or production payroll engine. It does not implement statutory tax, country-specific overtime, benefits, currency conversion, real identity/approval controls, or bank-file transmission. Approvals are simulated. The 80-hour threshold is a demo rule, not a legal standard. Do not use real employee or payroll data without security, privacy, legal, and accounting review.
