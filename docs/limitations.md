# Limitations and risk controls

- Synthetic data and scripted manager approval only; no real payroll, tax, or bank integration.
- The 80-hour threshold is an illustrative validation rule, not a statutory overtime calculation.
- Reconciliation independently aggregates time, allowances, and deductions from source tables; it does not validate the correctness of source-system inputs.
- Open exceptions block export. Export uniqueness and foreign-key constraints provide database-level safeguards.
- Production use requires role-based access, immutable audit controls, encryption, secrets management, backups, monitoring, legal review, and parallel-run reconciliation against an approved payroll system.
