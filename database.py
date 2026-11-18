"""
database.py - Database connection helpers for the Job Application Tracker.

Connection settings come from environment variables so that a password
is never saved in the code (or pushed to GitHub):

    DB_HOST      (default: localhost)
    DB_USER      (default: root)
    DB_PASSWORD  (default: empty)
    DB_NAME      (default: job_tracker)
"""

import json
import os

import mysql.connector

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "job_tracker"),
}


def get_db():
    """Open a new connection to the MySQL database."""
    return mysql.connector.connect(**DB_CONFIG)


def query_all(sql, params=()):
    """Run a SELECT and return every row as a list of dictionaries."""
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def query_one(sql, params=()):
    """Run a SELECT and return the first row (or None if there are no rows)."""
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    """Run an INSERT, UPDATE or DELETE, commit it, and return the new row's id."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def parse_json(value):
    """Turn a JSON column value from MySQL into a Python list/dict.

    Depending on the connector version, JSON columns come back as str,
    bytes, or already-parsed objects, so handle all three.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None
