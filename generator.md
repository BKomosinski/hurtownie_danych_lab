# Generator Danych

Zaawansowany generator tworzący plik CSV z symulowanymi danymi o ruchu robotów. Uwzględnia przemieszczanie się pojazdów do zdefiniowanych czujników, a następnie patrolowanie terenu z wykorzystaniem różnych profili ruchu (`straight`, `sine`, `zigzag`, `meander`). Zawiera również mechanizm geofencingu (odbijanie się od granic obszaru).

## Szybki start
Uruchomienie z domyślnymi parametrami (5 robotów, 3 czujniki, symulacja 1 godziny obszaru kampusu Piotrowo z częstotliwością 10Hz):

```bash
python generator.py
```

## Uruchomienie z własnymi parametrami
Możesz dostosować liczbę pojazdów, czas trwania, częstotliwość logowania i liczbę czujników:

```bash
python generator.py -o trasa.csv -n 10 -d 120 -f 5 -s 4
```

## Dostępne parametry (flagi)

| Flaga | Długa flaga | Opis | Domyślnie |
| :--- | :--- | :--- | :--- |
| `-o` | `--output` | Nazwa pliku wyjściowego CSV | `simulated_rovers_piotrowo.csv` |
| `-n` | `--num-rovers` | Liczba symulowanych robotów | `5` |
| `-d` | `--duration` | Czas trwania symulacji w sekundach | `3600` |
| `-f` | `--frequency` | Częstotliwość zapisu próbek w Hz | `10` |
| `-s` | `--sensors` | Liczba generowanych czujników na polu | `3` |

## Format pliku wyjściowego
Wygenerowany plik CSV zawiera następujące kolumny:
* **Id** - Identyfikator robota
* **timestamp** - Czas w formacie UNIX Epoch (w sekundach z ułamkiem)
* **latitude** - Szerokość geograficzna
* **longitude** - Długość geograficzna