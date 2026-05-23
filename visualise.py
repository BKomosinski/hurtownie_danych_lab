import pandas as pd
import matplotlib.pyplot as plt


def visualize_gnss_data(filename="simulated_rovers.csv") :
	print(f"Wczytywanie danych z pliku {filename}...")

	try :
		# Wczytanie danych z pliku CSV
		df = pd.read_csv(filename)
	except FileNotFoundError :
		print(f"Błąd: Nie znaleziono pliku '{filename}'. Wygeneruj go najpierw.")
		return

	# Inicjalizacja dużego, czytelnego okna wykresu
	plt.figure(figsize=(10, 8))

	# Grupowanie danych po nazwie robota ('rover_circle', 'rover_line', 'rover_wave')
	for frame_id, group in df.groupby('frame_id') :
		# Rysujemy trasę: X to Długość geograficzna (Longitude), Y to Szerokość (Latitude)
		plt.plot(
			group['longitude'],
			group['latitude'],
			marker='.',  # Kropki na każdym pomiarze
			linestyle='-',  # Linie łączące pomiary
			markersize=3,  # Wielkość kropek
			label=frame_id  # Nazwa do legendy
		)

	# Upiększanie wykresu
	plt.title('Trajektorie robotów (Widok GNSS z góry)', fontsize=14)
	plt.xlabel('Długość geograficzna (Longitude)', fontsize=12)
	plt.ylabel('Szerokość geograficzna (Latitude)', fontsize=12)
	plt.legend(title="Identyfikator robota")
	plt.grid(True, linestyle='--', alpha=0.6)

	# BARDZO WAŻNE: Wyrównanie skali osi X i Y!
	plt.gca().set_aspect('equal', adjustable='datalim')

	# Wyświetlenie interaktywnego okna
	plt.tight_layout()
	nazwa_wyjsciowa = "wizualizacja_tras_gnss.png"
	plt.savefig(nazwa_wyjsciowa, dpi=300, bbox_inches='tight')

if __name__ == "__main__" :
	visualize_gnss_data("simulated_rovers_piotrowo.csv")