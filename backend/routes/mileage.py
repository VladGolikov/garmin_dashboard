# backend/routes/mileage.py
from fastapi import APIRouter
from backend.db import get_db_connection
from datetime import datetime, timezone

router = APIRouter()

def get_monthly_stats(conn):
    with conn.cursor() as cur:
        # Текущий и прошлый месяц (с 1-го числа, включая сегодня)
        cur.execute("""
            SELECT
                EXTRACT(YEAR FROM start_time_utc) AS year,
                EXTRACT(MONTH FROM start_time_utc) AS month,
                SUM(distance_km) AS total_km
            FROM activities
            WHERE start_time_utc >= date_trunc('month', now() - interval '1 month')
            GROUP BY year, month
            ORDER BY year, month;
        """)
        rows = cur.fetchall()
        stats = { (r['year'], r['month']): r['total_km'] for r in rows }

        now = datetime.now(timezone.utc)
        current = (now.year, now.month)
        prev = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)

        return {
            "current_month": round(stats.get(current, 0), 2),
            "previous_month": round(stats.get(prev, 0), 2)
        }

def get_weekly_stats(conn):
    with conn.cursor() as cur:
        # Неделя по ISO (понедельник–воскресенье), за последние 12 недель
        cur.execute("""
            SELECT
                DATE_TRUNC('week', start_time_utc) AS week_start,
                SUM(distance_km) AS total_km
            FROM activities
            WHERE start_time_utc >= date_trunc('week', current_date - interval '12 weeks')
            GROUP BY week_start
            ORDER BY week_start;
        """)
        weeks = []
        for row in cur.fetchall():
            weeks.append({
                "week_start": row["week_start"].date().isoformat(),
                "total_km": float(round(row["total_km"], 2))
            })
        return weeks

def get_last_7_days(conn):
    with conn.cursor() as cur:
        # Ровно последние 7 календарных дней, включая сегодня
        cur.execute("""
            SELECT COALESCE(SUM(distance_km), 0) AS total_km
            FROM activities
            WHERE start_time_utc >= date_trunc('day', now() - interval '6 days')
              AND start_time_utc < date_trunc('day', now() + interval '1 day');
        """)
        row = cur.fetchone()
        return float(round(row["total_km"], 2))

def get_current_week(conn):
    with conn.cursor() as cur:
        # С начала текущей ISO-недели (понедельник) до сегодня
        cur.execute("""
            SELECT COALESCE(SUM(distance_km), 0) AS total_km
            FROM activities
            WHERE start_time_utc >= date_trunc('week', now())
              AND start_time_utc < date_trunc('day', now() + interval '1 day');
        """)
        row = cur.fetchone()
        return float(round(row["total_km"], 2))

@router.get("/monthly")
def monthly_stats():
    conn = get_db_connection()
    try:
        return get_monthly_stats(conn)
    finally:
        conn.close()

@router.get("/weekly")
def weekly_stats():
    conn = get_db_connection()
    try:
        return {"weeks": get_weekly_stats(conn)}
    finally:
        conn.close()

@router.get("/last7days")
def last_7_days():
    conn = get_db_connection()
    try:
        return {"km": get_last_7_days(conn)}
    finally:
        conn.close()

@router.get("/current_week")
def current_week():
    conn = get_db_connection()
    try:
        return {"km": get_current_week(conn)}
    finally:
        conn.close()
