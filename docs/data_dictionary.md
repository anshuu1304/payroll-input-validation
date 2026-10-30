# Data dictionary

| Entity | Purpose | Key relationships / safeguards |
|---|---|---|
| `pay_group` | Payroll grouping and currency | Unique group name |
| `employee` | Synthetic employee and hourly rate | FK to pay group; unique tax ID; non-negative rate |
| `pay_period` | Payroll period boundaries | Start date must not exceed end date |
| `time_entry` | Hours submitted for a period | FKs to employee and period; hours 0–100; approval flag |
| `leave_record` | Leave record for an employee and period | FKs to employee and period |
| `allowance` | Employee allowance items | FKs to employee and period; non-negative amount |
| `deduction` | Deduction items | FKs to employee and period; optional FK to leave record |
| `payroll_input` | Calculated gross, deductions, net | Unique employee + period; FKs to employee and period |
| `validation_rule` | Rule catalogue | Unique rule code |
| `exception_record` | Blocking validation findings | FKs to rule, employee and period; unique rule + source record |
| `approval` | Simulated manager approval | FK to payroll input |
| `payroll_export` | Simulated approved export | Unique payroll input; FKs to approval, employee and period |
| `audit_log` | Event history | Additional supporting table; polymorphic entity reference |

Source transaction volume is the sum of `time_entry`, `allowance`, and `deduction`. Leave records are reported separately.
