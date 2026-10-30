import random
from datetime import date, timedelta


def seed_data(connection, employee_count=3000, seed=20261022, inject_anomalies=True):
    rng = random.Random(seed)
    groups = [("PG1", "Monthly", "INR"), ("PG2", "Ops", "INR"), ("PG3", "Tech", "INR"), ("PG4", "Support", "INR")]
    periods = []
    for index in range(3):
        start = date(2026, 1, 1) + timedelta(days=30 * index)
        periods.append((f"PP{index + 1}", start.isoformat(), (start + timedelta(days=29)).isoformat()))
    connection.executemany("INSERT INTO pay_group VALUES(?,?,?)", groups)
    connection.executemany("INSERT INTO pay_period VALUES(?,?,?)", periods)
    connection.executemany(
        "INSERT INTO employee VALUES(?,?,?,?,?,1)",
        [(f"EMP{i:06}", groups[(i - 1) % 4][0], f"Employee {i}", f"TAX{i:08}", round(rng.uniform(150, 1200), 2)) for i in range(1, employee_count + 1)],
    )

    time_rows, allowance_rows, deduction_rows, leave_rows = [], [], [], []
    truth = {code: [] for code in ("R01", "R02", "R03", "R04", "R05")}
    for employee_no in range(1, employee_count + 1):
        employee_id = f"EMP{employee_no:06}"
        for period_no in range(1, 4):
            period_id = f"PP{period_no}"
            leave_id = f"LV{employee_no:06}-{period_no}"
            leave_rows.append((leave_id, employee_id, period_id, round(rng.uniform(0, 2), 1), "APPROVED"))
            for week in range(4):
                hours = 90.0 if inject_anomalies and employee_no <= 12 and period_no == 1 and week == 0 else round(rng.uniform(30, 45), 2)
                approved = 0 if inject_anomalies and 13 <= employee_no <= 22 and period_no == 1 and week == 0 else 1
                entry_id = f"TE{employee_no:06}-{period_no}-{week}"
                time_rows.append((entry_id, employee_id, period_id, (date(2026, 1, 1) + timedelta(days=(period_no - 1) * 30 + week * 7)).isoformat(), hours, approved))
                if hours > 80:
                    truth["R01"].append(entry_id)
                if not approved:
                    truth["R03"].append(entry_id)

            types = ["INTERNET", "TRAVEL", "MEAL", "WELLNESS"]
            for index, allowance_type in enumerate(types):
                allowance_rows.append((f"AL{employee_no:06}-{period_no}-{index}", employee_id, period_id, allowance_type, round(rng.uniform(500, 3000), 2)))
            if inject_anomalies and employee_no <= 15 and period_no == 1:
                duplicate_id = f"AL{employee_no:06}-{period_no}-DUP"
                allowance_rows.append((duplicate_id, employee_id, period_id, "MEAL", round(rng.uniform(500, 3000), 2)))
                truth["R02"].append(duplicate_id)

            for index in range(3):
                deduction_rows.append((f"DE{employee_no:06}-{period_no}-{index}", employee_id, period_id, None, "OTHER", round(rng.uniform(100, 1000), 2)))
            deduction_rows.append((f"DE{employee_no:06}-{period_no}-LEAVE", employee_id, period_id, leave_id, "LEAVE", round(rng.uniform(100, 1000), 2)))
            if inject_anomalies and employee_no <= 10 and period_no == 1:
                duplicate_id = f"DE{employee_no:06}-{period_no}-LEAVE-DUP"
                deduction_rows.append((duplicate_id, employee_id, period_id, leave_id, "LEAVE", round(rng.uniform(100, 1000), 2)))
                truth["R04"].append(duplicate_id)

    connection.executemany("INSERT INTO time_entry VALUES(?,?,?,?,?,?)", time_rows)
    connection.executemany("INSERT INTO allowance VALUES(?,?,?,?,?)", allowance_rows)
    connection.executemany("INSERT INTO leave_record VALUES(?,?,?,?,?)", leave_rows)
    connection.executemany("INSERT INTO deduction VALUES(?,?,?,?,?,?)", deduction_rows)
    truth["R05"] = [f"PI-EMP{i:06}-PP1" for i in range(22, min(employee_count, 26) + 1)] if inject_anomalies else []
    connection.commit()
    return {
        "employees": employee_count,
        "time": len(time_rows),
        "allowance": len(allowance_rows),
        "deduction": len(deduction_rows),
        "leave": len(leave_rows),
        "ground_truth": truth,
    }
