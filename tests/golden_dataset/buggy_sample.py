# This file intentionally contains known issues for evaluation

import pickle
import subprocess


def unsafe_deserialize(data: bytes):
    # KNOWN BUG: pickle.loads on untrusted data is a security vulnerability
    return pickle.loads(data)


def run_command(user_input: str):
    # KNOWN BUG: shell=True with user input = command injection
    subprocess.run(user_input, shell=True)


def divide_numbers(a, b):
    # KNOWN BUG: no zero division check
    return a / b


def fetch_all_users(conn):
    # KNOWN BUG: SQL injection via string formatting
    query = f"SELECT * FROM users WHERE id = {input()}"
    return conn.execute(query)
