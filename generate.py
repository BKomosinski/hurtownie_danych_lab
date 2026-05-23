import csv
import math
import random
import argparse


def ping_pong_movement(t_sec, velocity, max_distance) :
	"""
	Funkcja fali trójkątnej. Sprawia, że obiekt odbija się od wirtualnej ściany.
	Kiedy osiągnie 'max_distance', zawraca ze stałą prędkością 'velocity'.
	"""
	if velocity == 0 :
		return 0
	inside_sin = (velocity * t_sec * math.pi) / (2.0 * max_distance)
	return max_distance * (2.0 / math.pi) * math.asin(math.sin(inside_sin))


def generate_bounded_gnss(
		filename="simulated_rovers_piotrowo.csv",
		start_time_ns=1765375369784983905,
		duration_sec=494,
		frequency_hz=10,
		lat0=52.40152,
		lon0=16.95164,
		alt0=100.161
) :
	"""
	Generuje sztuczne dane GNSS dostosowane do statystyk profilowania z kampusu Piotrowo.
	"""
	steps = duration_sec * frequency_hz
	dt_ns = int(1_000_000_000 / frequency_hz)
	dt_sec = 1.0 / frequency_hz

	# Przeliczniki stopni na metry
	meters_to_lat = 1 / 111320.0
	meters_to_lon = 1 / (111320.0 * math.cos(math.radians(lat0)))

	# Wymiary wirtualnego ogrodzenia (połowa szerokości/długości kampusu w metrach)
	BOUNDARY_X = 40.0
	BOUNDARY_Y = 38.0

	with open(filename, mode='w', newline='') as f :
		writer = csv.writer(f)
		writer.writerow(['log_time_ns', 'frame_id', 'latitude', 'longitude', 'altitude', 'status'])

		for step in range(steps) :
			current_time = start_time_ns + (step * dt_ns)
			t_sec = step * dt_sec
			noise_alt = random.gauss(0, 0.15)  # Szum wysokości z raportu

			# --- 1. ROBOT: RUCH PO OKRĘGU ---
			r_circle = 15.0
			omega = 0.1
			dx1 = r_circle * math.cos(omega * t_sec)
			dy1 = r_circle * math.sin(omega * t_sec)

			writer.writerow([
				current_time, 'ublox_rover_circle',
				round(lat0 + (dy1 * meters_to_lat), 8),
				round(lon0 + (dx1 * meters_to_lon), 8),
				round(alt0 + noise_alt, 3), 2
			])

			# --- 2. ROBOT: RUCH W LINII PROSTEJ (Z ODBICIEM) ---
			v_line = 0.5
			dx2 = ping_pong_movement(t_sec, velocity=v_line, max_distance=BOUNDARY_X)
			dy2 = -20.0

			writer.writerow([
				current_time, 'ublox_rover_line',
				round(lat0 + (dy2 * meters_to_lat), 8),
				round(lon0 + (dx2 * meters_to_lon), 8),
				round(alt0 + noise_alt, 3), 2
			])

			# --- 3. ROBOT: RUCH SINUSOIDALNY (Z ODBICIEM) ---
			v_north = 0.3
			dy3 = ping_pong_movement(t_sec, velocity=v_north, max_distance=BOUNDARY_Y)
			dx3 = 5.0 * math.sin(2 * math.pi * 0.05 * t_sec)

			writer.writerow([
				current_time, 'ublox_rover_wave',
				round(lat0 + (dy3 * meters_to_lat), 8),
				round(lon0 + (dx3 * meters_to_lon), 8),
				round(alt0 + noise_alt, 3), 2
			])

	print(f"Wygenerowano '{filename}' pomyślnie.")
	print(f"Czas: {duration_sec}s, Częstotliwość: {frequency_hz}Hz.")
	print(f"Zabezpieczono granice Kampusu (X: ±{BOUNDARY_X}m, Y: ±{BOUNDARY_Y}m).")


if __name__ == "__main__" :
	parser = argparse.ArgumentParser(description="Generator realistycznych danych GNSS dla robota na kampusie.")

	parser.add_argument("-o", "--output", type=str, default="simulated_rovers_piotrowo.csv",
	                    help="Nazwa pliku wyjściowego (np. moje_dane.csv)")
	parser.add_argument("-d", "--duration", type=int, default=494,
	                    help="Czas trwania symulacji w sekundach (domyślnie: 494)")
	parser.add_argument("-f", "--frequency", type=int, default=10,
	                    help="Częstotliwość próbkowania w Hz (domyślnie: 10)")
	parser.add_argument("--lat", type=float, default=52.40152,
	                    help="Początkowa szerokość geograficzna")
	parser.add_argument("--lon", type=float, default=16.95164,
	                    help="Początkowa długość geograficzna")
	parser.add_argument("--alt", type=float, default=100.161,
	                    help="Początkowa wysokość n.p.m.")
	parser.add_argument("--start-time", type=int, default=1765375369784983905,
	                    help="Czas początkowy w nanosekundach")

	args = parser.parse_args()

	# Przekazanie argumentów do funkcji
	generate_bounded_gnss(
		filename=args.output,
		start_time_ns=args.start_time,
		duration_sec=args.duration,
		frequency_hz=args.frequency,
		lat0=args.lat,
		lon0=args.lon,
		alt0=args.alt
	)