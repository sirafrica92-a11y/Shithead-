"""Private manual ITIL-style incidents, problems and changes.

Separate, bounded SQLite journal beside (not inside) gameplay rooms.sqlite3.
These are manual owner notes, NOT automatically detected service incidents.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

STATUSES = {
    "incident": ("open", "investigating", "resolved"),
    "problem": ("investigating", "known_error", "resolved"),
    "change": ("planned", "in_progress", "completed", "rolled_back"),
}
PREFIX = {"incident": "INC", "problem": "PRB", "change": "CHG"}


class OperationsStore:
    def __init__(self, path: Path | str | None = None):
        self.lock = threading.RLock()
        self.db: sqlite3.Connection | None = None
        try:
            if path is not None:
                p = Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                location = str(p)
            else:
                location = ":memory:"
            self.db = sqlite3.connect(location, check_same_thread=False, timeout=0.5)
            self.db.execute("PRAGMA busy_timeout=500")
            self.db.execute(
                """CREATE TABLE IF NOT EXISTS owner_ops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL CHECK(kind IN ('incident','problem','change')),
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    created_utc TEXT NOT NULL,
                    updated_utc TEXT NOT NULL
                )"""
            )
            self.db.commit()
        except (sqlite3.Error, OSError):
            self.db = None

    def _db(self):
        if self.db is None:
            raise RuntimeError("Operational log storage unavailable")
        return self.db

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _validate(kind: str, title: str, description: str, status: str):
        if kind not in STATUSES or status not in STATUSES[kind]:
            raise ValueError("Invalid record type or status")
        if (not isinstance(title, str) or not title.strip()
                or len(title) > 120 or any(ord(c) < 32 for c in title)):
            raise ValueError("Enter a title between 1 and 120 characters")
        if (not isinstance(description, str) or len(description) > 1200
                or any(ord(c) < 32 and c not in "\n\t" for c in description)):
            raise ValueError("Description is too long or invalid")

    @staticmethod
    def _as_dict(row):
        id_, kind, title, description, status, created, updated = row
        return {
            "id": id_, "reference": f"{PREFIX[kind]}-{id_:04d}",
            "kind": kind, "title": title, "description": description,
            "status": status, "created_utc": created, "updated_utc": updated,
        }

    def list(self, limit: int = 50):
        if not 1 <= limit <= 100:
            raise ValueError("Invalid limit")
        with self.lock:
            try:
                rows = self._db().execute(
                    """SELECT id,kind,title,description,status,created_utc,updated_utc
                       FROM owner_ops ORDER BY id DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
            except sqlite3.Error as exc:
                raise RuntimeError("Operational log storage unavailable") from exc
        return [self._as_dict(r) for r in rows]

    def create(self, kind: str, title: str, description: str = "", status: str | None = None):
        status = status or STATUSES.get(kind, ("",))[0]
        self._validate(kind, title, description, status)
        when = self._now()
        with self.lock:
            try:
                with self._db() as db:
                    cursor = db.execute(
                        """INSERT INTO owner_ops(kind,title,description,status,created_utc,updated_utc)
                           VALUES(?,?,?,?,?,?)""",
                        (kind, title.strip(), description.strip(), status, when, when),
                    )
                id_ = cursor.lastrowid
                row = self._db().execute(
                    "SELECT id,kind,title,description,status,created_utc,updated_utc FROM owner_ops WHERE id=?",
                    (id_,),
                ).fetchone()
            except sqlite3.Error as exc:
                raise RuntimeError("Operational log storage unavailable") from exc
        return self._as_dict(row)

    def change_status(self, record_id: int, status: str):
        if record_id < 1:
            raise ValueError("Invalid record")
        with self.lock:
            try:
                db = self._db()
                row = db.execute("SELECT kind FROM owner_ops WHERE id=?", (record_id,)).fetchone()
                if row is None:
                    raise LookupError("Record not found")
                if status not in STATUSES[row[0]]:
                    raise ValueError("Invalid status for record type")
                with db:
                    db.execute("UPDATE owner_ops SET status=?, updated_utc=? WHERE id=?",
                               (status, self._now(), record_id))
                result = db.execute(
                    "SELECT id,kind,title,description,status,created_utc,updated_utc FROM owner_ops WHERE id=?",
                    (record_id,),
                ).fetchone()
            except sqlite3.Error as exc:
                raise RuntimeError("Operational log storage unavailable") from exc
        return self._as_dict(result)
