import csv
import math
import random
import argparse


def generate_realistic_gnss(
		filename="simulated_rovers.csv",
		start_time_ns=1765375369784983905,  # Wartość MIN z raportu
		duration_sec=494,  # 8 min 12 sek (z raportu)
		frequency_hz=10,  # Wyliczone z 4937 wiadomości / 494s
		lat0=52.40152,  # Wartość MEAN z raportu
		lon0=16.95164,  # Wartość MEAN z raportu
		alt0=100.161  # Wartość MEAN z raportu
) :
	"""
	Generuje sztuczne dane GNSS dostosowane do statystyk profilowania z kampusu Piotrowo.
	"""
	steps = duration_sec * frequency_hz
	dt_ns = int(1_000_000_000 / frequency_hz)
	dt_sec = 1.0 / frequency_hz

	# Przeliczniki
	meters_to_lat = 1 / 111320.0
	meters_to_lon = 1 / (111320.0 * math.cos(math.radians(lat0)))

	with open(filename, mode='w', newline='') as f :
		writer = csv.writer(f)
		writer.writerow(['log_time_ns', 'frame_id', 'latitude', 'longitude', 'altitude', 'status'])

		for step in range(steps) :
			current_time = start_time_ns + (step * dt_ns)
			t_sec = step * dt_sec

			# Szum wysokości GPS (Odchylenie ok. 0.15m zgodnie z raportem)
			noise_alt = random.gauss(0, 0.15)

			# --- 1. ROBOT: RUCH PO OKRĘGU (ublox_rover_circle) ---
			# Ograniczamy promień do 10m, by nie wyjść poza ramy kampusu (MIN/MAX LAT/LON)
			r_circle = 10.0
			omega = 0.1  # Wolniejszy obrót (ok 60 sekund na pełne koło)
			dx1 = r_circle * math.cos(omega * t_sec)
			dy1 = r_circle * math.sin(omega * t_sec)
			alt1 = alt0 + noise_alt

			writer.writerow([
				current_time, 'ublox_rover_circle',
				round(lat0 + (dy1 * meters_to_lat), 8),
				round(lon0 + (dx1 * meters_to_lon), 8),
				round(alt1, 3), 2  # Status 2 oznacza STATUS_GBAS_FIX
			])

			# --- 2. ROBOT: RUCH W LINII PROSTEJ (ublox_rover_line) ---
			# Jedzie bardzo wolno (0.2 m/s), aby przez 8 minut nie wyjechać z kampusu
			v_line = 0.15
			dx2 = v_line * t_sec - 35.0  # Startuje 35 metrów na zachód
			dy2 = 0.0
			alt2 = alt0 + noise_alt

			writer.writerow([
				current_time, 'ublox_rover_line',
				round(lat0 + (dy2 * meters_to_lat), 8),
				round(lon0 + (dx2 * meters_to_lon), 8),
				round(alt2, 3), 2
			])

			# --- 3. ROBOT: RUCH SINUSOIDALNY (ublox_rover_wave) ---
			v_north = 0.1  # Powolna jazda na północ
			amp = 5.0  # Mniejsze wężykowanie (5m w boki)
			freq = 0.05
			dy3 = v_north * t_sec - 20.0  # Startuje lekko z południa
			dx3 = amp * math.sin(2 * math.pi * freq * t_sec)

			writer.writerow([
				current_time, 'ublox_rover_wave',
				round(lat0 + (dy3 * meters_to_lat), 8),
				round(lon0 + (dx3 * meters_to_lon), 8),
				round(alt0 + noise_alt, 3), 2
			])

	print(f"Wygenerowano '{filename}'. Liczba rekordów dla każdego robota to ok. {steps}.")
	print(f"Statystyki są dopasowane do pliku .mcap z Politechniki Poznańskiej.")


if __name__ == "__main__" :
	parser = argparse.ArgumentParser(description="Generator realistycznych danych GNSS dla robota na kampusie.")
	parser.add_argument("-o", "--output", type=str, default="simulated_rovers_piotrowo.csv",
	                    help="Nazwa pliku wyjściowego")

	# Pozwalamy zmienić wartości, ale domyślne są wzięte bezpośrednio z pliku PDF
	args = parser.parse_args()
	generate_realistic_gnss(filename=args.output)