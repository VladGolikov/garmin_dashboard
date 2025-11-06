#!/usr/bin/env python3
import os
import sys
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import psycopg2
from garminconnect import Garmin
from dotenv import load_dotenv

import os
from pathlib import Path

# Загрузка .env из корня проекта
dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Константы
RUNNING_TYPES = {
    "running", "treadmill_running", "track_running"
}


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "garmin"),
        user=os.getenv("DB_USER", "runner"),
        password=os.getenv("DB_PASS", "securepass123")
    )


def fetch_running_activities(api: Garmin, start_date: datetime) -> List[Dict[str, Any]]:
    """
    Получает все беговые активности с указанной даты.
    """
    logger.info(f"Fetching activities from {start_date.date()} onward...")
    activities = []
    page = 0
    while True:
        try:
            page_data = api.get_activities(start=page * 100, limit=100)
            if not page_data:
                break
            for act in page_data:
                # Обработка activityType — может быть строкой или dict
                act_type_raw = act.get("activityType")
                if isinstance(act_type_raw, dict):
                    act_type = act_type_raw.get("typeKey", "").lower()
                elif isinstance(act_type_raw, str):
                    act_type = act_type_raw.lower()
                else:
                    act_type = ""

                if act_type in RUNNING_TYPES:
                    distance_m = act.get("distance", 0)
                    if distance_m and distance_m > 0:
                        # Парсим дату
                        start_time_gmt = act["startTimeGMT"]
                        if start_time_gmt.endswith("Z"):
                            start_time_gmt = start_time_gmt.replace("Z", "+00:00")
                        start_time = datetime.fromisoformat(start_time_gmt).astimezone(timezone.utc)
                        activities.append({
                            "garmin_activity_id": act["activityId"],
                            "start_time_utc": start_time,
                            "distance_km": round(distance_m / 1000.0, 3)
                        })
            logger.info(f"Fetched page {page + 1} ({len(page_data)} activities)")
            page += 1
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error fetching page {page + 1}: {e}")
            break
    return activities


def save_activities(activities: List[Dict[str, Any]]):
    """
    Сохраняет активности в БД с защитой от дублей.
    """
    if not activities:
        logger.info("No activities to save.")
        return

    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO activities (garmin_activity_id, start_time_utc, distance_km)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (garmin_activity_id) DO NOTHING
                    """,
                    [
                        (act["garmin_activity_id"], act["start_time_utc"], act["distance_km"])
                        for act in activities
                    ]
                )
                logger.info(f"Inserted {cur.rowcount} new activities.")
    finally:
        conn.close()


def main():
    # Инициализация API
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        logger.error("GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env")
        sys.exit(1)

    try:
        api = Garmin(email, password)
        api.login()
        logger.info("Successfully logged in to Garmin Connect.")
    except Exception as e:
        logger.error(f"Login failed: {e}")
        sys.exit(1)

    # Определяем дату начала: самая ранняя активность — 5 лет назад (или с 2020)
    start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # Получаем и сохраняем
    activities = fetch_running_activities(api, start_date)
    logger.info(f"Total running activities found: {len(activities)}")
    save_activities(activities)

    logger.info("Sync completed.")


if __name__ == "__main__":
    main()