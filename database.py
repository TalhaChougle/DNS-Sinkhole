"""
Database layer using SQLite.
Handles query logs, blocklists, and statistics.
"""

import sqlite3
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "dns_sinkhole.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist and seed default blocklist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            client_ip TEXT,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS blocklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            category TEXT DEFAULT 'custom',
            reason TEXT DEFAULT '',
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Default settings
    c.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        [
            ("sinkhole_enabled", "true"),
            ("upstream_dns", "8.8.8.8"),
        ]
    )

    # Seed with well-known bad domains for demo
    default_blocked = [
        ("doubleclick.net",       "ads",      "Google Ads tracker"),
        ("ads.google.com",        "ads",      "Google Ads"),
        ("tracking.example.com",  "tracker",  "Generic tracker"),
        ("malware-test.com",      "malware",  "Known malware domain"),
        ("phishing-site.net",     "phishing", "Known phishing domain"),
        ("adserver.example.org",  "ads",      "Ad server"),
        ("analytics.facebook.com","tracker",  "Facebook analytics"),
        ("googlesyndication.com", "ads",      "Google ad syndication"),
        ("amazon-adsystem.com",   "ads",      "Amazon ads"),
        ("scorecardresearch.com", "tracker",  "Scorecard tracker"),
        ("quantserve.com",        "tracker",  "Quantcast tracker"),
        ("c2server-demo.ru",      "malware",  "Demo C2 server"),
    ]
    c.executemany(
        "INSERT OR IGNORE INTO blocklist (domain, category, reason) VALUES (?, ?, ?)",
        default_blocked
    )

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")


def db_log_query(domain, client_ip, action):
    """Log a DNS query to the database."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO query_logs (domain, client_ip, action) VALUES (?, ?, ?)",
            (domain, client_ip, action)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Log error: {e}")


def db_is_blocked(domain):
    """Check if a domain (or its parent domain) is blocked."""
    try:
        conn = get_connection()

        # Check if sinkhole is enabled
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'sinkhole_enabled'"
        ).fetchone()
        if row and row["value"] != "true":
            conn.close()
            return False

        # Check exact match and parent domains
        parts = domain.split(".")
        for i in range(len(parts)):
            candidate = ".".join(parts[i:])
            row = conn.execute(
                "SELECT id FROM blocklist WHERE domain = ?", (candidate,)
            ).fetchone()
            if row:
                conn.close()
                return True

        conn.close()
        return False
    except Exception as e:
        print(f"[DB] Block check error: {e}")
        return False


def db_get_logs(limit=200, filter_action=None, search=None):
    """Return recent query logs."""
    conn = get_connection()
    query = "SELECT * FROM query_logs"
    params = []
    conditions = []

    if filter_action:
        conditions.append("action = ?")
        params.append(filter_action)
    if search:
        conditions.append("domain LIKE ?")
        params.append(f"%{search}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_get_stats():
    """Return aggregate statistics."""
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) as c FROM query_logs").fetchone()["c"]
    blocked = conn.execute(
        "SELECT COUNT(*) as c FROM query_logs WHERE action='BLOCKED'"
    ).fetchone()["c"]
    allowed = total - blocked
    blocklist_count = conn.execute("SELECT COUNT(*) as c FROM blocklist").fetchone()["c"]

    # Top blocked domains
    top_blocked = conn.execute("""
        SELECT domain, COUNT(*) as count FROM query_logs
        WHERE action='BLOCKED'
        GROUP BY domain ORDER BY count DESC LIMIT 5
    """).fetchall()

    # Top queried domains
    top_queried = conn.execute("""
        SELECT domain, COUNT(*) as count FROM query_logs
        GROUP BY domain ORDER BY count DESC LIMIT 5
    """).fetchall()

    # Queries per hour (last 24 hours)
    hourly = conn.execute("""
        SELECT strftime('%H:00', timestamp) as hour, COUNT(*) as count
        FROM query_logs
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour ORDER BY hour
    """).fetchall()

    # Category breakdown
    categories = conn.execute("""
        SELECT b.category, COUNT(*) as count
        FROM query_logs q JOIN blocklist b ON q.domain = b.domain
        WHERE q.action = 'BLOCKED'
        GROUP BY b.category
    """).fetchall()

    conn.close()
    return {
        "total": total,
        "blocked": blocked,
        "allowed": allowed,
        "blocklist_count": blocklist_count,
        "block_rate": round((blocked / total * 100), 1) if total > 0 else 0,
        "top_blocked": [dict(r) for r in top_blocked],
        "top_queried": [dict(r) for r in top_queried],
        "hourly": [dict(r) for r in hourly],
        "categories": [dict(r) for r in categories],
    }


def db_get_blocklist(search=None):
    """Return all blocked domains."""
    conn = get_connection()
    query = "SELECT * FROM blocklist"
    params = []
    if search:
        query += " WHERE domain LIKE ?"
        params.append(f"%{search}%")
    query += " ORDER BY added_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_add_domain(domain, category="custom", reason=""):
    """Add a domain to the blocklist."""
    domain = domain.strip().lower()
    if not re.match(r"^[a-zA-Z0-9.\-]+$", domain):
        return False, "Invalid domain format"
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO blocklist (domain, category, reason) VALUES (?, ?, ?)",
            (domain, category, reason)
        )
        conn.commit()
        conn.close()
        return True, "Domain added"
    except sqlite3.IntegrityError:
        return False, "Domain already in blocklist"
    except Exception as e:
        return False, str(e)


def db_remove_domain(domain_id):
    """Remove a domain from blocklist by ID."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM blocklist WHERE id = ?", (domain_id,))
        conn.commit()
        conn.close()
        return True, "Domain removed"
    except Exception as e:
        return False, str(e)


def db_clear_logs():
    """Clear all query logs."""
    conn = get_connection()
    conn.execute("DELETE FROM query_logs")
    conn.commit()
    conn.close()


def db_get_setting(key):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def db_set_setting(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()
