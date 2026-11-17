from datetime import datetime
from app.db import fetch_recent_readings
from app.ollama_client import diagnose_live_window


def get_live_dashboard_data() -> dict:
    readings = fetch_recent_readings(limit=160)
    if not readings:
        return {"readings": [], "latest": [], "total_watts": 0.0, "avg_temp": 0.0, "active_alerts": 0}

    latest_by_inv = {}
    for r in readings:
        latest_by_inv[r["inverter_id"]] = r

    latest_list = list(latest_by_inv.values())
    total_watts = round(sum(item["ac_power_watts"] for item in latest_list), 1)
    avg_temp = round(sum(item["panel_temp_c"] for item in latest_list) / len(latest_list), 1)
    active_alerts = sum(1 for item in latest_list if item["status_code"] != "NORMAL")

    return {
        "readings": readings,
        "latest": latest_list,
        "total_watts": total_watts,
        "avg_temp": avg_temp,
        "active_alerts": active_alerts
    }


def run_live_diagnosis() -> dict:
    readings = fetch_recent_readings(limit=24)
    lines = []
    for r in readings[-12:]:
        ts_short = datetime.fromisoformat(r["recorded_at"]).strftime("%H:%M:%S")
        lines.append(
            f"{ts_short} | {r['inverter_id']} | {r['ac_power_watts']}W | "
            f"{r['dc_voltage']}V | {r['panel_temp_c']}C | {r['status_code']}"
        )
    diagnosis = diagnose_live_window("\n".join(lines))
    return {"diagnosis": diagnosis}