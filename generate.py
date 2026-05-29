import csv
import math
import random
import argparse

# --- STAŁE I KONFIGURACJA ---
FIELD_MIN_LAT = 52.4600
FIELD_MAX_LAT = 52.4650
FIELD_MIN_LON = 16.9200
FIELD_MAX_LON = 16.9300

METERS_TO_LAT = 1 / 111320.0
METERS_TO_LON = 1 / (111320.0 * math.cos(math.radians((FIELD_MIN_LAT + FIELD_MAX_LAT) / 2)))


def clamp(val, min_val, max_val) :
	return max(min(val, max_val), min_val)


def generate_sensors(num_sensors) :
	sensors = []
	for i in range(num_sensors) :
		lat = random.uniform(FIELD_MIN_LAT, FIELD_MAX_LAT)
		lon = random.uniform(FIELD_MIN_LON, FIELD_MAX_LON)
		sensors.append({'id' : f"sensor_{i}", 'lat' : lat, 'lon' : lon})
	return sensors


def is_near_sensor(rover_lat, rover_lon, sensors, threshold_meters=15.0) :
	min_dist = float('inf')
	closest_sensor = None

	for s in sensors :
		d_lat = (rover_lat - s['lat']) / METERS_TO_LAT
		d_lon = (rover_lon - s['lon']) / METERS_TO_LON
		dist = math.sqrt(d_lat ** 2 + d_lon ** 2)
		if dist < min_dist :
			min_dist = dist
			closest_sensor = s['id']

	if min_dist <= threshold_meters :
		return True, closest_sensor
	return False, None


import numpy as np


def generate_fleet_data(num_rovers=5, duration_sec=3600, frequency_hz=10, num_sensors=3, start_time_unix=1714398000.523):
   steps = duration_sec * frequency_hz
   dt = 1.0 / frequency_hz

   # 1. Inicjalizacja stanu robotów jako tablice (zamiast słowników)
   # Wszystkie parametry dla N robotów w jednym miejscu
   lat = np.random.uniform(52.4600, 52.4650, num_rovers)
   lon = np.random.uniform(16.9200, 16.9300, num_rovers)
   speeds = np.random.uniform(1.0, 2.5, num_rovers)
   angles = np.random.uniform(0, 2 * np.pi, num_rovers)

   # Profile przypisane jako tablica liczb (0:straight, 1:sine, 2:zigzag, 3:meander)
   profiles = np.random.randint(0, 4, num_rovers)

   # Parametry dla każdego robota
   omega = np.random.uniform(0.5, 1.5, num_rovers)
   amplitude = np.random.uniform(2.0, 6.0, num_rovers)
   period = np.random.uniform(2.0, 5.0, num_rovers)
   roam_start_t = np.zeros(num_rovers)

   data_to_insert = []

   # Stałe przeliczniki
   METERS_TO_LAT = 1 / 111320.0
   METERS_TO_LON = 1 / (111320.0 * np.cos(np.radians(52.4625)))

   print("Generuję dane wektorowo...")

   for step in range(steps):
      current_time = start_time_unix + (step * dt)
      t_total = step * dt

      # Obliczanie przesunięć dla każdego profilu naraz (maskowanie)
      d_lat_m = np.zeros(num_rovers)
      d_lon_m = np.zeros(num_rovers)

      # STRAIGHT
      mask = (profiles == 0)
      d_lat_m[mask] = (speeds[mask] * dt) * np.sin(angles[mask])
      d_lon_m[mask] = (speeds[mask] * dt) * np.cos(angles[mask])

      # SINE
      mask = (profiles == 1)
      t_roam = t_total - roam_start_t[mask]
      lateral = amplitude[mask] * omega[mask] * np.cos(omega[mask] * t_roam) * dt
      d_lat_m[mask] = (speeds[mask] * dt) * np.sin(angles[mask]) + lateral * np.cos(angles[mask])
      d_lon_m[mask] = (speeds[mask] * dt) * np.cos(angles[mask]) - lateral * np.sin(angles[mask])

      # ZIGZAG
      mask = (profiles == 2)
      t_roam = t_total - roam_start_t[mask]
      sign = np.where((t_roam % period[mask]) < (period[mask] / 2), 1, -1)
      lateral = sign * speeds[mask] * 0.8 * dt
      d_lat_m[mask] = (speeds[mask] * dt) * np.sin(angles[mask]) + lateral * np.cos(angles[mask])
      d_lon_m[mask] = (speeds[mask] * dt) * np.cos(angles[mask]) - lateral * np.sin(angles[mask])

      # MEANDER
      mask = (profiles == 3)
      angles[mask] += np.random.uniform(-0.15, 0.15, np.sum(mask))
      d_lat_m[mask] = (speeds[mask] * dt) * np.sin(angles[mask])
      d_lon_m[mask] = (speeds[mask] * dt) * np.cos(angles[mask])

      # Aktualizacja pozycji
      lat += d_lat_m * METERS_TO_LAT
      lon += d_lon_m * METERS_TO_LON

      # Geofencing (wszystkie naraz)
      lat = np.clip(lat, 52.4600, 52.4650)
      lon = np.clip(lon, 16.9200, 16.9300)

      # Zbieranie danych (tu musimy dodać do listy)
      for i in range(num_rovers):
         data_to_insert.append((i + 1, current_time, lat[i], lon[i]))

   return data_to_insert


if __name__ == "__main__":
    import argparse
    import csv

    parser = argparse.ArgumentParser(description="Generator floty rolniczej.")
    parser.add_argument("-o", "--output", type=str, default="simulated_rovers_piotrowo.csv")
    parser.add_argument("-n", "--num-rovers", type=int, default=100)
    parser.add_argument("-d", "--duration", type=int, default=3600)
    parser.add_argument("-f", "--frequency", type=int, default=10)
    parser.add_argument("-s", "--sensors", type=int, default=3)

    args = parser.parse_args()

    data = generate_fleet_data(
        num_rovers=args.num_rovers,
        duration_sec=args.duration,
        frequency_hz=args.frequency,
        num_sensors=args.sensors
    )

    print(f"Zapisuję {len(data)} rekordów do pliku '{args.output}'...")
    with open(args.output, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Id', 'timestamp', 'latitude', 'longitude'])
        writer.writerows(data)

    print("Gotowe!")