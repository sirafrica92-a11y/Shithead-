"""Privacy-minimal, fail-open counters for the SHITHEAD Games owner dashboard.

Keeps aggregate *daily* counts in a separate SQLite file. Never stores
player names, room codes, seat tokens, IPs, full referrers or identifiers.
Metrics are accepted only from trusted server-side game transitions.

Analytics is observational: an analytics storage error must never break a
match or stop a room being created. Its admin report fails visibly instead
of silently presenting missing metrics as zero.
"""
from __future__ import annotations

import csv
import io
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from server.app.game_catalog import GAMES

LOG = logging.getLogger(__name__)

METRICS = (
    "page_views",
    "rooms_created",
    "players_joined",
    "matches_started",
    "matches_completed",
)
GAME_METRICS = set(METRICS) - {"page_views"}
SOURCES = ("direct", "instagram", "tiktok", "youtube", "facebook",
           "google", "whatsapp", "other")


def traffic_source(*, utm_source: str | None = None,
                   referrer: str | None = None) -> str:
    """Map coarse marketing sources to an allowlist; never retain raw URLs."""
    aliases = {
        "ig": "instagram", "instagram": "instagram",
        "tt": "tiktok", "tiktok": "tiktok",
        "yt": "youtube", "youtube": "youtube",
        "fb": "facebook", "facebook": "facebook",
        "wa": "whatsapp", "whatsapp": "whatsapp",
        "google": "google",
    }
    if utm_source:
        return aliases.get(utm_source.strip().lower()[:32], "other")
    if not referrer:
        return "direct"
    try:
        parsed = urlsplit(referrer[:500])
        hostname = (parsed.hostname or "").lower().strip(".")
    except ValueError:
        return "other"
    if not hostname:
        return "other"
    if hostname == "play.shithead.games":
        return "direct"
    for domain, source in (
        ("instagram.com", "instagram"), ("tiktok.com", "tiktok"),
        ("youtube.com", "youtube"), ("youtu.be", "youtube"),
        ("facebook.com", "facebook"), ("fb.com", "facebook"),
        ("google.com", "google"), ("whatsapp.com", "whatsapp"),
        ("wa.me", "whatsapp"),
    ):
        if hostname == domain or hostname.endswith("." + domain):
            return source
    return "other"


def _utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


