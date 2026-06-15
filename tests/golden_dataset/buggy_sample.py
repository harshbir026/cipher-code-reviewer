# This file intentionally contains known issues for evaluation.
# Used by test_golden_dataset.py and test_cwe_detection.py to measure recall.

import pickle
import subprocess

# ── Original 4 functions ──────────────────────────────────────────────────────


def unsafe_deserialize(data: bytes):
    # KNOWN BUG: pickle.loads on untrusted data — CWE-502
    return pickle.loads(data)


def run_command(user_input: str):
    # KNOWN BUG: shell=True with user input = command injection — CWE-78
    subprocess.run(user_input, shell=True)


def divide_numbers(a, b):
    # KNOWN BUG: no zero division check — Bug
    return a / b


def fetch_all_users(conn):
    # KNOWN BUG: SQL injection via f-string — CWE-89
    query = f"SELECT * FROM users WHERE id = {input()}"
    return conn.execute(query)


# ── New CWE-89 (SQL Injection) function ──────────────────────────────────────


def get_user_by_email(conn, email: str):
    # KNOWN BUG: SQL injection via string concatenation — CWE-89
    # Attacker can pass email = "' OR '1'='1" to dump all records
    query = "SELECT * FROM users WHERE email = '" + email + "'"
    return conn.execute(query)


# ── New CWE-79 (XSS) function ─────────────────────────────────────────────────


def render_user_profile(username: str) -> str:
    # KNOWN BUG: XSS — user input embedded directly in HTML without escaping — CWE-79
    # Attacker can pass username = "<script>alert('xss')</script>"
    return f"<div class='profile'>Welcome, {username}!</div>"
