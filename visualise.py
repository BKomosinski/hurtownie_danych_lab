import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def visualize_fleet_data(filename="") :
	print(f"Wczytywanie danych z pliku {filename}...")
	try :
		df = pd.read_csv(filename)
	except FileNotFoundError :
		print(f"Błąd: Nie znaleziono pliku '{filename}'.")
		return

	# Współrzędne naszego pola uprawnego (Geofence) z generatora
	FIELD_MIN_LAT = 52.4600
	FIELD_MAX_LAT = 52.4650
	FIELD_MIN_LON = 16.9200
	FIELD_MAX_LON = 16.9300

	plt.figure(figsize=(10, 8))
	ax = plt.gca()

	# 1. Rysowanie wirtualnego ogrodzenia (Geofence)
	# Zaznaczamy pole zielonym prostokątem
	rect_width = FIELD_MAX_LON - FIELD_MIN_LON
	rect_height = FIELD_MAX_LAT - FIELD_MIN_LAT

	geofence_box = patches.Rectangle(
		(FIELD_MIN_LON, FIELD_MIN_LAT),  # (X, Y) dolnego lewego rogu
		rect_width,
		rect_height,
		linewidth=2,
		edgecolor='green',
		facecolor='lightgreen',
		alpha=0.2,  # Lekka przezroczystość
		label='Obszar pola (Geofence)'
	)
	ax.add_patch(geofence_box)

	# 2. Rysowanie tras poszczególnych robotów
	# Grupujemy dane po kolumnie 'Id'
	for robot_id, group in df.groupby('Id') :
		plt.plot(
			group['longitude'],
			group['latitude'],
			marker='.',
			linestyle='-',
			linewidth=0.5,  # Cienka linia ścieżki
			markersize=2,  # Małe kropki
			label=f'Robot {robot_id}'
		)

	# 3. Upiększanie wykresu
	plt.title('Ruch floty robotów na polu uprawnym (Sensor Proximity & Geofencing)', fontsize=14)
	plt.xlabel('Długość geograficzna (Longitude)')
	plt.ylabel('Szerokość geograficzna (Latitude)')

	# Przenosimy legendę poza wykres, żeby nie zasłaniała danych
	plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
	plt.grid(True, linestyle='--', alpha=0.5)

	# Równe proporcje osi, aby obszar nie był zniekształcony
	ax.set_aspect('equal', adjustable='datalim')

	# Dostosowanie marginesów
	plt.tight_layout()
	nazwa_wyjsciowa = "wizualizacja_tras_gnss.png"
	plt.savefig(nazwa_wyjsciowa, dpi=300, bbox_inches='tight')

if __name__ == "__main__" :
	visualize_fleet_data("simulated_rovers_piotrowo.csv")