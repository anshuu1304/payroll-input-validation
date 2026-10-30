# Engineering review and reconstruction notes

## Defects corrected in this reconstruction

1. Replaced employee-by-employee SQL lookups with grouped SQL aggregation for payroll construction.
2. Removed the hard-coded employee-ID suppression from duplicate allowance detection. Baseline allowance types are unique; duplicate rows are detected by grouping on employee, period, and allowance type.
3. Replaced anomaly-tag-driven leave deduction checks with a business-key check for repeated leave deductions tied to the same leave record.
4. Replaced hard-coded reconciliation failures with a comparison of stored payroll input against independently aggregated time, allowance, and deduction source tables.
5. Kept ground-truth labels in a separate generated report; validation logic does not read the labels.
6. Prevented approval/export for any employee-period with an open exception.
7. Added idempotent export and audit behavior, unique payroll input per employee-period, and a unique export per payroll input.
8. Added regression tests for clean baselines, reconciliation tampering, blocking, idempotency, and full-volume generation.

## Verification performed

- Full 3,000-employee, three-period pipeline run.
- 108,025 source transactions generated.
- 10 automated tests passed.
- Two full runs with the same seed produced identical summary and ground-truth files.
- Foreign-key check returned zero violations.
- Zero exports had an open exception; zero duplicate exports; zero missing approvals.
- ZIP archive integrity and a fresh extracted-folder test run passed.

This verification applies only to this reconstructed codebase. It does not verify the original Claude workspace or its separate audit claims.
