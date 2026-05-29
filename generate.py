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


def generate_fleet_data(
      num_rovers=5,
      start_time_unix=1714398000.523,
      duration_sec=3600,
      frequency_hz=10,
      num_sensors=3
) :
   steps = duration_sec * frequency_hz
   dt_sec = 1.0 / frequency_hz

   sensors = generate_sensors(num_sensors)
   print("--- Zdefiniowane Czujniki ---")
   for s in sensors :
      print(f"[{s['id']}]: Lat: {s['lat']:.6f}, Lon: {s['lon']:.6f}")

   rovers = []
   profiles = ['straight', 'sine', 'zigzag', 'meander']

   for i in range(num_rovers) :
      target_sensor = random.choice(sensors)
      profile = random.choice(profiles)

      rovers.append({
         'id' : i + 1,
         'lat' : random.uniform(FIELD_MIN_LAT, FIELD_MAX_LAT),
         'lon' : random.uniform(FIELD_MIN_LON, FIELD_MAX_LON),
         'target_sensor' : target_sensor,
         'state' : 'moving_to_sensor',
         'time_at_sensor' : 0,
         'speed' : random.uniform(1.0, 2.5),
         'target_time_at_sensor' : (duration_sec / 2) + random.uniform(-300, 300),
         'profile' : profile,
         'roam_angle' : random.uniform(0, 2 * math.pi),
         'omega' : random.uniform(0.5, 1.5),
         'amplitude' : random.uniform(2.0, 6.0),
         'period' : random.uniform(2.0, 5.0),
         'roam_start_t' : 0
      })

   proximity_hits = {s['id'] : 0 for s in sensors}
   data_to_insert = []

   print(f"\nGenerowanie danych dla {num_rovers} robotów (Profile: {', '.join(profiles)})...")

   for step in range(steps) :
      current_time = start_time_unix + (step * dt_sec)
      t_total = step * dt_sec

      for rover in rovers :
         ts = rover['target_sensor']

         if rover['state'] == 'moving_to_sensor' :
            dx_m = (ts['lon'] - rover['lon']) / METERS_TO_LON
            dy_m = (ts['lat'] - rover['lat']) / METERS_TO_LAT
            dist = math.sqrt(dx_m ** 2 + dy_m ** 2)

            if dist < 5.0 :
               rover['state'] = 'working_at_sensor'
            else :
               move_dist = rover['speed'] * dt_sec
               ratio = move_dist / dist if dist != 0 else 0
               rover['lon'] += (dx_m * ratio) * METERS_TO_LON
               rover['lat'] += (dy_m * ratio) * METERS_TO_LAT

         elif rover['state'] == 'working_at_sensor' :
            angle = random.uniform(0, 2 * math.pi)
            rover['lon'] += (math.cos(angle) * 0.5 * dt_sec) * METERS_TO_LON
            rover['lat'] += (math.sin(angle) * 0.5 * dt_sec) * METERS_TO_LAT

            rover['time_at_sensor'] += dt_sec
            if rover['time_at_sensor'] >= rover['target_time_at_sensor'] :
               rover['state'] = 'roaming'
               rover['roam_start_t'] = t_total

         elif rover['state'] == 'roaming' :
            t_roam = t_total - rover['roam_start_t']
            d_lat_m = 0.0
            d_lon_m = 0.0
            forward_m = rover['speed'] * dt_sec
            angle = rover['roam_angle']

            if rover['profile'] == 'straight' :
               d_lat_m = forward_m * math.sin(angle)
               d_lon_m = forward_m * math.cos(angle)
            elif rover['profile'] == 'sine' :
               lateral_m = rover['amplitude'] * rover['omega'] * math.cos(rover['omega'] * t_roam) * dt_sec
               d_lat_m = forward_m * math.sin(angle) + lateral_m * math.cos(angle)
               d_lon_m = forward_m * math.cos(angle) - lateral_m * math.sin(angle)
            elif rover['profile'] == 'zigzag' :
               lateral_sign = 1 if (t_roam % rover['period']) < (rover['period'] / 2) else -1
               lateral_m = lateral_sign * rover['speed'] * 0.8 * dt_sec
               d_lat_m = forward_m * math.sin(angle) + lateral_m * math.cos(angle)
               d_lon_m = forward_m * math.cos(angle) - lateral_m * math.sin(angle)
            elif rover['profile'] == 'meander' :
               rover['roam_angle'] += random.uniform(-0.15, 0.15)
               angle = rover['roam_angle']
               d_lat_m = forward_m * math.sin(angle)
               d_lon_m = forward_m * math.cos(angle)

            rover['lat'] += d_lat_m * METERS_TO_LAT
            rover['lon'] += d_lon_m * METERS_TO_LON

         old_lat, old_lon = rover['lat'], rover['lon']
         rover['lat'] = clamp(rover['lat'], FIELD_MIN_LAT, FIELD_MAX_LAT)
         rover['lon'] = clamp(rover['lon'], FIELD_MIN_LON, FIELD_MAX_LON)

         if rover['lat'] != old_lat or rover['lon'] != old_lon :
            rover['roam_angle'] += math.pi + random.uniform(-0.5, 0.5)

         is_near, s_id = is_near_sensor(rover['lat'], rover['lon'], sensors, threshold_meters=15.0)
         if is_near :
            proximity_hits[s_id] += 1

         data_to_insert.append((
            rover['id'],
            current_time,
            rover['lat'],
            rover['lon']
         ))

   print("\nZakończono generowanie danych.")
   for s_id, hits in proximity_hits.items() :
      time_near_sensor = hits / frequency_hz
      print(f"Czujnik {s_id}: Zarejestrowano roboty w pobliżu przez {time_near_sensor:.1f} sekund.")

   return data_to_insert


if __name__ == "__main__":
    import argparse
    import csv

    parser = argparse.ArgumentParser(description="Generator floty rolniczej.")
    parser.add_argument("-o", "--output", type=str, default="simulated_rovers_piotrowo.csv")
    parser.add_argument("-n", "--num-rovers", type=int, default=5)
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