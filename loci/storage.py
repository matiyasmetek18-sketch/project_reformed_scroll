"""SQLite for one reader: amens, saves, notes, follows, and their quotes."""

import json
import os
import sqlite3
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(path):
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 3000")
    conn.execute("PRAGMA journal_mode = WAL")
    _schema(conn)
    return conn


def _schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS amens (
            quote_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS saves (
            quote_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            quote_id TEXT PRIMARY KEY,
            body TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS follows (
            author TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            author TEXT NOT NULL,
            work TEXT NOT NULL DEFAULT '',
            citation TEXT NOT NULL DEFAULT '',
            year INTEGER,
            latin TEXT NOT NULL DEFAULT '',
            topics TEXT NOT NULL DEFAULT '[]',
            question TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def amen_ids(conn):
    rows = conn.execute("SELECT quote_id FROM amens").fetchall()
    return {row["quote_id"] for row in rows}


def saved_ids(conn):
    rows = conn.execute("SELECT quote_id FROM saves").fetchall()
    return {row["quote_id"] for row in rows}


def notes_map(conn):
    rows = conn.execute("SELECT quote_id, body FROM notes").fetchall()
    return {row["quote_id"]: row["body"] for row in rows}


def followed_authors(conn):
    rows = conn.execute("SELECT author FROM follows").fetchall()
    return {row["author"] for row in rows}


def toggle_amen(conn, quote_id):
    row = conn.execute("SELECT 1 FROM amens WHERE quote_id = ?", (quote_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM amens WHERE quote_id = ?", (quote_id,))
        conn.commit()
        return False
    conn.execute(
        "INSERT INTO amens (quote_id, created_at) VALUES (?, ?)",
        (quote_id, now()),
    )
    conn.commit()
    return True


def set_amen(conn, quote_id, value):
    if value:
        conn.execute(
            "INSERT OR IGNORE INTO amens (quote_id, created_at) VALUES (?, ?)",
            (quote_id, now()),
        )
    else:
        conn.execute("DELETE FROM amens WHERE quote_id = ?", (quote_id,))
    conn.commit()
    return bool(value)


def toggle_save(conn, quote_id):
    row = conn.execute("SELECT 1 FROM saves WHERE quote_id = ?", (quote_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM saves WHERE quote_id = ?", (quote_id,))
        conn.commit()
        return False
    conn.execute(
        "INSERT INTO saves (quote_id, created_at) VALUES (?, ?)",
        (quote_id, now()),
    )
    conn.commit()
    return True


def set_note(conn, quote_id, body):
    text = (body or "").strip()
    if not text:
        conn.execute("DELETE FROM notes WHERE quote_id = ?", (quote_id,))
        conn.commit()
        return ""
    conn.execute(
        """
        INSERT INTO notes (quote_id, body, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(quote_id) DO UPDATE SET body = excluded.body, updated_at = excluded.updated_at
        """,
        (quote_id, text, now()),
    )
    conn.commit()
    return text


def toggle_follow(conn, author):
    row = conn.execute("SELECT 1 FROM follows WHERE author = ?", (author,)).fetchone()
    if row:
        conn.execute("DELETE FROM follows WHERE author = ?", (author,))
        conn.commit()
        return False
    conn.execute(
        "INSERT INTO follows (author, created_at) VALUES (?, ?)",
        (author, now()),
    )
    conn.commit()
    return True


def list_user_quotes(conn):
    rows = conn.execute(
        """
        SELECT id, text, author, work, citation, year, latin, topics, question
        FROM user_quotes ORDER BY id
        """
    ).fetchall()
    quotes = []
    for row in rows:
        try:
            topics = json.loads(row["topics"] or "[]")
        except ValueError:
            topics = []
        if not isinstance(topics, list):
            topics = []
        quotes.append(
            {
                "id": "u%d" % row["id"],
                "author": row["author"],
                "work": row["work"] or "",
                "citation": row["citation"] or "",
                "year": row["year"],
                "question": row["question"] or "",
                "text": row["text"],
                "latin": row["latin"] or "",
                "topics": [str(topic) for topic in topics],
                "attribution": "",
                "source_url": "",
                "source_note": "",
                "reader_added": True,
            }
        )
    return quotes


def add_user_quote(conn, fields):
    cur = conn.execute(
        """
        INSERT INTO user_quotes (
            text, author, work, citation, year, latin, topics, question, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fields["text"],
            fields["author"],
            fields.get("work") or "",
            fields.get("citation") or "",
            fields.get("year"),
            fields.get("latin") or "",
            json.dumps(fields.get("topics") or []),
            fields.get("question") or "",
            now(),
        ),
    )
    conn.commit()
    return "u%d" % cur.lastrowid


def delete_user_quote(conn, row_id):
    cur = conn.execute("DELETE FROM user_quotes WHERE id = ?", (row_id,))
    if cur.rowcount != 1:
        conn.rollback()
        return False
    quote_id = "u%d" % row_id
    conn.execute("DELETE FROM amens WHERE quote_id = ?", (quote_id,))
    conn.execute("DELETE FROM saves WHERE quote_id = ?", (quote_id,))
    conn.execute("DELETE FROM notes WHERE quote_id = ?", (quote_id,))
    conn.commit()
    return True
