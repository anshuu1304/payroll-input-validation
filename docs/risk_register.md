# Risk register

| Risk | Severity | Current control | Residual status |
|---|---|---|---|
| Synthetic rules/data may not represent actual payroll law or policy | Critical | Explicitly documented; no real payroll integration | Open; must not be used for production payroll decisions |
| No real authentication or role-based authorization | High | Simulated `PAYROLL_MANAGER` approval only | Open; implement identity, least privilege, and separation of duties before production |
| Audit log entity reference is polymorphic and not a foreign key | Medium | Events are written by the workflow and tied to stable entity IDs | Open; use typed audit references or immutable event store in production |
| Demo validation thresholds may not match company policy | High | Thresholds are explicit in code and documentation | Open; obtain approved policy and jurisdiction-specific review |
| Ground-truth anomalies are deliberately planted | High | Ground truth is isolated from validation and metrics are computed separately | Open; 100% synthetic precision/recall is not evidence of real-world accuracy |
| No encryption, secrets management, backups, or monitoring | High | No secrets or real personal data are included | Open; required before handling real employee data |
| Export is a simulated database record, not a bank/payroll-provider file | High | No external transmission is implemented | Open; require format validation, dual approval, and reconciliation before integration |

## Release recommendation

Suitable as a synthetic technical assessment/demo after reviewing the stated scope. Not approved for live payroll, employee-data processing, statutory calculations, or financial disbursement.
