
import argparse
import sys
import time

import clickhouse_connect
import numpy as np

sys.path.insert(0, "../hurtownie_danych_lab-main")
from generate import generate_fleet_data

# Stałe geograficzne (pole Piotrowo)

FIELD_MIN_LAT = 52.4600
FIELD_MAX_LAT = 52.4650
FIELD_MIN_LON = 16.9200
FIELD_MAX_LON = 16.9300

GEOFENCE = {
    "min_lat": FIELD_MIN_LAT + 0.001,
    "max_lat": FIELD_MAX_LAT - 0.001,
    "min_lon": FIELD_MIN_LON + 0.002,
    "max_lon": FIELD_MAX_LON - 0.002,
}

SENSORS = [
    {"sensor_id": 1, "lat": 52.4610, "lon": 16.9220, "threshold": 75.0},
    {"sensor_id": 2, "lat": 52.4625, "lon": 16.9250, "threshold": 60.0},
    {"sensor_id": 3, "lat": 52.4640, "lon": 16.9270, "threshold": 80.0},
    {"sensor_id": 4, "lat": 52.4615, "lon": 16.9280, "threshold": 70.0},
    {"sensor_id": 5, "lat": 52.4635, "lon": 16.9230, "threshold": 65.0},
]

PROXIMITY_RADIUS_M = 15.0
COLLISION_RADIUS_M = 2.0

BATCH_SIZE = 500_000


def get_client():
    return clickhouse_connect.get_client(
        host="localhost", port=8123, username="admin", password="admin"
    )


def drop_and_create_tables(client):
    print("[DDL] Tworzę tabele...")

    client.command("DROP TABLE IF EXISTS robot_positions")
    client.command("""
        CREATE TABLE robot_positions (
            robot_id    UInt32,
            ts          Float64,
            lat         Float64,
            lon         Float64
        )
        ENGINE = MergeTree()
        ORDER BY (robot_id, ts)
        SETTINGS index_granularity = 8192
    """)

    client.command("DROP TABLE IF EXISTS sensors")
    client.command("""
        CREATE TABLE sensors (
            sensor_id   UInt32,
            lat         Float64,
            lon         Float64,
            threshold   Float64
        )
        ENGINE = MergeTree()
        ORDER BY sensor_id
    """)

    client.command("DROP TABLE IF EXISTS sensor_readings")
    client.command("""
        CREATE TABLE sensor_readings (
            sensor_id   UInt32,
            ts          Float64,
            value       Float64      
        )
        ENGINE = MergeTree()
        ORDER BY (sensor_id, ts)
    """)

    client.command("DROP TABLE IF EXISTS geofence_zones")
    client.command("""
        CREATE TABLE geofence_zones (
            zone_id     UInt32,
            min_lat     Float64,
            max_lat     Float64,
            min_lon     Float64,
            max_lon     Float64,
            label       String
        )
        ENGINE = MergeTree()
        ORDER BY zone_id
    """)

    print("[DDL] Tabele gotowe.")


def insert_static_data(client, sim_start: float, sim_end: float):
    print("[STATIC] Wstawiam dane statyczne (czujniki, geofence, odczyty)...")

    client.insert("geofence_zones", [
        [1, GEOFENCE["min_lat"], GEOFENCE["max_lat"],
         GEOFENCE["min_lon"], GEOFENCE["max_lon"], "Pole Piotrowo – strefa dozwolona"]
    ], column_names=["zone_id", "min_lat", "max_lat", "min_lon", "max_lon", "label"])

    sensor_rows = [[s["sensor_id"], s["lat"], s["lon"], s["threshold"]] for s in SENSORS]
    client.insert("sensors", sensor_rows, column_names=["sensor_id", "lat", "lon", "threshold"])

    mid = (sim_start + sim_end) / 2.0
    readings = []
    for s in SENSORS:
        ts = sim_start
        while ts <= sim_end:
            if ts <= mid:
                val = s["threshold"] + np.random.uniform(5, 25)
            else:
                val = s["threshold"] - np.random.uniform(5, 20)
            readings.append([s["sensor_id"], round(ts, 3), round(float(val), 2)])
            ts += 1.0  # co 1 sekundę

    client.insert("sensor_readings", readings, column_names=["sensor_id", "ts", "value"])
    print(f"[STATIC] Wstawiono {len(readings)} odczytów czujników.")


def load_robot_data(client, num_rovers: int, duration: int, freq: int):
    print(f"[DATA] Generuję dane: {num_rovers} robotów, {duration}s, {freq}Hz...")
    t0 = time.perf_counter()
    raw = generate_fleet_data(
        num_rovers=num_rovers,
        duration_sec=duration,
        frequency_hz=freq,
    )
    gen_time = time.perf_counter() - t0
    print(f"[DATA] Wygenerowano {len(raw):,} rekordów w {gen_time:.1f}s")

    print("[DATA] Wstawiam do ClickHouse...")
    t1 = time.perf_counter()
    for i in range(0, len(raw), BATCH_SIZE):
        batch = raw[i : i + BATCH_SIZE]
        client.insert(
            "robot_positions",
            batch,
            column_names=["robot_id", "ts", "lat", "lon"],
        )
        pct = min(100, (i + BATCH_SIZE) / len(raw) * 100)
        print(f"  {pct:.0f}%  ({i + len(batch):,}/{len(raw):,})")

    ins_time = time.perf_counter() - t1
    total = len(raw)
    print(f"[DATA] Insert zakończony: {ins_time:.1f}s ({total/ins_time:,.0f} wierszy/s)")
    return raw


def verify(client):
    cnt = client.command("SELECT count() FROM robot_positions")
    print(f"[VERIFY] robot_positions: {cnt:,} wierszy")
    cnt2 = client.command("SELECT count() FROM sensor_readings")
    print(f"[VERIFY] sensor_readings: {cnt2:,} wierszy")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rovers",   type=int, default=50)
    parser.add_argument("--duration", type=int, default=3600)
    parser.add_argument("--freq",     type=int, default=10)
    args = parser.parse_args()

    client = get_client()
    drop_and_create_tables(client)

    sim_start = 1714398000.0
    sim_end   = sim_start + args.duration

    insert_static_data(client, sim_start, sim_end)
    load_robot_data(client, args.rovers, args.duration, args.freq)
    verify(client)
    print("\nSetup zakończony.")


if __name__ == "__main__":
    main()
