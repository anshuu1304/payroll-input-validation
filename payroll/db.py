import sqlite3
from pathlib import Path

RULES = [
    ("R01", "Excessive hours"),
    ("R02", "Duplicate allowance"),
    ("R03", "Unapproved time"),
    ("R04", "Duplicate leave deduction"),
    ("R05", "Reconciliation mismatch"),
]

def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    return connection

def initialize(connection):
    connection.executescript(Path(__file__).with_name("schema.sql").read_text())
    connection.executemany(
        "INSERT OR IGNORE INTO validation_rule VALUES(?,?,?)",
        [(f"RULE-{code}", code, description) for code, description in RULES],
    )
    connection.commit()