class AnalyticsStore:
    """Small isolated daily event counter, safe for the existing one-worker app."""

    def __init__(self, db_path: str | Path | None = None):
        self.lock = threading.RLock()
        self.db: sqlite3.Connection | None = None
        self.problem: str | None = None
        try:
            if db_path is not None:
                path = Path(db_path).expanduser()
                path.parent.mkdir(parents=True, exist_ok=True)
                location = str(path)
            else:
                location = ":memory:"
            db = sqlite3.connect(location, check_same_thread=False, timeout=0.25)
            db.execute("PRAGMA busy_timeout = 250")
            db.execute(
                """CREATE TABLE IF NOT EXISTS analytics_daily (
                     day TEXT NOT NULL,
                     game TEXT NOT NULL,
                     mode TEXT NOT NULL,
                     metric TEXT NOT NULL,
                     source TEXT NOT NULL,
                     total INTEGER NOT NULL DEFAULT 0 CHECK (total >= 0),
                     PRIMARY KEY(day, game, mode, metric, source)
                   )"""
            )
            db.commit()
            self.db = db
        except (OSError, sqlite3.Error) as exc:
            self.problem = type(exc).__name__
            LOG.warning("Analytics storage unavailable: %s", type(exc).__name__)

    @property
    def available(self) -> bool:
        return self.db is not None and self.problem is None

    def record(self, metric: str, *, game: str = "", mode: str = "",
               source: str = "", day: str | None = None) -> bool:
        """Record one *server-confirmed* event. Failure never affects gameplay."""
        if metric not in METRICS:
            raise ValueError("Unrecognised analytics event")
        if metric == "page_views":
            if game or mode or source not in SOURCES:
                raise ValueError("Invalid page-view dimensions")
        elif game not in GAMES or source:
            raise ValueError("Invalid game analytics dimensions")
        if mode not in ("", "partner", "cutthroat") or (
                game != "dominoes" and mode):
            raise ValueError("Invalid analytics game mode")
        when = day if day is not None else _utc_day()
        if not self.available:
            return False
        with self.lock:
            try:
                assert self.db is not None
                with self.db:
                    self.db.execute(
                        """INSERT INTO analytics_daily(day, game, mode, metric, source, total)
                           VALUES (?, ?, ?, ?, ?, 1)
                           ON CONFLICT(day, game, mode, metric, source)
                           DO UPDATE SET total = total + 1""",
                        (when, game, mode, metric, source),
                    )
                return True
            except sqlite3.Error as exc:
                self.problem = type(exc).__name__
                LOG.warning("Analytics write failed: %s", type(exc).__name__)
                return False

    def rows(self, days: int = 30) -> list[tuple[str, str, str, str, str, int]]:
        """Rows contain only coarse aggregate dimensions, not player data."""
        if days not in (0, 7, 30, 90, 365):
            raise ValueError("Invalid analytics reporting period")
        if not self.available:
            raise RuntimeError("Analytics storage is unavailable")
        since = (
            (datetime.now(timezone.utc).date() - timedelta(days=days - 1)).isoformat()
            if days else None
        )
        with self.lock:
            assert self.db is not None
            try:
                if since is None:
                    rows = self.db.execute(
                        """SELECT day, game, mode, metric, source, total
                           FROM analytics_daily ORDER BY day, game, mode, metric, source"""
                    ).fetchall()
                else:
                    rows = self.db.execute(
                        """SELECT day, game, mode, metric, source, total
                           FROM analytics_daily WHERE day >= ?
                           ORDER BY day, game, mode, metric, source""",
                        (since,),
                    ).fetchall()
            except sqlite3.Error as exc:
                self.problem = type(exc).__name__
                LOG.warning("Analytics report failed: %s", type(exc).__name__)
                raise RuntimeError("Analytics storage is unavailable") from exc
        return rows

    def report(self, days: int = 30) -> dict:
        rows = self.rows(days)
        overview = {metric: 0 for metric in METRICS}
        games = {
            game: {
                "key": game, "name": GAMES[game].name,
                "rooms_created": 0, "players_joined": 0,
                "matches_started": 0, "matches_completed": 0,
                "modes": {},
            }
            for game in GAMES
        }
        referrals = {source: 0 for source in SOURCES}
        dates: dict[str, dict] = {}
        if days:
            now = datetime.now(timezone.utc).date()
            for i in range(days - 1, -1, -1):
                date_key = (now - timedelta(days=i)).isoformat()
                dates[date_key] = {
                    "date": date_key, "page_views": 0,
                    "rooms_created": 0, "matches_started": 0,
                    "matches_completed": 0,
                }

        for date_key, game, mode, metric, source, amount in rows:
            overview[metric] += amount
            day_entry = dates.setdefault(date_key, {
                "date": date_key, "page_views": 0, "rooms_created": 0,
                "matches_started": 0, "matches_completed": 0,
            })
            if metric in day_entry:
                day_entry[metric] += amount
            if metric == "page_views":
                referrals[source] += amount
            else:
                target = games[game]
                target[metric] += amount
                if game == "dominoes":
                    group = target["modes"].setdefault(mode or "partner", {
                        "rooms_created": 0, "players_joined": 0,
                        "matches_started": 0, "matches_completed": 0,

                    })
                    group[metric] += amount
        ordered_games = sorted(
            games.values(),
            key=lambda item: (-item["matches_started"],
                              -item["rooms_created"], item["name"]),
        )
        return {
            "period_days": days,
            "timezone": "UTC",
            "available_from": rows[0][0] if rows else None,
            "overview": overview,
            "games": ordered_games,
            "sources": [
                {"source": name, "page_views": count}
                for name, count in sorted(referrals.items(), key=lambda x: (-x[1], x[0]))
            ],
            "daily": [dates[k] for k in sorted(dates)],
            "notes": {
                "page_views": "Homepage loads, including repeat loads and possible bots; not unique people.",
                "matches_started": "Server-confirmed game starts (including rematches/restarts), not visits or room creations.",
                "matches_completed": "Server-confirmed completion of a full match, not each domino hand.",
                "privacy": "No cookies, visitor IDs, raw IPs, names, room codes or complete referrer URLs in analytics.",
            },
        }

    def export_csv(self, days: int = 30) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(("date_utc", "game", "mode", "metric", "source", "count"))
        writer.writerows(self.rows(days))
        return out.getvalue()
