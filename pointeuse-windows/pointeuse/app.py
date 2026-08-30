#!/usr/bin/env python3
"""Pointeuse locale — application web sans dépendance externe.

Lancement : python app.py
Tableau administrateur : http://localhost:8000/admin
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import html
import io
import json
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
from datetime import date, datetime, timedelta
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from zoneinfo import ZoneInfo

APP_NAME = "Présence"
APP_VERSION = "fériés en rouge clair + journal du code admin (30/08/2026)"
DEFAULT_TZ = os.environ.get("APP_TIMEZONE", "Africa/Algiers")
try:
    TZ = ZoneInfo(DEFAULT_TZ)
except Exception:
    TZ = datetime.now().astimezone().tzinfo

DB_PATH = Path("pointeuse.db")
REPORT_DIR = Path("rapports")
SECRET = b""
LOGIN_ATTEMPTS: dict[str, list[float]] = {}
ATTEMPTS_LOCK = threading.Lock()
REPORT_LOCK = threading.Lock()
DAILY_WORK_MINUTES = 7 * 60

CSS = r"""
:root{--ink:#152238;--muted:#64748b;--line:#e5eaf1;--soft:#f5f7fb;--white:#fff;--blue:#185adb;--blue2:#0d47ba;--green:#087a55;--green-bg:#e9f8f1;--red:#b42318;--red-bg:#fff0ee;--amber:#946200;--amber-bg:#fff6d8;--shadow:0 14px 34px rgba(22,34,56,.09);--radius:18px}
*{box-sizing:border-box}html{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);background:#f7f9fc}body{margin:0;min-height:100vh}.shell{max-width:1120px;margin:0 auto;padding:0 24px}.topbar{background:rgba(255,255,255,.94);border-bottom:1px solid var(--line);height:72px;display:flex;align-items:center;position:sticky;top:0;z-index:10}.topbar .shell{display:flex;align-items:center;justify-content:space-between;width:100%}.brand{display:flex;align-items:center;gap:11px;font-weight:800;letter-spacing:-.02em;color:var(--ink);text-decoration:none}.brandmark{width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,#2167e8,#1647ad);display:grid;place-items:center;box-shadow:0 7px 14px rgba(24,90,219,.25)}.brandmark svg{width:21px;height:21px}.navlinks{display:flex;gap:8px;align-items:center}.navlink{color:var(--muted);font-size:14px;font-weight:650;text-decoration:none;padding:9px 12px;border-radius:10px}.navlink:hover{background:var(--soft);color:var(--ink)}main{padding:40px 0 64px}.eyebrow{color:var(--blue);font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.12em}.hero{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:26px}.hero h1{font-size:32px;line-height:1.15;letter-spacing:-.04em;margin:7px 0 5px}.hero p{color:var(--muted);margin:0;line-height:1.55}.card{background:var(--white);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}.padded{padding:26px}.grid{display:grid;gap:18px}.stats{grid-template-columns:repeat(3,1fr);margin-bottom:18px}.stat{padding:20px 22px;display:flex;align-items:center;gap:15px}.stat-icon{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;font-size:19px}.stat-icon.blue{background:#eaf1ff;color:var(--blue)}.stat-icon.green{background:var(--green-bg);color:var(--green)}.stat-icon.red{background:var(--red-bg);color:var(--red)}.stat-label{font-size:13px;color:var(--muted);font-weight:650}.stat-value{font-size:25px;font-weight:800;line-height:1;margin-top:5px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:18px 20px;border-bottom:1px solid var(--line)}.toolbar-left,.toolbar-right,.inline{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.table-wrap{overflow:auto}table{border-collapse:collapse;width:100%}th{font-size:12px;letter-spacing:.055em;text-transform:uppercase;color:var(--muted);text-align:left;padding:14px 20px;background:#fafbfd;border-bottom:1px solid var(--line)}td{padding:17px 20px;border-bottom:1px solid var(--line);font-size:14px}tr:last-child td{border-bottom:0}.weekend-row td{background:#d6dbe3}.person{font-weight:750}.subline{font-size:12px;color:var(--muted);margin-top:5px}.time{font-size:15px;font-weight:750;font-variant-numeric:tabular-nums}.dash{color:#b1bac8}.badge{display:inline-flex;align-items:center;gap:6px;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:800;vertical-align:middle}.badge:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}.absent{background:var(--red-bg);color:var(--red)}.present{background:var(--green-bg);color:var(--green)}.finished{background:#eef2f7;color:#526174}.weekend{background:#eef2f7;color:#526174}.holiday{background:#ffdede;color:#b42318}.leave{background:#f0ebff;color:#6941c6}.pause{background:var(--amber-bg);color:var(--amber)}.btn{appearance:none;border:0;border-radius:11px;padding:11px 15px;font:inherit;font-size:14px;font-weight:750;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:8px;transition:.16s ease}.btn:hover{transform:translateY(-1px)}.btn:active{transform:none}.btn-primary{background:var(--blue);color:white;box-shadow:0 7px 16px rgba(24,90,219,.22)}.btn-primary:hover{background:var(--blue2)}.btn-secondary{background:#edf2fb;color:#29415f}.btn-danger{background:var(--red-bg);color:var(--red)}.btn-ghost{background:transparent;color:var(--muted);border:1px solid var(--line)}.btn-large{min-height:58px;padding:15px 22px;font-size:16px;border-radius:14px;width:100%}.btn[disabled]{opacity:.45;cursor:not-allowed;box-shadow:none;transform:none}.input,.select{width:100%;border:1px solid #d8e0eb;border-radius:11px;background:white;color:var(--ink);padding:11px 12px;font:inherit;font-size:14px;outline:none}.input:focus,.select:focus{border-color:#739bef;box-shadow:0 0 0 3px rgba(24,90,219,.1)}label{display:block;font-size:13px;font-weight:750;margin-bottom:7px}.field{margin-bottom:16px}.help{font-size:12px;color:var(--muted);line-height:1.5;margin-top:7px}.form-row{display:grid;grid-template-columns:1fr 1fr auto;gap:11px;align-items:end}.section-title{font-size:18px;letter-spacing:-.02em;margin:0}.section-subtitle{color:var(--muted);font-size:13px;margin:5px 0 0}.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;margin-bottom:18px}.lower-grid{grid-template-columns:1.5fr 1fr;margin-top:18px;align-items:start}.employee-list{display:grid;gap:8px}.employee-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 13px;border:1px solid var(--line);border-radius:12px}.employee-meta{min-width:0}.employee-name{font-weight:750;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.device-state{font-size:12px;color:var(--muted);margin-top:3px}.row-actions{display:flex;gap:7px}.icon-btn{width:35px;height:35px;padding:0;border-radius:9px}.notice{border-radius:13px;padding:13px 15px;margin-bottom:18px;font-size:13px;font-weight:650;line-height:1.45}.notice-success{background:var(--green-bg);color:var(--green);border:1px solid #c5ebdb}.notice-error{background:var(--red-bg);color:var(--red);border:1px solid #ffd4cf}.notice-info{background:#edf4ff;color:#24519c;border:1px solid #d4e4ff}.login-shell{min-height:calc(100vh - 72px);display:grid;place-items:center;padding:35px 20px}.login-card{width:100%;max-width:420px;padding:30px}.login-card h1{font-size:26px;letter-spacing:-.035em;margin:18px 0 7px}.login-card>p{color:var(--muted);line-height:1.5;margin:0 0 24px}.terminal{max-width:620px;margin:0 auto}.clock{text-align:center;padding:34px 25px 26px}.clock-time{font-size:52px;line-height:1;font-weight:850;letter-spacing:-.055em;font-variant-numeric:tabular-nums}.clock-date{color:var(--muted);margin-top:10px;font-size:14px;text-transform:capitalize}.welcome{padding:25px;border-top:1px solid var(--line)}.welcome h1{font-size:24px;letter-spacing:-.03em;margin:0 0 6px}.welcome p{color:var(--muted);margin:0}.punch-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:22px}.today-status{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:18px;padding:14px;background:var(--soft);border-radius:12px}.today-times{font-size:12px;color:var(--muted);line-height:1.6;text-align:right}.empty{padding:42px 20px;text-align:center;color:var(--muted)}.empty strong{display:block;color:var(--ink);font-size:15px;margin-bottom:5px}.footer-note{text-align:center;color:#8793a4;font-size:12px;margin-top:20px}.danger-zone{border-top:1px solid var(--line);margin-top:22px;padding-top:20px}.modal-note{background:var(--amber-bg);color:var(--amber);border:1px solid #f5dfa1;padding:11px 13px;border-radius:11px;font-size:12px;line-height:1.5}.date-input{width:auto;min-width:145px}.no-js{background:var(--amber-bg);padding:10px;text-align:center;font-size:13px;color:var(--amber)}.admin-layout{max-width:1460px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:238px minmax(0,1fr);gap:26px;align-items:start}.admin-content{min-width:0}.admin-sidebar{position:sticky;top:96px;align-self:start;background:linear-gradient(165deg,#14233c,#0d1728);border-radius:18px;padding:18px 12px;box-shadow:0 18px 38px rgba(15,27,47,.18);max-height:calc(100vh - 116px);overflow:auto}.sidebar-label{padding:4px 12px 13px;color:#7f94b4;font-size:10px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}.side-nav{display:grid;gap:5px}.side-link{display:flex;align-items:center;gap:10px;color:#bdc9dc;text-decoration:none;font-size:13px;font-weight:700;padding:10px 11px;border-radius:11px;transition:.16s ease}.side-link:hover{background:rgba(255,255,255,.08);color:white}.side-link.active{background:#2366df;color:white;box-shadow:0 7px 16px rgba(0,0,0,.18)}.side-icon{width:25px;height:25px;display:grid;place-items:center;border-radius:8px;background:rgba(255,255,255,.08);font-size:13px;flex:0 0 auto}.side-link.active .side-icon{background:rgba(255,255,255,.16)}.side-divider{height:1px;background:rgba(255,255,255,.1);margin:8px 9px}.side-logout{color:#f3b9b4}.section-anchor{scroll-margin-top:96px}@media(max-width:1050px){.admin-layout{grid-template-columns:1fr;padding:0 18px;gap:18px}.admin-sidebar{top:78px;z-index:8;display:flex;align-items:center;overflow-x:auto;max-height:none;padding:9px;border-radius:14px}.sidebar-label{display:none}.side-nav{display:flex;gap:5px}.side-link{white-space:nowrap;padding:8px 10px}.side-divider{width:1px;height:28px;margin:0 4px}.section-anchor{scroll-margin-top:150px}}@media(max-width:760px){.shell{padding:0 15px}.topbar{height:64px}.topbar .navlink.hide-mobile{display:none}main{padding-top:27px}.hero{align-items:flex-start;flex-direction:column}.hero h1{font-size:27px}.stats{grid-template-columns:1fr}.stat{padding:15px 17px}.lower-grid{grid-template-columns:1fr}.form-row{grid-template-columns:1fr}.toolbar{align-items:flex-start;flex-direction:column}.toolbar-right{width:100%}.toolbar-right .btn{flex:1}.date-input{flex:1}.padded{padding:20px}.punch-grid{grid-template-columns:1fr}.clock-time{font-size:45px}th,td{padding-left:15px;padding-right:15px;min-width:132px}th:first-child,td:first-child{min-width:180px}.login-card{padding:24px}.navlinks{gap:2px}.leave-form{grid-template-columns:1fr!important}.admin-layout{padding:0 12px}.admin-sidebar{top:68px}.side-icon{display:none}.side-link{font-size:12px}}

"""

LOGO = """<span class="brandmark" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M12 6v6l4 2" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="8" stroke="white" stroke-width="2.2"/></svg></span>"""



def now_local() -> datetime:
    return datetime.now(TZ)


def today_iso() -> str:
    return now_local().date().isoformat()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def pin_digest(pin: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 180_000).hex()


def new_pin_values(pin: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    return salt.hex(), pin_digest(pin, salt)


def init_db(demo: bool = False) -> None:
    with db() as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                start_date TEXT,
                pin_salt TEXT,
                pin_hash TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL UNIQUE,
                token_hash TEXT NOT NULL UNIQUE,
                associated_at TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                work_date TEXT NOT NULL,
                arrival_at TEXT,
                break_start_at TEXT,
                break_end_at TEXT,
                departure_at TEXT,
                UNIQUE(employee_id, work_date),
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            );
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holiday_date TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS employee_leaves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                label TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(work_date);
            CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(holiday_date);
            CREATE INDEX IF NOT EXISTS idx_leaves_dates ON employee_leaves(start_date,end_date);
            """
        )
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(employees)")}
        if "start_date" not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN start_date TEXT")
        if "pin_salt" not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN pin_salt TEXT")
        if "pin_hash" not in columns:
            conn.execute("ALTER TABLE employees ADD COLUMN pin_hash TEXT")
        conn.execute("UPDATE employees SET start_date=substr(created_at,1,10) WHERE start_date IS NULL OR start_date='' ")
        attendance_columns = {r["name"] for r in conn.execute("PRAGMA table_info(attendance)")}
        if "break_start_at" not in attendance_columns:
            conn.execute("ALTER TABLE attendance ADD COLUMN break_start_at TEXT")
        if "break_end_at" not in attendance_columns:
            conn.execute("ALTER TABLE attendance ADD COLUMN break_end_at TEXT")
        existing = conn.execute("SELECT value FROM settings WHERE key='pin_salt'").fetchone()
        if not existing:
            salt_hex, digest = new_pin_values(os.environ.get("APP_ADMIN_PIN", "1234"))
            conn.execute("INSERT INTO settings(key,value) VALUES('pin_salt',?)", (salt_hex,))
            conn.execute("INSERT INTO settings(key,value) VALUES('pin_hash',?)", (digest,))
        if demo and conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            stamp = now_local().isoformat(timespec="seconds")
            demo_start = now_local().date().replace(day=1).isoformat()
            for first, last, pin in [("Amine", "Benali", "1111"), ("Sarah", "Mansouri", "2222"), ("Yacine", "Haddad", "3333")]:
                salt_hex, digest = new_pin_values(pin)
                conn.execute(
                    "INSERT INTO employees(first_name,last_name,start_date,pin_salt,pin_hash,created_at) VALUES(?,?,?,?,?,?)",
                    (first, last, demo_start, salt_hex, digest, stamp),
                )
            # Deux jours fériés d’exemple pour voir le surlignage orange du rapport.
            demo_day = now_local().date()
            for offset, demo_label in ((-3, "Mawlid Ennabawi"), (3, "Aïd El Adha")):
                conn.execute(
                    "INSERT OR IGNORE INTO holidays(holiday_date,label) VALUES(?,?)",
                    ((demo_day + timedelta(days=offset)).isoformat(), demo_label),
                )


def verify_pin(pin: str) -> bool:
    with db() as conn:
        values = {r["key"]: r["value"] for r in conn.execute("SELECT key,value FROM settings WHERE key IN ('pin_salt','pin_hash')")}
    if "pin_salt" not in values or "pin_hash" not in values:
        return False
    attempt = pin_digest(pin, bytes.fromhex(values["pin_salt"]))
    return hmac.compare_digest(attempt, values["pin_hash"])


def set_pin(pin: str) -> None:
    salt_hex, digest = new_pin_values(pin)
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('pin_salt',?)", (salt_hex,))
        conn.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('pin_hash',?)", (digest,))


def admin_journal(event: str) -> None:
    """Note chaque changement du code admin dans journal_admin.txt.

    Le patron garde ainsi une trace datée de toute modification du code,
    avec le nouveau code en clair et le PC utilisé, même si quelqu’un
    d’autre le change avant lui.
    """
    try:
        target = DB_PATH.parent / "journal_admin.txt"
        header = ""
        if not target.exists():
            header = (
                "JOURNAL DU CODE ADMINISTRATEUR\n"
                "(date, heure, PC utilisé, nouveau code).\n"
                + "=" * 60 + "\n"
            )
        with target.open("a", encoding="utf-8") as fh:
            fh.write(header + f"{now_local().strftime('%d/%m/%Y %H:%M:%S')} · {event}\n")
    except Exception as exc:
        print(f"[journal] Impossible d’écrire le journal admin : {exc}")


def set_employee_pin(employee_id: int, pin: str) -> None:
    salt_hex, digest = new_pin_values(pin)
    with db() as conn:
        conn.execute("UPDATE employees SET pin_salt=?,pin_hash=? WHERE id=? AND active=1", (salt_hex, digest, employee_id))


def normalize_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip()).casefold()
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def verify_employee_identity(employee: sqlite3.Row, first: str, last: str, pin: str) -> bool:
    if normalize_name(first) != normalize_name(employee["first_name"]) or normalize_name(last) != normalize_name(employee["last_name"]):
        return False
    if not employee["pin_salt"] or not employee["pin_hash"]:
        return False
    attempt = pin_digest(pin, bytes.fromhex(employee["pin_salt"]))
    return hmac.compare_digest(attempt, employee["pin_hash"])


def load_or_create_secret() -> bytes:
    secret_file = DB_PATH.with_suffix(".secret")
    if secret_file.exists():
        return secret_file.read_bytes()
    value = secrets.token_bytes(32)
    secret_file.write_bytes(value)
    return value


def sign(value: str) -> str:
    signature = hmac.new(SECRET, value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def unsign(value: str) -> str | None:
    try:
        data, signature = value.rsplit(".", 1)
    except ValueError:
        return None
    expected = hmac.new(SECRET, data.encode(), hashlib.sha256).hexdigest()
    return data if hmac.compare_digest(signature, expected) else None


def valid_date(value: str | None, fallback: str | None = None) -> str:
    if not value:
        return fallback or today_iso()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        return fallback or today_iso()


def full_name(row: sqlite3.Row) -> str:
    return f"{row['first_name']} {row['last_name']}"


def fmt_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except ValueError:
        return value[11:16] if len(value) >= 16 else value


def french_date(value: str) -> str:
    names = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    d = datetime.strptime(value, "%Y-%m-%d").date()
    return f"{names[d.weekday()]} {d.day} {months[d.month - 1]} {d.year}"


def short_french_date(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def month_shift(d: date, months: int, day: int) -> date:
    index = d.year * 12 + (d.month - 1) + months
    return date(index // 12, index % 12 + 1, day)


def month_period(reference: date) -> tuple[date, date]:
    """Retourne le premier et le dernier jour réel du mois."""
    start = date(reference.year, reference.month, 1)
    end = month_shift(reference, 1, 1) - timedelta(days=1)
    return start, end


def current_month_period(reference: date | None = None) -> tuple[date, date]:
    return month_period(reference or now_local().date())


def latest_completed_period(reference: date | None = None) -> tuple[date, date]:
    """Mois civil précédent, utilisé pour le rapport final."""
    ref = reference or now_local().date()
    previous = month_shift(ref, -1, 1)
    return month_period(previous)


def date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def day_context(day_iso: str) -> tuple[str | None, bool]:
    with db() as conn:
        holiday = conn.execute("SELECT label FROM holidays WHERE holiday_date=?", (day_iso,)).fetchone()
    d = datetime.strptime(day_iso, "%Y-%m-%d").date()
    return (holiday["label"] if holiday else None), d.weekday() in (4, 5)


def status_info(arrival: str | None, departure: str | None, holiday: str | None = None, weekend: bool = False, leave: str | None = None, break_start: str | None = None, break_end: str | None = None) -> tuple[str, str]:
    if arrival:
        if departure:
            return "Parti", "finished"
        if break_start and not break_end:
            return "En pause", "pause"
        return "Présent", "present"
    if holiday:
        shown = holiday.strip()
        suffix = "…" if len(shown) > 38 else ""
        return f"Jour férié · {shown[:38]}{suffix}", "holiday"
    if weekend:
        return "Week-end", "weekend"
    if leave:
        return "Congé", "leave"
    return "Absent", "absent"


def page(title: str, body: str, *, admin: bool = False, scripts: str = "", simple: bool = False) -> bytes:
    nav = '<a class="navlink" href="/admin/logout">Déconnexion</a>' if admin and not simple else ""
    brand_href = "/admin" if admin else "/"
    doc = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · {APP_NAME}</title><meta name="theme-color" content="#185adb"><link rel="icon" href="/favicon.svg">
<style>{CSS}</style></head><body><noscript><div class="no-js">JavaScript est recommandé pour l’actualisation automatique.</div></noscript>
<header class="topbar"><div class="shell"><a class="brand" href="{brand_href}">{LOGO}<span>{APP_NAME}</span></a><nav class="navlinks">{nav}</nav></div></header>
{body}<script>{scripts}</script></body></html>"""
    return doc.encode("utf-8")


def message_box(kind: str | None, text: str | None) -> str:
    if not text:
        return ""
    allowed = "success" if kind == "success" else "error" if kind == "error" else "info"
    return f'<div class="notice notice-{allowed}" role="status">{html.escape(text)}</div>'


def pdf_escape(value: str) -> bytes:
    raw = value.encode("cp1252", errors="replace")
    return raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class PDFPage:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def text(self, x: float, y: float, value: str, size: float = 9, bold: bool = False, color=(0.10, 0.15, 0.23)) -> None:
        font = "F2" if bold else "F1"
        prefix = f"BT /{font} {size:g} Tf {color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x:.1f} {y:.1f} Td (".encode("ascii")
        self.parts.append(prefix + pdf_escape(value) + b") Tj ET\n")

    def line(self, x1: float, y1: float, x2: float, y2: float, color=(0.86, 0.89, 0.93), width: float = 0.6) -> None:
        self.parts.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} RG {width:.2f} w {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S\n".encode())

    def rect(self, x: float, y: float, w: float, h: float, color) -> None:
        self.parts.append(f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f\n".encode())

    def bytes(self) -> bytes:
        return b"".join(self.parts)


def build_pdf(pages: list[PDFPage]) -> bytes:
    for index, p in enumerate(pages, 1):
        p.text(500, 22, f"Page {index}/{len(pages)}", 8, color=(0.40, 0.45, 0.53))
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    }
    kids = []
    for i, p in enumerate(pages):
        page_no, content_no = 5 + i * 2, 6 + i * 2
        kids.append(f"{page_no} 0 R")
        objects[page_no] = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_no} 0 R >>".encode()
        stream = p.bytes()
        objects[content_no] = f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream"
    objects[2] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()
    max_obj = max(objects)
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * (max_obj + 1)
    for obj_no in range(1, max_obj + 1):
        offsets[obj_no] = len(output)
        output.extend(f"{obj_no} 0 obj\n".encode())
        output.extend(objects[obj_no])
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {max_obj + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for obj_no in range(1, max_obj + 1):
        output.extend(f"{offsets[obj_no]:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


def report_filename(start: date, end: date, provisional: bool = False) -> str:
    suffix = "_provisoire" if provisional else ""
    return f"rapport_presence_{start.isoformat()}_au_{end.isoformat()}{suffix}.pdf"


def report_dataset(start: date, end: date) -> list[dict]:
    with db() as conn:
        employees = conn.execute(
            """SELECT * FROM employees e
               WHERE (active=1 AND COALESCE(start_date,substr(created_at,1,10))<=?)
                  OR EXISTS(SELECT 1 FROM attendance a
                            WHERE a.employee_id=e.id AND a.work_date BETWEEN ? AND ?)
               ORDER BY last_name,first_name""",
            (end.isoformat(), start.isoformat(), end.isoformat()),
        ).fetchall()
        attendance = conn.execute(
            "SELECT * FROM attendance WHERE work_date BETWEEN ? AND ?", (start.isoformat(), end.isoformat())
        ).fetchall()
        holidays = {r["holiday_date"]: r["label"] for r in conn.execute(
            "SELECT * FROM holidays WHERE holiday_date BETWEEN ? AND ?", (start.isoformat(), end.isoformat())
        )}
        leaves = conn.execute(
            """SELECT * FROM employee_leaves
               WHERE start_date<=? AND end_date>?""",
            (end.isoformat(), start.isoformat()),
        ).fetchall()
    attendance_map = {(r["employee_id"], r["work_date"]): r for r in attendance}
    leave_map: dict[tuple[int, str], str] = {}
    for leave in leaves:
        leave_start = max(start, datetime.strptime(leave["start_date"], "%Y-%m-%d").date())
        # end_date est la date de reprise : elle n’est pas incluse dans le congé.
        return_date = datetime.strptime(leave["end_date"], "%Y-%m-%d").date()
        leave_end = min(end, return_date - timedelta(days=1))
        for leave_day in date_range(leave_start, leave_end):
            leave_map[(leave["employee_id"], leave_day.isoformat())] = leave["label"]
    result = []
    today = now_local().date()
    for employee in employees:
        details = []
        employee_start = datetime.strptime(employee["start_date"] or employee["created_at"][:10], "%Y-%m-%d").date()
        totals = {"present": 0, "absent": 0, "weekend": 0, "holiday": 0, "leave": 0, "blank": 0, "minutes": 0, "absence_minutes": 0}
        for d in date_range(start, end):
            iso = d.isoformat()
            row = attendance_map.get((employee["id"], iso))
            arrival = row["arrival_at"] if row else None
            break_start = row["break_start_at"] if row else None
            break_end = row["break_end_at"] if row else None
            departure = row["departure_at"] if row else None
            if arrival:
                status = "Présent"
                totals["present"] += 1
                if departure:
                    try:
                        worked = int((datetime.fromisoformat(departure) - datetime.fromisoformat(arrival)).total_seconds() // 60)
                        if break_start and break_end:
                            worked -= max(0, int((datetime.fromisoformat(break_end) - datetime.fromisoformat(break_start)).total_seconds() // 60))
                        totals["minutes"] += max(0, worked)
                    except ValueError:
                        pass
            elif d < employee_start:
                status = ""
                totals["blank"] += 1
            elif (employee["id"], iso) in leave_map and iso not in holidays and d.weekday() not in (4, 5):
                # Un congé enregistré apparaît immédiatement dans l’aperçu
                # mensuel, même si la date est aujourd’hui ou dans le futur.
                status = f"Congé - {leave_map[(employee['id'], iso)]}"
                totals["leave"] += 1
            elif iso in holidays:
                # Un jour férié s’affiche dès qu’il est enregistré, avec son
                # nom (ex : Mawlid Ennabawi), même si la date est future.
                status = f"Férié - {holidays[iso]}"
                totals["holiday"] += 1
            elif d >= today:
                status = ""
                totals["blank"] += 1
            elif d.weekday() in (4, 5):
                status = "Week-end"
                totals["weekend"] += 1
            else:
                status = "Absent"
                totals["absent"] += 1
                totals["absence_minutes"] += DAILY_WORK_MINUTES
            blank = not status
            details.append({"date": d, "arrival": "" if blank else (fmt_time(arrival) or "—"), "break_start": "" if blank else (fmt_time(break_start) or "—"), "break_end": "" if blank else (fmt_time(break_end) or "—"), "departure": "" if blank else (fmt_time(departure) or "—"), "status": status})
        result.append({"name": full_name(employee), "start_date": employee_start, "totals": totals, "details": details})
    return result


def make_report_pdf(start: date, end: date) -> bytes:
    dataset = report_dataset(start, end)
    pages: list[PDFPage] = []
    for employee in dataset:
        p = PDFPage()
        p.rect(0, 774, 595, 68, (0.09, 0.35, 0.86))
        p.text(40, 808, "Rapport mensuel de présence", 19, True, (1, 1, 1))
        p.text(40, 787, f"Du {short_french_date(start)} au {short_french_date(end)} · Début employé : {short_french_date(employee['start_date'])}", 10, color=(0.90, 0.94, 1))

        # Les heures de pause et de reprise sont affichées avec les pointages.
        p.rect(36, 728, 523, 23, (0.94, 0.96, 0.99))
        headers = [(40, "Nom et prénom"), (178, "Date"), (260, "Arrivée"), (330, "Pause"), (400, "Reprise"), (475, "Sortie")]
        for x, label in headers:
            p.text(x, 736, label, 8, True, (0.30, 0.37, 0.47))

        y = 712
        for detail in employee["details"]:
            is_leave = detail["status"].startswith("Congé")
            is_holiday = detail["status"].startswith("Férié")
            is_weekend = detail["date"].weekday() in (4, 5)
            arrival = "" if detail["arrival"] == "—" else detail["arrival"]
            break_start = "" if detail["break_start"] == "—" else detail["break_start"]
            break_end = "" if detail["break_end"] == "—" else detail["break_end"]
            departure = "" if detail["departure"] == "—" else detail["departure"]
            # Nom du jour férié tel qu’il a été saisi (ex : Mawlid Ennabawi).
            holiday_name = detail["status"].split(" - ", 1)[1].strip() if is_holiday and " - " in detail["status"] else ""
            if is_weekend:
                p.rect(36, y - 5, 523, 16, (0.84, 0.86, 0.89))
            if is_holiday:
                # Le rouge clair du jour férié passe devant le gris du week-end.
                p.rect(36, y - 5, 523, 16, (1.00, 0.88, 0.88))
                arrival, break_start, break_end, departure = "JOUR FÉRIÉ", "", "", ""
            if is_leave:
                # Le violet du congé reste prioritaire sur le gris du week-end.
                p.rect(36, y - 5, 523, 16, (0.96, 0.94, 1.00))
                arrival, break_start, break_end, departure = "CONGÉ", "", "", ""
            holiday_color = (0.41, 0.25, 0.78) if is_leave else (0.70, 0.14, 0.10) if is_holiday else (0.10, 0.15, 0.23)
            p.text(40, y, employee["name"][:23], 7.2, True)
            p.text(178, y, detail["date"].strftime("%d/%m/%Y"), 7.2)
            p.text(272, y, arrival, 7.5, is_leave or is_holiday, holiday_color)
            # Le nom du férié est écrit en rouge sur les colonnes du milieu.
            if is_holiday:
                shown_name = holiday_name if len(holiday_name) <= 48 else holiday_name[:48].rstrip() + "…"
                p.text(342, y, shown_name, 7.5, True, (0.70, 0.14, 0.10))
            p.text(342, y, break_start, 7.5)
            p.text(412, y, break_end, 7.5)
            p.text(492, y, departure, 7.5)
            p.line(36, y - 6, 559, y - 6)
            y -= 18

        # Une seule ligne de total au bas du tableau de chaque employé.
        totals = employee["totals"]
        p.rect(36, y - 34, 523, 38, (0.93, 0.96, 1.00))
        p.text(46, y - 20, "TOTAL", 10, True, (0.05, 0.32, 0.72))
        p.text(135, y - 20, f"Journées travaillées : {totals['present']}", 10, True, (0.05, 0.32, 0.72))
        p.text(365, y - 20, f"Jours d'absence : {totals['absent']}", 10, True, (0.70, 0.14, 0.10))
        p.text(40, 48, "Les week-ends sont en gris, les congés en violet et les jours fériés en rouge clair avec leur nom. Les dates futures sans pointage restent vides.", 7.5, color=(0.40, 0.45, 0.53))
        pages.append(p)

    if not pages:
        p = PDFPage()
        p.rect(0, 762, 595, 80, (0.09, 0.35, 0.86))
        p.text(40, 803, "Rapport mensuel de présence", 22, True, (1, 1, 1))
        p.text(40, 781, f"Du {short_french_date(start)} au {short_french_date(end)}", 10, color=(0.90, 0.94, 1))
        p.text(40, 720, "Aucun employé à afficher pour cette période.", 11, True)
        pages.append(p)
    return build_pdf(pages)


def write_report(start: date, end: date, force: bool = False, provisional: bool = False) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    target = REPORT_DIR / report_filename(start, end, provisional)
    with REPORT_LOCK:
        if force or not target.exists():
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(make_report_pdf(start, end))
            temporary.replace(target)
    return target


def ensure_latest_report(force: bool = False) -> Path:
    """Rapport final du mois précédent."""
    start, end = latest_completed_period()
    return write_report(start, end, force, provisional=False)


def ensure_current_preview(force: bool = False) -> Path:
    """Aperçu du mois courant, avec aujourd’hui et les jours futurs vides."""
    start, end = current_month_period()
    return write_report(start, end, force, provisional=True)


def report_scheduler() -> None:
    while True:
        try:
            now = now_local()
            # Le 1er, finalisation du mois précédent. Du 28 à la fin du mois,
            # l’aperçu courant est actualisé chaque heure.
            ensure_latest_report(now.day == 1)
            if now.day >= 28:
                ensure_current_preview(True)
        except Exception as exc:
            print(f"[rapport] Erreur : {exc}")
        time.sleep(3600)


class AppHandler(BaseHTTPRequestHandler):
    server_version = "Presence/2.0"

    def log_message(self, fmt: str, *args) -> None:
        sys.stdout.write(f"[{self.log_date_time_string()}] {self.client_address[0]} {fmt % args}\n")

    def send_bytes(self, data: bytes, content_type: str = "text/html; charset=utf-8", status: int = 200, headers: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location: str, cookie: str | None = None) -> None:
        headers = {"Location": location}
        if cookie:
            headers["Set-Cookie"] = cookie
        self.send_bytes(b"", status=303, headers=headers)

    def parse_cookies(self) -> cookies.SimpleCookie:
        jar = cookies.SimpleCookie()
        try:
            jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError:
            pass
        return jar

    def cookie_value(self, name: str) -> str | None:
        morsel = self.parse_cookies().get(name)
        return morsel.value if morsel else None

    def form(self) -> dict[str, str]:
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 1_000_000)
        except ValueError:
            length = 0
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return {key: values[-1] for key, values in parse_qs(raw, keep_blank_values=True).items()}

    def admin_session(self) -> tuple[bool, str | None]:
        raw = self.cookie_value("presence_admin")
        data = unsign(raw) if raw else None
        if not data:
            return False, None
        try:
            stamp, csrf = data.split(":", 1)
            if time.time() - int(stamp) > 8 * 3600:
                return False, None
            return True, csrf
        except (ValueError, TypeError):
            return False, None

    def require_admin(self, api: bool = False) -> tuple[bool, str | None]:
        valid, csrf = self.admin_session()
        if not valid:
            if api:
                self.send_json({"error": "Session expirée"}, 401)
            else:
                self.redirect("/admin/login")
            return False, None
        return True, csrf

    def verify_csrf(self, data: dict[str, str], expected: str | None) -> bool:
        return bool(expected and hmac.compare_digest(data.get("csrf", ""), expected))

    def device_employee(self) -> sqlite3.Row | None:
        token = self.cookie_value("presence_device")
        if not token:
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with db() as conn:
            return conn.execute(
                "SELECT e.* FROM devices d JOIN employees e ON e.id=d.employee_id WHERE d.token_hash=? AND e.active=1",
                (token_hash,),
            ).fetchone()

    def send_json(self, obj: object, status: int = 200) -> None:
        self.send_bytes(json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8", status)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
        if route == "/":
            self.employee_home(query)
        elif route == "/setup":
            self.setup_page(query)
        elif route == "/admin":
            self.admin_dashboard(query)
        elif route == "/admin/login":
            self.admin_login_page(query)
        elif route == "/admin/logout":
            self.redirect("/admin/login", "presence_admin=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict")
        elif route == "/admin/data":
            self.admin_data(query)
        elif route == "/admin/export.csv":
            self.export_csv(query)
        elif route == "/admin/report/latest.pdf":
            self.latest_report_pdf()
        elif route == "/admin/report/current.pdf":
            self.current_report_pdf()
        elif re.fullmatch(r"/admin/reports/[A-Za-z0-9_.-]+\.pdf", route):
            self.saved_report_pdf(route)
        elif route == "/health":
            self.send_json({"ok": True, "time": now_local().isoformat(timespec="seconds")})
        elif route == "/favicon.svg":
            svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#185adb"/><circle cx="32" cy="32" r="20" fill="none" stroke="white" stroke-width="6"/><path d="M32 18v15l11 6" fill="none" stroke="white" stroke-width="6" stroke-linecap="round"/></svg>'''
            self.send_bytes(svg, "image/svg+xml")
        else:
            self.send_bytes(page("Page introuvable", '<main><div class="shell"><div class="card padded"><h1>Page introuvable</h1><a class="btn btn-primary" href="/">Retour</a></div></div></main>'), status=404)

    def do_POST(self) -> None:
        route = urlparse(self.path).path.rstrip("/") or "/"
        data = self.form()
        if route == "/punch":
            self.punch(data)
        elif route == "/setup/associate":
            self.associate(data)
        elif route == "/admin/login":
            self.admin_login(data)
        elif route == "/admin/employees":
            self.add_employee(data)
        elif route == "/admin/employee-pin":
            self.change_employee_pin(data)
        elif route == "/admin/employee-start":
            self.change_employee_start(data)
        elif route == "/admin/holidays":
            self.add_holiday(data)
        elif route == "/admin/leaves":
            self.add_leave(data)
        elif re.fullmatch(r"/admin/leaves/\d+/delete", route):
            self.delete_leave(route, data)
        elif re.fullmatch(r"/admin/holidays/\d+/delete", route):
            self.delete_holiday(route, data)
        elif re.fullmatch(r"/admin/employees/\d+/delete", route):
            self.deactivate_employee(route, data)
        elif re.fullmatch(r"/admin/devices/\d+/revoke", route):
            self.revoke_device(route, data)
        elif route == "/admin/pin":
            self.change_pin(data)
        elif route == "/admin/attendance/edit":
            self.edit_attendance(data)
        elif route == "/admin/attendance/reset":
            self.reset_attendance(data)
        else:
            self.send_bytes(page("Page introuvable", "<main><div class='shell'><h1>Page introuvable</h1></div></main>"), status=404)

    def employee_home(self, query: dict[str, str]) -> None:
        employee = self.device_employee()
        if not employee:
            self.setup_page(query)
            return
        date_iso = today_iso()
        with db() as conn:
            attendance = conn.execute("SELECT * FROM attendance WHERE employee_id=? AND work_date=?", (employee["id"], date_iso)).fetchone()
            leave_row = conn.execute("SELECT label FROM employee_leaves WHERE employee_id=? AND start_date<=? AND end_date>? ORDER BY start_date DESC LIMIT 1", (employee["id"], date_iso, date_iso)).fetchone()
        arrival = attendance["arrival_at"] if attendance else None
        break_start = attendance["break_start_at"] if attendance else None
        break_end = attendance["break_end_at"] if attendance else None
        departure = attendance["departure_at"] if attendance else None
        leave_label = leave_row["label"] if leave_row else None
        holiday, weekend = day_context(date_iso)
        status_label, status_class = status_info(arrival, departure, holiday, weekend, leave_label, break_start, break_end)
        can_arrive = not arrival
        can_break_start = bool(arrival and not departure and not break_start)
        can_break_end = bool(break_start and not break_end and not departure)
        can_depart = bool(arrival and not departure and (not break_start or break_end))
        msg = message_box(query.get("type"), query.get("message"))
        context_notice = f'<div class="notice notice-info">Aujourd’hui est un jour férié : {html.escape(holiday)}. Le pointage reste possible si vous travaillez.</div>' if holiday else ('<div class="notice notice-info">Aujourd’hui est un jour de week-end. Le pointage reste possible si vous travaillez.</div>' if weekend else (f'<div class="notice notice-info">Un congé est enregistré aujourd’hui : {html.escape(leave_label)}. Le pointage reste possible si vous travaillez.</div>' if leave_label else ''))
        csrf = sign(f"punch:{employee['id']}:{date_iso}")
        body = f"""<main><div class="shell"><div class="terminal">{msg}{context_notice}<section class="card">
        <div class="clock"><div class="eyebrow">Poste de {html.escape(full_name(employee))}</div><div class="clock-time" id="clock">--:--:--</div><div class="clock-date">{html.escape(french_date(date_iso))}</div></div>
        <div class="welcome"><h1>Pointage employé</h1><p>Saisissez votre identité et votre code personnel avant chaque action.</p>
        <form method="post" action="/punch" autocomplete="off"><input type="hidden" name="csrf" value="{csrf}">
          <div class="grid" style="grid-template-columns:1fr 1fr;gap:12px;margin-top:20px"><div class="field"><label for="first_name">Prénom</label><input class="input" id="first_name" name="first_name" required maxlength="60" autofocus></div><div class="field"><label for="last_name">Nom</label><input class="input" id="last_name" name="last_name" required maxlength="60"></div></div>
          <div class="field"><label for="employee_pin">Code personnel</label><input class="input" id="employee_pin" name="employee_pin" type="password" inputmode="numeric" required maxlength="20" placeholder="••••"></div>
          <div class="punch-grid"><button class="btn btn-primary btn-large" name="action" value="arrival"{' disabled' if not can_arrive else ''}>✓ Pointer l’arrivée</button><button class="btn btn-ghost btn-large" name="action" value="break_start"{' disabled' if not can_break_start else ''}>Ⅱ Début de pause</button><button class="btn btn-secondary btn-large" name="action" value="break_end"{' disabled' if not can_break_end else ''}>▶ Reprendre le travail</button><button class="btn btn-secondary btn-large" name="action" value="departure"{' disabled' if not can_depart else ''}>→ Pointer le départ</button></div>
        </form>
        <div class="today-status"><span class="badge {status_class}">{status_label}</span><div class="today-times">Arrivée : <strong>{fmt_time(arrival) or '—'}</strong><br>Pause : <strong>{fmt_time(break_start) or '—'}</strong><br>Reprise : <strong>{fmt_time(break_end) or '—'}</strong><br>Départ : <strong>{fmt_time(departure) or '—'}</strong></div></div>
        </div></section><p class="footer-note">Ce PC est attribué à {html.escape(full_name(employee))}</p></div></div></main>"""
        scripts = """function tick(){const d=new Date();document.getElementById('clock').textContent=d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit',second:'2-digit'});}tick();setInterval(tick,1000);"""
        self.send_bytes(page("Pointer", body, scripts=scripts))

    def setup_page(self, query: dict[str, str]) -> None:
        current = self.device_employee()
        with db() as conn:
            employees = conn.execute("SELECT e.*, EXISTS(SELECT 1 FROM devices d WHERE d.employee_id=e.id) associated FROM employees e WHERE e.active=1 ORDER BY e.last_name,e.first_name").fetchall()
        options = ''.join(f'<option value="{r["id"]}">{html.escape(full_name(r))}{" — déjà attribué" if r["associated"] else ""}</option>' for r in employees)
        msg = message_box(query.get("type"), query.get("message"))
        if not employees:
            content = f"{msg}<div class='notice notice-info'>Aucun employé n’est disponible. Demandez au responsable de créer les employés depuis son espace d’administration.</div>"
        else:
            current_note = f'<div class="notice notice-info">Ce PC est actuellement attribué à <strong>{html.escape(full_name(current))}</strong>. La nouvelle attribution remplacera l’ancienne.</div>' if current else ""
            content = f"""{msg}{current_note}<form method="post" action="/setup/associate"><div class="field"><label for="employee_id">Employé propriétaire de ce PC</label><select class="select" id="employee_id" name="employee_id" required><option value="">Choisir un employé…</option>{options}</select><div class="help">Cette configuration est protégée par le code administrateur.</div></div><div class="field"><label for="pin">Code administrateur</label><input class="input" id="pin" name="pin" type="password" inputmode="numeric" required placeholder="••••"></div><button class="btn btn-primary btn-large">Attribuer ce PC</button></form>"""
        body = f"""<main class="login-shell"><section class="card login-card">{LOGO}<h1>Première configuration</h1><p>Le responsable effectue cette opération une seule fois sur le PC de l’employé.</p>{content}</section></main>"""
        self.send_bytes(page("Configurer le PC", body, simple=True))

    def punch(self, data: dict[str, str]) -> None:
        employee = self.device_employee()
        if not employee:
            self.redirect("/setup?type=error&message=" + quote("Ce PC n’est pas encore attribué."))
            return
        date_iso = today_iso()
        if not hmac.compare_digest(data.get("csrf", ""), sign(f"punch:{employee['id']}:{date_iso}")):
            self.redirect("/?type=error&message=" + quote("La page a expiré. Réessayez."))
            return
        key = f"punch:{self.client_address[0]}:{employee['id']}"
        now = time.time()
        with ATTEMPTS_LOCK:
            recent = [x for x in LOGIN_ATTEMPTS.get(key, []) if now - x < 300]
            LOGIN_ATTEMPTS[key] = recent
        if len(recent) >= 8:
            self.redirect("/?type=error&message=" + quote("Trop de tentatives incorrectes. Attendez cinq minutes."))
            return
        if not verify_employee_identity(employee, data.get("first_name", ""), data.get("last_name", ""), data.get("employee_pin", "")):
            with ATTEMPTS_LOCK:
                LOGIN_ATTEMPTS.setdefault(key, []).append(now)
            self.redirect("/?type=error&message=" + quote("Nom, prénom ou code personnel incorrect pour ce PC."))
            return
        with ATTEMPTS_LOCK:
            LOGIN_ATTEMPTS.pop(key, None)
        action = data.get("action")
        stamp = now_local().isoformat(timespec="seconds")
        with db() as conn:
            row = conn.execute("SELECT * FROM attendance WHERE employee_id=? AND work_date=?", (employee["id"], date_iso)).fetchone()
            if action == "arrival":
                if row and row["arrival_at"]:
                    msg, kind = "L’arrivée est déjà enregistrée aujourd’hui.", "error"
                else:
                    conn.execute("INSERT INTO attendance(employee_id,work_date,arrival_at) VALUES(?,?,?) ON CONFLICT(employee_id,work_date) DO UPDATE SET arrival_at=excluded.arrival_at", (employee["id"], date_iso, stamp))
                    msg, kind = f"Arrivée de {full_name(employee)} enregistrée à {stamp[11:16]}.", "success"
            elif action == "break_start":
                if not row or not row["arrival_at"]:
                    msg, kind = "Enregistrez d’abord l’arrivée.", "error"
                elif row["departure_at"]:
                    msg, kind = "La journée est déjà terminée.", "error"
                elif row["break_start_at"]:
                    msg, kind = "Le début de pause est déjà enregistré.", "error"
                else:
                    conn.execute("UPDATE attendance SET break_start_at=? WHERE employee_id=? AND work_date=?", (stamp, employee["id"], date_iso))
                    msg, kind = f"Début de pause enregistré à {stamp[11:16]}.", "success"
            elif action == "break_end":
                if not row or not row["break_start_at"]:
                    msg, kind = "Enregistrez d’abord le début de la pause.", "error"
                elif row["break_end_at"]:
                    msg, kind = "La reprise est déjà enregistrée.", "error"
                elif row["departure_at"]:
                    msg, kind = "La journée est déjà terminée.", "error"
                else:
                    conn.execute("UPDATE attendance SET break_end_at=? WHERE employee_id=? AND work_date=?", (stamp, employee["id"], date_iso))
                    msg, kind = f"Reprise du travail enregistrée à {stamp[11:16]}.", "success"
            elif action == "departure":
                if not row or not row["arrival_at"]:
                    msg, kind = "Enregistrez d’abord l’arrivée.", "error"
                elif row["departure_at"]:
                    msg, kind = "Le départ est déjà enregistré aujourd’hui.", "error"
                elif row["break_start_at"] and not row["break_end_at"]:
                    msg, kind = "Enregistrez la reprise du travail avant le départ.", "error"
                else:
                    conn.execute("UPDATE attendance SET departure_at=? WHERE employee_id=? AND work_date=?", (stamp, employee["id"], date_iso))
                    msg, kind = f"Départ de {full_name(employee)} enregistré à {stamp[11:16]}.", "success"
            else:
                msg, kind = "Action inconnue.", "error"
        self.redirect(f"/?type={kind}&message={quote(msg)}")

    def associate(self, data: dict[str, str]) -> None:
        if not verify_pin(data.get("pin", "")):
            self.redirect("/setup?type=error&message=" + quote("Code administrateur incorrect."))
            return
        try:
            employee_id = int(data.get("employee_id", ""))
        except ValueError:
            employee_id = 0
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with db() as conn:
            employee = conn.execute("SELECT * FROM employees WHERE id=? AND active=1", (employee_id,)).fetchone()
            if not employee:
                self.redirect("/setup?type=error&message=" + quote("Employé introuvable."))
                return
            current_token = self.cookie_value("presence_device")
            if current_token:
                conn.execute("DELETE FROM devices WHERE token_hash=?", (hashlib.sha256(current_token.encode()).hexdigest(),))
            conn.execute("DELETE FROM devices WHERE employee_id=?", (employee_id,))
            conn.execute("INSERT INTO devices(employee_id,token_hash,associated_at) VALUES(?,?,?)", (employee_id, token_hash, now_local().isoformat(timespec="seconds")))
        cookie = f"presence_device={token}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Strict"
        self.redirect("/?type=success&message=" + quote(f"Ce PC est maintenant attribué à {full_name(employee)}."), cookie)

    def admin_login_page(self, query: dict[str, str]) -> None:
        valid, _ = self.admin_session()
        if valid:
            self.redirect("/admin")
            return
        msg = message_box(query.get("type"), query.get("message"))
        body = f"""<main class="login-shell"><section class="card login-card">{LOGO}<h1>Administration</h1><p>Consultez les présences, jours fériés et rapports mensuels.</p>{msg}<form method="post" action="/admin/login"><div class="field"><label for="pin">Code administrateur</label><input class="input" id="pin" name="pin" type="password" inputmode="numeric" autofocus required></div><button class="btn btn-primary btn-large">Se connecter</button></form></section></main>"""
        self.send_bytes(page("Connexion", body, admin=True, simple=True))

    def admin_login(self, data: dict[str, str]) -> None:
        ip = "admin:" + self.client_address[0]
        now = time.time()
        with ATTEMPTS_LOCK:
            recent = [x for x in LOGIN_ATTEMPTS.get(ip, []) if now - x < 300]
            LOGIN_ATTEMPTS[ip] = recent
        if len(recent) >= 8:
            self.redirect("/admin/login?type=error&message=" + quote("Trop de tentatives. Attendez cinq minutes."))
            return
        if not verify_pin(data.get("pin", "")):
            with ATTEMPTS_LOCK:
                LOGIN_ATTEMPTS.setdefault(ip, []).append(now)
            self.redirect("/admin/login?type=error&message=" + quote("Code incorrect."))
            return
        with ATTEMPTS_LOCK:
            LOGIN_ATTEMPTS.pop(ip, None)
        value = sign(f"{int(now)}:{secrets.token_urlsafe(18)}")
        self.redirect("/admin", f"presence_admin={value}; Path=/; Max-Age=28800; HttpOnly; SameSite=Strict")

    def attendance_rows(self, day_iso: str) -> list[dict]:
        holiday, weekend = day_context(day_iso)
        with db() as conn:
            rows = conn.execute(
                """SELECT e.id,e.first_name,e.last_name,e.start_date,e.created_at,a.arrival_at,a.break_start_at,a.break_end_at,a.departure_at,
                          (SELECT l.label FROM employee_leaves l
                           WHERE l.employee_id=e.id AND l.start_date<=? AND l.end_date>?
                           ORDER BY l.start_date DESC LIMIT 1) AS leave_label
                   FROM employees e
                   LEFT JOIN attendance a ON a.employee_id=e.id AND a.work_date=?
                   WHERE e.active=1 ORDER BY e.last_name,e.first_name""",
                (day_iso, day_iso, day_iso),
            ).fetchall()
        result = []
        selected_day = datetime.strptime(day_iso, "%Y-%m-%d").date()
        for row in rows:
            employee_start = datetime.strptime(row["start_date"] or row["created_at"][:10], "%Y-%m-%d").date()
            if not row["arrival_at"] and selected_day < employee_start:
                label, css_class = "", ""
            elif not row["arrival_at"] and selected_day >= now_local().date() and not row["leave_label"]:
                label, css_class = "", ""
            else:
                label, css_class = status_info(row["arrival_at"], row["departure_at"], holiday, weekend, row["leave_label"], row["break_start_at"], row["break_end_at"])
            blank = not label
            result.append({"id": row["id"], "name": full_name(row), "arrival": "" if blank else fmt_time(row["arrival_at"]), "break_start": "" if blank else fmt_time(row["break_start_at"]), "break_end": "" if blank else fmt_time(row["break_end_at"]), "departure": "" if blank else fmt_time(row["departure_at"]), "status": label, "status_class": css_class, "weekend": weekend})
        return result

    def admin_dashboard(self, query: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        day_iso = valid_date(query.get("date"))
        rows = self.attendance_rows(day_iso)
        with db() as conn:
            employees = conn.execute("SELECT e.*, EXISTS(SELECT 1 FROM devices d WHERE d.employee_id=e.id) associated FROM employees e WHERE e.active=1 ORDER BY e.last_name,e.first_name").fetchall()
            holidays = conn.execute("SELECT * FROM holidays ORDER BY holiday_date DESC LIMIT 20").fetchall()
            leaves = conn.execute("""SELECT l.*,e.first_name,e.last_name FROM employee_leaves l
                                     JOIN employees e ON e.id=l.employee_id
                                     ORDER BY l.start_date DESC LIMIT 30""").fetchall()
        reports = sorted(REPORT_DIR.glob("rapport_presence_*.pdf"), reverse=True)[:12] if REPORT_DIR.exists() else []
        present_count = sum(1 for r in rows if r["status"] in ("Présent", "En pause"))
        absent_count = sum(1 for r in rows if r["status"] == "Absent")
        arrived_count = sum(1 for r in rows if r["arrival"])
        table_rows = self.render_rows(rows) or '<tr><td colspan="5"><div class="empty"><strong>Aucun employé</strong>Ajoutez votre premier employé ci-dessous.</div></td></tr>'
        employee_items = "".join(self.employee_item(r, csrf or "") for r in employees) or '<div class="empty"><strong>Équipe vide</strong>Les employés ajoutés apparaîtront ici.</div>'
        employee_options = ''.join(f'<option value="{r["id"]}">{html.escape(full_name(r))}</option>' for r in employees)
        holiday_items = ''.join(f'<div class="employee-row"><div><div class="employee-name">{html.escape(r["label"])}</div><div class="device-state">{html.escape(french_date(r["holiday_date"]).capitalize())}</div></div><form method="post" action="/admin/holidays/{r["id"]}/delete"><input type="hidden" name="csrf" value="{csrf}"><button class="btn btn-danger icon-btn" onclick="return confirm(\'Supprimer ce jour férié ?\')">×</button></form></div>' for r in holidays) or '<div class="empty"><strong>Aucun jour férié</strong>Ajoutez-les avec le formulaire.</div>'
        leave_items = ''.join(f'<div class="employee-row"><div><div class="employee-name">{html.escape(full_name(r))} · {html.escape(r["label"])}</div><div class="device-state">Début : {html.escape(r["start_date"])} · Reprise : {html.escape(r["end_date"])}</div></div><form method="post" action="/admin/leaves/{r["id"]}/delete"><input type="hidden" name="csrf" value="{csrf}"><button class="btn btn-danger icon-btn" onclick="return confirm(\'Supprimer ce congé ?\')">×</button></form></div>' for r in leaves) or '<div class="empty"><strong>Aucun congé</strong>Ajoutez une période de congé ci-dessous.</div>'
        report_items = ''.join(f'<div class="employee-row"><div><div class="employee-name">{"Aperçu provisoire" if "_provisoire" in p.stem else "Rapport final"}</div><div class="device-state">{html.escape(p.stem.replace("rapport_presence_", "").replace("_au_", " au ").replace("_provisoire", ""))}</div></div><a class="btn btn-ghost" href="/admin/reports/{quote(p.name)}">PDF</a></div>' for p in reports) or '<div class="empty"><strong>Aucun rapport</strong>Le premier sera créé automatiquement.</div>'
        msg = message_box(query.get("type"), query.get("message"))
        start, end = latest_completed_period()
        current_start, current_end = current_month_period()
        body = f"""<main><div class="admin-layout"><aside class="admin-sidebar" aria-label="Menu administrateur"><div class="sidebar-label">Espace administrateur</div><nav class="side-nav"><a class="side-link active" href="#dashboard"><span class="side-icon">⌂</span>Vue d’ensemble</a><a class="side-link" href="#employees"><span class="side-icon">＋</span>Ajouter un employé</a><a class="side-link" href="#leaves"><span class="side-icon">◇</span>Ajouter un congé</a><a class="side-link" href="#holidays"><span class="side-icon">☆</span>Jours fériés</a><a class="side-link" href="#reports"><span class="side-icon">▤</span>Rapports PDF</a><a class="side-link" href="#corrections"><span class="side-icon">↻</span>Correction des pointages</a><a class="side-link" href="#security"><span class="side-icon">●</span>Modifier le mot de passe</a><div class="side-divider"></div><a class="side-link side-logout" href="/admin/logout"><span class="side-icon">→</span>Déconnexion</a></nav></aside><div class="admin-content">{msg}<div id="dashboard" class="hero section-anchor"><div><div class="eyebrow">Tableau de bord</div><h1>Présences de l’équipe</h1><p id="date-label">{html.escape(french_date(day_iso).capitalize())}</p></div><div class="inline"><a class="btn btn-ghost" href="/admin/report/latest.pdf">Dernier PDF final</a><a class="btn btn-primary" href="/admin/report/current.pdf">Aperçu du mois</a></div></div>
        <section class="grid stats"><div class="card stat"><div class="stat-icon blue">👥</div><div><div class="stat-label">Effectif total</div><div class="stat-value" id="stat-total">{len(rows)}</div></div></div><div class="card stat"><div class="stat-icon green">✓</div><div><div class="stat-label">Actuellement présents</div><div class="stat-value" id="stat-present">{present_count}</div></div></div><div class="card stat"><div class="stat-icon red">!</div><div><div class="stat-label">Absents attendus</div><div class="stat-value" id="stat-absent">{absent_count}</div></div></div></section>
        <section class="card"><div class="toolbar"><div><h2 class="section-title">Feuille de présence</h2><p class="section-subtitle"><span id="stat-arrived">{arrived_count}</span> arrivée(s) enregistrée(s)</p></div><div class="toolbar-right"><input class="input date-input" type="date" id="work-date" value="{day_iso}"><a class="btn btn-ghost" id="export-link" href="/admin/export.csv?date={day_iso}">↓ Exporter CSV</a></div></div><div class="table-wrap"><table><thead><tr><th>Nom et prénom</th><th>Arrivée</th><th>Début pause</th><th>Reprise</th><th>Départ</th></tr></thead><tbody id="attendance-body">{table_rows}</tbody></table></div></section>
        <div class="grid lower-grid"><section id="employees" class="card padded section-anchor"><div class="section-head"><div><h2 class="section-title">Employés et PC attribués</h2><p class="section-subtitle">Définissez le PIN lors de l’ajout, puis configurez son PC.</p></div></div><form method="post" action="/admin/employees"><input type="hidden" name="csrf" value="{csrf}"><div class="grid leave-form" style="grid-template-columns:1fr 1fr 150px 150px;gap:10px"><div><label>Prénom</label><input class="input" name="first_name" required maxlength="60"></div><div><label>Nom</label><input class="input" name="last_name" required maxlength="60"></div><div><label>Date de début</label><input class="input" name="employee_start_date" type="date" value="{today_iso()}" required></div><div><label>PIN personnel</label><input class="input" name="employee_pin" type="password" inputmode="numeric" minlength="4" maxlength="20" required></div></div><button class="btn btn-primary" style="margin-top:12px">+ Ajouter l’employé</button></form><div style="height:18px"></div><div class="employee-list">{employee_items}</div>
        <div class="danger-zone"><h3 class="section-title" style="font-size:15px">Changer un code employé</h3><form class="inline" method="post" action="/admin/employee-pin" style="margin-top:12px"><input type="hidden" name="csrf" value="{csrf}"><select class="select" name="employee_id" required><option value="">Employé…</option>{employee_options}</select><input class="input" name="new_employee_pin" type="password" inputmode="numeric" minlength="4" maxlength="20" required placeholder="Nouveau PIN"><button class="btn btn-secondary">Modifier</button></form><h3 class="section-title" style="font-size:15px;margin-top:18px">Modifier une date de début</h3><form class="inline" method="post" action="/admin/employee-start" style="margin-top:12px"><input type="hidden" name="csrf" value="{csrf}"><select class="select" name="employee_id" required><option value="">Employé…</option>{employee_options}</select><input class="input" name="employee_start_date" type="date" required><button class="btn btn-secondary">Modifier</button></form><div class="help">Toutes les dates antérieures au début seront laissées vides dans le tableau mensuel.</div></div></section>
        <section id="holidays" class="card padded section-anchor"><div class="section-head"><div><h2 class="section-title">Jours fériés</h2><p class="section-subtitle">Vendredi et samedi sont déjà des week-ends.</p></div></div><form method="post" action="/admin/holidays"><input type="hidden" name="csrf" value="{csrf}"><div class="field"><label>Date</label><input class="input" name="holiday_date" type="date" required></div><div class="field"><label>Libellé</label><input class="input" name="label" maxlength="80" required placeholder="Fête nationale"></div><button class="btn btn-primary">+ Ajouter</button></form><div style="height:18px"></div><div class="employee-list">{holiday_items}</div></section></div>
        <section id="leaves" class="card padded section-anchor" style="margin-top:18px"><div class="section-head"><div><h2 class="section-title">Congés des employés</h2><p class="section-subtitle">Les journées ouvrées en congé ne sont pas comptées comme absences.</p></div></div><form method="post" action="/admin/leaves"><input type="hidden" name="csrf" value="{csrf}"><div class="grid leave-form" style="grid-template-columns:1.2fr 1fr 1fr 1.5fr;gap:10px"><div><label>Employé</label><select class="select" name="employee_id" required><option value="">Choisir…</option>{employee_options}</select></div><div><label>Du</label><input class="input" name="start_date" type="date" required></div><div><label>Date de reprise</label><input class="input" name="end_date" type="date" required><div class="help">Cette date est un jour normal de travail.</div></div><div><label>Motif</label><input class="input" name="label" maxlength="80" required placeholder="Congé annuel"></div></div><button class="btn btn-primary" style="margin-top:12px">+ Ajouter le congé</button></form><div style="height:18px"></div><div class="employee-list">{leave_items}</div></section>
        <div class="grid lower-grid"><section id="reports" class="card padded section-anchor"><div class="section-head"><div><h2 class="section-title">Rapports PDF</h2><p class="section-subtitle">Mois civil complet : 28, 29, 30 ou 31 jours selon le calendrier.</p></div></div><div class="notice notice-info">Aperçu courant : du {short_french_date(current_start)} au {short_french_date(current_end)}. Les dates avant le début d’un employé, aujourd’hui et les jours futurs restent vides. Aperçu automatique le 28, rapport final le 1er du mois suivant.</div><div class="inline"><a class="btn btn-primary" href="/admin/report/current.pdf">Télécharger l’aperçu</a><a class="btn btn-secondary" href="/admin/report/latest.pdf">Dernier rapport final</a></div><div style="height:16px"></div><div class="employee-list">{report_items}</div></section>
        <section id="security" class="card padded section-anchor"><div class="section-head"><div><h2 class="section-title">Modifier le mot de passe</h2><p class="section-subtitle">Changez le code d’accès de l’administrateur.</p></div></div><form method="post" action="/admin/pin"><input type="hidden" name="csrf" value="{csrf}"><div class="field"><label>Code administrateur actuel</label><input class="input" name="current_pin" type="password" required></div><div class="field"><label>Nouveau code administrateur</label><input class="input" name="new_pin" type="password" minlength="4" maxlength="20" required></div><button class="btn btn-secondary">Changer le code</button></form><div id="corrections" class="danger-zone section-anchor"><h3 class="section-title" style="font-size:16px">Corriger un pointage</h3><p class="modal-note" style="margin-top:10px">Choisissez l’employé et la date. Pour ajouter ou corriger une heure, indiquez l’heure puis utilisez le bouton correspondant. La suppression permet à l’employé de pointer à nouveau.</p><form method="post" action="/admin/attendance/edit" style="margin-top:14px"><input type="hidden" name="csrf" value="{csrf}"><div class="field"><label>Employé</label><select class="select" name="employee_id" required><option value="">Choisir…</option>{employee_options}</select></div><div class="grid" style="grid-template-columns:1fr 1fr;gap:10px"><div class="field"><label>Date à corriger</label><input class="input" id="correction-date" name="date" type="date" value="{day_iso}" required></div><div class="field"><label>Heure à enregistrer</label><input class="input" name="time_value" type="time" step="60"><div class="help">Nécessaire seulement pour définir une arrivée ou un départ.</div></div></div><div class="grid" style="grid-template-columns:1fr 1fr;gap:8px"><button class="btn btn-primary" name="action" value="set_arrival">Définir l’arrivée</button><button class="btn btn-secondary" name="action" value="set_break_start">Définir la pause</button><button class="btn btn-secondary" name="action" value="set_break_end">Définir la reprise</button><button class="btn btn-secondary" name="action" value="set_departure">Définir le départ</button><button class="btn btn-danger" name="action" value="clear_arrival" onclick="return confirm('Supprimer uniquement l’arrivée ?')">Supprimer l’arrivée</button><button class="btn btn-danger" name="action" value="clear_break_start" onclick="return confirm('Supprimer uniquement le début de pause ?')">Supprimer la pause</button><button class="btn btn-danger" name="action" value="clear_break_end" onclick="return confirm('Supprimer uniquement la reprise ?')">Supprimer la reprise</button><button class="btn btn-danger" name="action" value="clear_departure" onclick="return confirm('Supprimer uniquement le départ ?')">Supprimer le départ</button></div><button class="btn btn-ghost" style="width:100%;margin-top:8px" name="action" value="clear_all" onclick="return confirm('Effacer l’arrivée et le départ ?')">Effacer tous les pointages</button></form></div></section></div>
        <p class="footer-note">Actualisation automatique toutes les 15 secondes · Fuseau : {html.escape(DEFAULT_TZ)}</p></div></div></main>"""
        scripts = r"""
const dateInput=document.getElementById('work-date'),body=document.getElementById('attendance-body');
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function row(r){const blank=!r.status,badge=blank?'':`<div class="subline"><span class="badge ${esc(r.status_class)}">${esc(r.status)}</span></div>`;return `<tr class="${r.weekend?'weekend-row':''}"><td><div class="person">${esc(r.name)}</div>${badge}</td><td><span class="time">${blank?'':esc(r.arrival||'—')}</span></td><td><span class="time">${blank?'':esc(r.break_start||'—')}</span></td><td><span class="time">${blank?'':esc(r.break_end||'—')}</span></td><td><span class="time">${blank?'':esc(r.departure||'—')}</span></td></tr>`}
async function refresh(push=true){const d=dateInput.value;try{const res=await fetch('/admin/data?date='+encodeURIComponent(d),{cache:'no-store'});if(res.status===401){location='/admin/login';return}const x=await res.json();body.innerHTML=x.rows.length?x.rows.map(row).join(''):'<tr><td colspan="5"><div class="empty"><strong>Aucune donnée</strong></div></td></tr>';document.getElementById('stat-total').textContent=x.stats.total;document.getElementById('stat-present').textContent=x.stats.present;document.getElementById('stat-absent').textContent=x.stats.absent;document.getElementById('stat-arrived').textContent=x.stats.arrived;document.getElementById('date-label').textContent=x.date_label;document.getElementById('export-link').href='/admin/export.csv?date='+encodeURIComponent(d);document.getElementById('correction-date').value=d;if(push)history.replaceState({},'', '/admin?date='+encodeURIComponent(d));}catch(e){console.warn(e)}}
dateInput.addEventListener('change',()=>refresh());setInterval(()=>refresh(false),15000);
const sideLinks=[...document.querySelectorAll('.side-link[href^="#"]')];
function activateSideLink(id){sideLinks.forEach(link=>link.classList.toggle('active',link.getAttribute('href')==='#'+id));}
sideLinks.forEach(link=>link.addEventListener('click',()=>activateSideLink(link.getAttribute('href').slice(1))));
if('IntersectionObserver' in window){const sections=sideLinks.map(link=>document.querySelector(link.getAttribute('href'))).filter(Boolean);const observer=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(visible)activateSideLink(visible.target.id);},{rootMargin:'-110px 0px -62% 0px',threshold:[0,.15,.4]});sections.forEach(section=>observer.observe(section));}
"""
        self.send_bytes(page("Tableau de bord", body, admin=True, scripts=scripts))

    def render_rows(self, rows: list[dict]) -> str:
        rendered = []
        for row in rows:
            if row["status"]:
                badge = f'<div class="subline"><span class="badge {row["status_class"]}">{html.escape(row["status"])}</span></div>'
                arrival = html.escape(row["arrival"] or "—")
                break_start = html.escape(row["break_start"] or "—")
                break_end = html.escape(row["break_end"] or "—")
                departure = html.escape(row["departure"] or "—")
            else:
                badge = ""
                arrival = break_start = break_end = departure = ""
            row_class = "weekend-row" if row.get("weekend") else ""
            rendered.append(f'<tr class="{row_class}"><td><div class="person">{html.escape(row["name"])}</div>{badge}</td><td><span class="time">{arrival}</span></td><td><span class="time">{break_start}</span></td><td><span class="time">{break_end}</span></td><td><span class="time">{departure}</span></td></tr>')
        return "".join(rendered)

    def employee_item(self, row: sqlite3.Row, csrf: str) -> str:
        state = "PC attribué" if row["associated"] else "PC non configuré"
        code_state = "Code personnel prêt" if row["pin_hash"] else "Code personnel à définir"
        revoke = f'<form method="post" action="/admin/devices/{row["id"]}/revoke"><input type="hidden" name="csrf" value="{csrf}"><button class="btn btn-ghost icon-btn" title="Dissocier le PC" onclick="return confirm(\'Dissocier ce PC ?\')">↻</button></form>' if row["associated"] else ""
        delete = f'<form method="post" action="/admin/employees/{row["id"]}/delete"><input type="hidden" name="csrf" value="{csrf}"><button class="btn btn-danger icon-btn" title="Retirer" onclick="return confirm(\'Retirer cet employé ? Son historique restera conservé.\')">×</button></form>'
        return f'<div class="employee-row"><div class="employee-meta"><div class="employee-name">{html.escape(full_name(row))}</div><div class="device-state">Début : {html.escape(row["start_date"] or "non défini")} · {state} · {code_state}</div></div><div class="row-actions">{revoke}{delete}</div></div>'

    def admin_data(self, query: dict[str, str]) -> None:
        ok, _ = self.require_admin(api=True)
        if not ok:
            return
        day_iso = valid_date(query.get("date"))
        rows = self.attendance_rows(day_iso)
        self.send_json({"date": day_iso, "date_label": french_date(day_iso).capitalize(), "rows": rows, "stats": {"total": len(rows), "present": sum(r["status"] in ("Présent", "En pause") for r in rows), "absent": sum(r["status"] == "Absent" for r in rows), "arrived": sum(bool(r["arrival"]) for r in rows)}})

    def export_csv(self, query: dict[str, str]) -> None:
        ok, _ = self.require_admin()
        if not ok:
            return
        day_iso = valid_date(query.get("date"))
        rows = self.attendance_rows(day_iso)
        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Nom et prénom", "Heure d'arrivée", "Début de pause", "Reprise", "Heure de départ", "Statut", "Date"])
        for row in rows:
            writer.writerow([row["name"], row["arrival"] or "", row["break_start"] or "", row["break_end"] or "", row["departure"] or "", row["status"], day_iso])
        self.send_bytes(output.getvalue().encode(), "text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="presences-{day_iso}.csv"'})

    def latest_report_pdf(self) -> None:
        ok, _ = self.require_admin()
        if not ok:
            return
        target = ensure_latest_report(True)
        self.send_bytes(target.read_bytes(), "application/pdf", headers={"Content-Disposition": f'attachment; filename="{target.name}"'})

    def current_report_pdf(self) -> None:
        ok, _ = self.require_admin()
        if not ok:
            return
        target = ensure_current_preview(True)
        self.send_bytes(target.read_bytes(), "application/pdf", headers={"Content-Disposition": f'attachment; filename="{target.name}"'})

    def saved_report_pdf(self, route: str) -> None:
        ok, _ = self.require_admin()
        if not ok:
            return
        filename = route.rsplit("/", 1)[-1]
        target = REPORT_DIR / filename
        if not target.is_file() or target.parent.resolve() != REPORT_DIR.resolve():
            self.send_bytes(b"Rapport introuvable", "text/plain; charset=utf-8", 404)
            return
        self.send_bytes(target.read_bytes(), "application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    def add_employee(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        first = re.sub(r"\s+", " ", data.get("first_name", "").strip())[:60]
        last = re.sub(r"\s+", " ", data.get("last_name", "").strip())[:60]
        pin = data.get("employee_pin", "")
        try:
            employee_start = datetime.strptime(data.get("employee_start_date", ""), "%Y-%m-%d").date()
        except ValueError:
            self.redirect("/admin?type=error&message=" + quote("La date de début de l’employé est obligatoire.")); return
        if not first or not last or not (4 <= len(pin) <= 20):
            self.redirect("/admin?type=error&message=" + quote("Nom, prénom, date de début et PIN de 4 à 20 caractères sont obligatoires.")); return
        with db() as conn:
            duplicate = conn.execute("SELECT id FROM employees WHERE lower(first_name)=lower(?) AND lower(last_name)=lower(?) AND active=1", (first, last)).fetchone()
            if duplicate:
                self.redirect("/admin?type=error&message=" + quote("Cet employé existe déjà.")); return
            salt_hex, digest = new_pin_values(pin)
            conn.execute("INSERT INTO employees(first_name,last_name,start_date,pin_salt,pin_hash,created_at) VALUES(?,?,?,?,?,?)", (first, last, employee_start.isoformat(), salt_hex, digest, now_local().isoformat(timespec="seconds")))
        self.redirect("/admin?type=success&message=" + quote(f"{first} {last} a été ajouté(e) avec son code personnel."))

    def change_employee_pin(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        try: employee_id = int(data.get("employee_id", ""))
        except ValueError: employee_id = 0
        pin = data.get("new_employee_pin", "")
        if not (4 <= len(pin) <= 20):
            self.redirect("/admin?type=error&message=" + quote("Le PIN employé doit contenir entre 4 et 20 caractères.")); return
        set_employee_pin(employee_id, pin)
        self.redirect("/admin?type=success&message=" + quote("Le code personnel de l’employé a été modifié."))

    def change_employee_start(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        try:
            employee_id = int(data.get("employee_id", ""))
            employee_start = datetime.strptime(data.get("employee_start_date", ""), "%Y-%m-%d").date()
        except ValueError:
            self.redirect("/admin?type=error&message=" + quote("Employé ou date de début invalide.")); return
        with db() as conn:
            result = conn.execute("UPDATE employees SET start_date=? WHERE id=? AND active=1", (employee_start.isoformat(), employee_id))
            if result.rowcount == 0:
                self.redirect("/admin?type=error&message=" + quote("Employé introuvable.")); return
        self.redirect("/admin?type=success&message=" + quote("La date de début de l’employé a été modifiée."))

    def add_leave(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        try:
            employee_id = int(data.get("employee_id", ""))
            start_date = datetime.strptime(data.get("start_date", ""), "%Y-%m-%d").date()
            end_date = datetime.strptime(data.get("end_date", ""), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            self.redirect("/admin?type=error&message=" + quote("Employé ou dates de congé invalides.")); return
        label = data.get("label", "").strip()[:80]
        if end_date <= start_date:
            self.redirect("/admin?type=error&message=" + quote("La date de reprise doit être après le premier jour de congé.")); return
        if not label:
            self.redirect("/admin?type=error&message=" + quote("Le motif du congé est obligatoire.")); return
        with db() as conn:
            employee = conn.execute("SELECT id FROM employees WHERE id=? AND active=1", (employee_id,)).fetchone()
            if not employee:
                self.redirect("/admin?type=error&message=" + quote("Employé introuvable.")); return
            overlap = conn.execute("SELECT id FROM employee_leaves WHERE employee_id=? AND start_date<? AND end_date>?", (employee_id, end_date.isoformat(), start_date.isoformat())).fetchone()
            if overlap:
                self.redirect("/admin?type=error&message=" + quote("Une période de congé existe déjà pour cet employé à ces dates.")); return
            conn.execute("INSERT INTO employee_leaves(employee_id,start_date,end_date,label,created_at) VALUES(?,?,?,?,?)", (employee_id, start_date.isoformat(), end_date.isoformat(), label, now_local().isoformat(timespec="seconds")))
        try:
            ensure_current_preview(True)
        except Exception as exc:
            print(f"[rapport] Actualisation après congé impossible : {exc}")
        self.redirect("/admin?type=success&message=" + quote(f"Le congé a été ajouté. Le {end_date.strftime('%d/%m/%Y')} est enregistré comme date de reprise et jour normal de travail."))

    def delete_leave(self, route: str, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        leave_id = int(route.split("/")[3])
        with db() as conn:
            conn.execute("DELETE FROM employee_leaves WHERE id=?", (leave_id,))
        try:
            ensure_current_preview(True)
        except Exception as exc:
            print(f"[rapport] Actualisation après suppression impossible : {exc}")
        self.redirect("/admin?type=success&message=" + quote("Le congé a été supprimé et le tableau mensuel a été actualisé."))

    def add_holiday(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        raw_date, label = data.get("holiday_date", ""), data.get("label", "").strip()[:80]
        try: holiday_date = datetime.strptime(raw_date, "%Y-%m-%d").date().isoformat()
        except ValueError:
            self.redirect("/admin?type=error&message=" + quote("Date de jour férié invalide.")); return
        if not label:
            self.redirect("/admin?type=error&message=" + quote("Le nom du jour férié est obligatoire.")); return
        with db() as conn:
            conn.execute("INSERT INTO holidays(holiday_date,label) VALUES(?,?) ON CONFLICT(holiday_date) DO UPDATE SET label=excluded.label", (holiday_date, label))
        self.redirect("/admin?type=success&message=" + quote("Jour férié enregistré."))

    def delete_holiday(self, route: str, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        holiday_id = int(route.split("/")[3])
        with db() as conn: conn.execute("DELETE FROM holidays WHERE id=?", (holiday_id,))
        self.redirect("/admin?type=success&message=" + quote("Jour férié supprimé."))

    def deactivate_employee(self, route: str, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        employee_id = int(route.split("/")[3])
        with db() as conn:
            conn.execute("DELETE FROM devices WHERE employee_id=?", (employee_id,))
            conn.execute("UPDATE employees SET active=0 WHERE id=?", (employee_id,))
        self.redirect("/admin?type=success&message=" + quote("Employé retiré. Son historique est conservé."))

    def revoke_device(self, route: str, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        employee_id = int(route.split("/")[3])
        with db() as conn: conn.execute("DELETE FROM devices WHERE employee_id=?", (employee_id,))
        self.redirect("/admin?type=success&message=" + quote("Le PC a été dissocié."))

    def change_pin(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        current, new = data.get("current_pin", ""), data.get("new_pin", "")
        if not verify_pin(current):
            admin_journal(f"TENTATIVE DE CHANGEMENT REFUSÉE (code actuel incorrect) · PC : {self.client_address[0]}")
            self.redirect("/admin?type=error&message=" + quote("Le code administrateur actuel est incorrect.")); return
        if not (4 <= len(new) <= 20):
            self.redirect("/admin?type=error&message=" + quote("Le nouveau code doit contenir entre 4 et 20 caractères.")); return
        set_pin(new)
        admin_journal(f"CODE ADMINISTRATEUR MODIFIÉ · PC : {self.client_address[0]} · Nouveau code : {new}")
        self.redirect("/admin?type=success&message=" + quote("Le code administrateur a été modifié."))

    def edit_attendance(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok:
            return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        try:
            employee_id = int(data.get("employee_id", ""))
            day_iso = datetime.strptime(data.get("date", ""), "%Y-%m-%d").date().isoformat()
        except (ValueError, TypeError):
            self.redirect("/admin?type=error&message=" + quote("Employé ou date invalide.")); return
        action = data.get("action", "")
        set_actions = {
            "set_arrival": ("arrival_at", "L’arrivée"),
            "set_break_start": ("break_start_at", "Le début de pause"),
            "set_break_end": ("break_end_at", "La reprise"),
            "set_departure": ("departure_at", "Le départ"),
        }
        clear_actions = {
            "clear_arrival": ("arrival_at", "L’arrivée"),
            "clear_break_start": ("break_start_at", "Le début de pause"),
            "clear_break_end": ("break_end_at", "La reprise"),
            "clear_departure": ("departure_at", "Le départ"),
        }
        if action not in set_actions and action not in clear_actions and action != "clear_all":
            self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Action de correction inconnue.")); return

        with db() as conn:
            employee = conn.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
            if not employee:
                self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Employé introuvable.")); return
            row = conn.execute("SELECT * FROM attendance WHERE employee_id=? AND work_date=?", (employee_id, day_iso)).fetchone()

            if action in set_actions:
                time_value = data.get("time_value", "").strip()
                try:
                    corrected = datetime.strptime(f"{day_iso} {time_value}", "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
                except ValueError:
                    self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Indiquez une heure valide avant d’enregistrer.")); return
                column, label = set_actions[action]
                values = {name: (datetime.fromisoformat(row[name]) if row and row[name] else None) for name in ("arrival_at", "break_start_at", "break_end_at", "departure_at")}
                values[column] = corrected
                if values["break_start_at"] and not values["arrival_at"]:
                    self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Définissez d’abord l’arrivée.")); return
                if values["break_end_at"] and not values["break_start_at"]:
                    self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Définissez d’abord le début de pause.")); return
                ordered = [values[name] for name in ("arrival_at", "break_start_at", "break_end_at", "departure_at") if values[name]]
                if any(later < earlier for earlier, later in zip(ordered, ordered[1:])):
                    self.redirect(f"/admin?date={day_iso}&type=error&message=" + quote("Les heures doivent respecter l’ordre : arrivée, pause, reprise, départ.")); return
                conn.execute("INSERT INTO attendance(employee_id,work_date) VALUES(?,?) ON CONFLICT(employee_id,work_date) DO NOTHING", (employee_id, day_iso))
                conn.execute(f"UPDATE attendance SET {column}=? WHERE employee_id=? AND work_date=?", (corrected.isoformat(timespec="seconds"), employee_id, day_iso))
                message = f"{label} de {full_name(employee)} a été enregistré(e) à {time_value}."
            elif action in clear_actions:
                column, label = clear_actions[action]
                conn.execute(f"UPDATE attendance SET {column}=NULL WHERE employee_id=? AND work_date=?", (employee_id, day_iso))
                message = f"{label} de {full_name(employee)} a été supprimé(e). L’employé peut effectuer ce pointage à nouveau."
            else:
                conn.execute("DELETE FROM attendance WHERE employee_id=? AND work_date=?", (employee_id, day_iso))
                message = f"Tous les pointages de {full_name(employee)} ont été supprimés."
            empty = conn.execute("""SELECT id FROM attendance WHERE employee_id=? AND work_date=?
                                    AND arrival_at IS NULL AND break_start_at IS NULL
                                    AND break_end_at IS NULL AND departure_at IS NULL""", (employee_id, day_iso)).fetchone()
            if empty:
                conn.execute("DELETE FROM attendance WHERE id=?", (empty["id"],))
        self.redirect(f"/admin?date={day_iso}&type=success&message=" + quote(message))

    def reset_attendance(self, data: dict[str, str]) -> None:
        ok, csrf = self.require_admin()
        if not ok: return
        if not self.verify_csrf(data, csrf):
            self.redirect("/admin?type=error&message=" + quote("La session a expiré.")); return
        try: employee_id = int(data.get("employee_id", ""))
        except ValueError: employee_id = 0
        day_iso = valid_date(data.get("date"))
        with db() as conn: conn.execute("DELETE FROM attendance WHERE employee_id=? AND work_date=?", (employee_id, day_iso))
        self.redirect(f"/admin?date={day_iso}&type=success&message=" + quote("Les heures ont été remises à zéro."))


def local_ip() -> str:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "ADRESSE-IP-DU-SERVEUR"
    finally:
        sock.close()


def main() -> None:
    global DB_PATH, REPORT_DIR, SECRET
    parser = argparse.ArgumentParser(description="Pointeuse locale simple")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--db", default=os.environ.get("ATTENDANCE_DB", "pointeuse.db"))
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    DB_PATH = Path(args.db).resolve()
    REPORT_DIR = DB_PATH.parent / "rapports"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db(args.demo)
    SECRET = load_or_create_secret()
    try:
        ensure_latest_report(False)
        if now_local().day >= 28:
            ensure_current_preview(False)
    except Exception as exc:
        print(f"[rapport] Génération initiale impossible : {exc}")
    threading.Thread(target=report_scheduler, daemon=True, name="rapports-mensuels").start()
    server = ThreadingHTTPServer((args.host, args.port), AppHandler)
    print("\n" + "=" * 66)
    print(f"  {APP_NAME} est démarrée")
    print(f"  Version : {APP_VERSION}")
    print(f"  Administration : http://localhost:{args.port}/admin")
    print(f"  Adresse pour les PC employés : http://{local_ip()}:{args.port}")
    print("  Code administrateur initial : 1234")
    if args.demo:
        print("  Codes démo : Amine 1111 · Sarah 2222 · Yacine 3333")
    print("  Arrêt : Ctrl+C")
    print("=" * 66 + "\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt de la pointeuse…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

