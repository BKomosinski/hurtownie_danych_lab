GEOFENCE_SQL = """
SELECT
    robot_id,
    countIf(lat < {min_lat:Float64}
         OR lat > {max_lat:Float64}
         OR lon < {min_lon:Float64}
         OR lon > {max_lon:Float64}) AS violations,
    count() AS total_samples
FROM robot_positions
GROUP BY robot_id
HAVING violations > 0
ORDER BY violations DESC
"""

GEOFENCE_PARAMS = {
    "min_lat": 52.4610,
    "max_lat": 52.4640,
    "min_lon": 16.9220,
    "max_lon": 16.9280,
}


def geofence_query():
    """Zwraca SQL + parametry dla zapytania Geofencing."""
    return GEOFENCE_SQL, GEOFENCE_PARAMS


PROXIMITY_SQL = """
WITH
    robot_sensor_pairs AS (
        SELECT
            rp.robot_id,
            rp.ts,
            s.sensor_id,
            s.threshold,
            -- Odległość euklidesowa w metrach (aproksymacja kartezjańska)
            sqrt(
                pow((rp.lat - s.lat) * 111320.0, 2) +
                pow((rp.lon - s.lon) * 111320.0 * cos(toFloat64(52.4625) * pi() / 180.0), 2)
            ) AS dist_m
        FROM robot_positions AS rp
        CROSS JOIN sensors AS s
        WHERE dist_m <= {radius_m:Float64}
    ),
    with_readings AS (
        SELECT
            rsp.robot_id,
            rsp.sensor_id,
            rsp.ts,
            sr.value,
            rsp.threshold
        FROM robot_sensor_pairs AS rsp
        INNER JOIN sensor_readings AS sr
            ON rsp.sensor_id = sr.sensor_id
            AND floor(rsp.ts) = floor(sr.ts)   -- dopasowanie do sekundy
        WHERE sr.value > rsp.threshold          -- czujnik przekroczył próg
    )
SELECT
    robot_id,
    sensor_id,
    count() AS alert_events
FROM with_readings
GROUP BY robot_id, sensor_id
ORDER BY alert_events DESC
LIMIT 100
"""

PROXIMITY_PARAMS = {
    "radius_m": 15.0,
}


def proximity_query():
    return PROXIMITY_SQL, PROXIMITY_PARAMS

COLLISION_SQL = """
SELECT
    r1.robot_id   AS robot_a,
    r2.robot_id   AS robot_b,
    count()       AS near_miss_events,
    min(
        sqrt(
            pow((r1.lat - r2.lat) * 111320.0, 2) +
            pow((r1.lon - r2.lon) * 111320.0 * cos(toFloat64(52.4625) * pi() / 180.0), 2)
        )
    ) AS min_dist_m
FROM robot_positions AS r1
INNER JOIN robot_positions AS r2
    ON round(r1.ts, 1) = round(r2.ts, 1)
    AND r1.robot_id < r2.robot_id
WHERE
    sqrt(
        pow((r1.lat - r2.lat) * 111320.0, 2) +
        pow((r1.lon - r2.lon) * 111320.0 * cos(toFloat64(52.4625) * pi() / 180.0), 2)
    ) <= {collision_radius_m:Float64}
GROUP BY robot_a, robot_b
HAVING near_miss_events > 0
ORDER BY near_miss_events DESC
LIMIT 50
"""

COLLISION_PARAMS = {
    "collision_radius_m": 2.0,
}


def collision_query():
    return COLLISION_SQL, COLLISION_PARAMS



ALL_QUERIES = {
    "geofencing":  geofence_query,
    "proximity":   proximity_query,
    "collision":   collision_query,
}
