import math
import random
import sqlite3
from datetime import datetime, timedelta, timezone
from app.config import SOLAR_DB_PATH

INVERTERS = ["INV-01", "INV-02", "INV-03", "INV-04"]
_tick_counter = 0


def get_connection(db_path=SOLAR_DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _generate_tick_rows(ts: datetime, step: int) -> list[tuple]:
    rng = random.Random()
    rows = []
    wave = max(0.2, math.sin(step / 12.0) * 0.5 + 0.5)
    for idx, inv in enumerate(INVERTERS):
        cloud_factor = 0.55 if (inv == "INV-02" and (step % 15 in (5, 6, 7))) else 1.0
        voltage = round(rng.uniform(365.0, 405.0) * (0.92 if cloud_factor < 1.0 else 1.0), 2)
        current = round((3.0 + 11.0 * wave) * cloud_factor + rng.uniform(-0.4, 0.4), 2)
        power = round(voltage * current * 0.97, 1)
        temp = round(28.0 + 26.0 * wave + (9.5 if inv == "INV-03" and step % 18 > 11 else 0.0) + rng.uniform(-0.5, 0.5), 1)
        status = "THERMAL_WARN" if temp > 58.0 else ("SHADING_DROP" if cloud_factor < 1.0 else "NORMAL")
        rows.append((ts.isoformat(), inv, voltage, current, power, temp, status))
    return rows


def init_db():
    global _tick_counter
    conn = get_connection(SOLAR_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS inverter_readings")
    cursor.execute("""
        CREATE TABLE inverter_readings (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            inverter_id TEXT NOT NULL,
            dc_voltage REAL NOT NULL,
            dc_current REAL NOT NULL,
            ac_power_watts REAL NOT NULL,
            panel_temp_c REAL NOT NULL,
            status_code TEXT NOT NULL
        )
    """)

    now = datetime.now(timezone.utc)
    for i in range(40):
        ts = now - timedelta(seconds=(40 - i) * 2)
        cursor.executemany("""
            INSERT INTO inverter_readings (
                recorded_at, inverter_id, dc_voltage, dc_current,
                ac_power_watts, panel_temp_c, status_code
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, _generate_tick_rows(ts, i))
    _tick_counter = 40

    conn.commit()
    conn.close()


def insert_live_tick():
    global _tick_counter
    conn = get_connection(SOLAR_DB_PATH)
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc)
    cursor.executemany("""
        INSERT INTO inverter_readings (
            recorded_at, inverter_id, dc_voltage, dc_current,
            ac_power_watts, panel_temp_c, status_code
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, _generate_tick_rows(ts, _tick_counter))
    _tick_counter += 1

    cursor.execute("""
        DELETE FROM inverter_readings
        WHERE reading_id NOT IN (
            SELECT reading_id FROM inverter_readings ORDER BY reading_id DESC LIMIT 600
        )
    """)
    conn.commit()
    conn.close()


def fetch_recent_readings(limit: int = 160) -> list[dict]:
    conn = get_connection(SOLAR_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT recorded_at, inverter_id, dc_voltage, dc_current,
               ac_power_watts, panel_temp_c, status_code
        FROM inverter_readings
        ORDER BY reading_id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    rows.reverse()
    return rows