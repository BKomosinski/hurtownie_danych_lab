# Projekt: Wydajność ClickHouse – Dane Robotyczne
## Etap 1B: Generator + zapytania + benchmark

---

## Struktura projektu

```
projekt_clickhouse/
├── setup_and_load.py     # Tworzy schemat, wstawia dane robotów + czujniki
├── queries.py            # Definicje 3 zapytań SQL (Geofencing, Proximity, Collision)
├── run_queries.py        # Szybkie uruchomienie 3 zapytań + wyświetlenie wyników
├── benchmark.py          # Pełny benchmark (czas, cache, współbieżność, indeksy)
├── visualize_results.py  # Wykresy z pliku benchmark_results.csv
└── README.md
```

---

## Wymagania

```bash
pip install clickhouse-connect numpy pandas matplotlib
```

Uruchomienie ClickHouse z `docker-compose.yml` (katalog nadrzędny):
```bash
docker compose up -d
```

---

## Krok 1 – Załaduj dane

```bash
# Domyślnie: 50 robotów, 3600s symulacji, 10 Hz → ~1.8M rekordów
python setup_and_load.py

python setup_and_load.py --rovers 50 --duration 36000 --freq 10
```

---

## Krok 2 – Sprawdź wyniki zapytań

```bash
python run_queries.py
```

Wyświetla wyniki i czas dla:
- **Geofencing** – liczba próbek poza geofence per robot
- **Sensor Proximity** – liczba zdarzeń alarmowych (robot blisko czujnika + przekroczony próg)
- **Collision Detection** – pary robotów w bliskiej odległości w tym samym momencie

---

## Krok 3 – Pełny benchmark

```bash
python benchmark.py

python benchmark.py --no-index-test --no-concurrency

python benchmark.py --iterations 5
```

Zapisuje wyniki do `benchmark_results.csv`.

---

## Krok 4 – Wizualizacja

```bash
python visualize_results.py
```

---

## Co mierzy benchmark?

| Test               | Opis                                                         |
|--------------------|--------------------------------------------------------------|
| `basic`            | min/avg/max z N iteracji (domyślnie 10)                      |
| `cache_cold`       | 1. wykonanie po czyszczeniu cache                            |
| `cache_warm`       | kolejne wykonania (potencjalnie z cache marks/buffer)        |
| `concurrency_1`    | 1 równoczesny użytkownik (baseline)                          |
| `concurrency_5`    | 5 równoczesnych zapytań (ThreadPool)                         |
| `concurrency_10`   | 10 równoczesnych zapytań                                     |
| `no_index`         | bez indeksów skipping (ORDER BY id tylko)                    |
| `index_build_time` | czas budowania/materializacji 3 indeksów minmax              |
| `with_index`       | z indeksami minmax na lat, lon, ts                           |

---

## Schemat bazy danych

```sql
-- Główna tabela pozycji robotów
CREATE TABLE robot_positions (
    robot_id  UInt32,
    ts        Float64,   -- UNIX timestamp z ułamkiem sekundy
    lat       Float64,
    lon       Float64
) ENGINE = MergeTree() ORDER BY (robot_id, ts);

-- Statyczne sensory środowiskowe
CREATE TABLE sensors (
    sensor_id  UInt32,
    lat        Float64,
    lon        Float64,
    threshold  Float64   -- próg wilgotności
) ENGINE = MergeTree() ORDER BY sensor_id;

-- Odczyty wilgotności czujników (co 1s)
CREATE TABLE sensor_readings (
    sensor_id  UInt32,
    ts         Float64,
    value      Float64
) ENGINE = MergeTree() ORDER BY (sensor_id, ts);

-- Definicja geofence (strefa dozwolona)
CREATE TABLE geofence_zones (
    zone_id    UInt32,
    min_lat    Float64,
    max_lat    Float64,
    min_lon    Float64,
    max_lon    Float64,
    label      String
) ENGINE = MergeTree() ORDER BY zone_id;
```

---

## Parametry geograficzne

- **Pole:** 52.4600–52.4650°N, 16.9200–16.9300°E (kampus Piotrowo, Poznań)
- **Geofence:** prostokąt wewnętrzny (bufor ~100m od granic pola)
- **5 czujników:** rozmieszczonych stałe w różnych częściach pola
- **Próg alertu czujnika:** przekroczony przez pierwszą połowę czasu symulacji
- **Próg bliskości (sensor proximity):** 15 m
- **Próg kolizji robot–robot:** 2 m

---

## Indeksy ClickHouse

ClickHouse używa **primary key** (ORDER BY) jako głównego mechanizmu filtrowania (sparse index, granule = 8192 wierszy). Dodatkowe **skipping indexes** (typ `minmax`) pozwalają pominąć granule gdzie wartości lat/lon/ts nie pasują do warunku WHERE.

```sql
-- Dodanie indeksów minmax (tworzone przez benchmark.py automatycznie)
ALTER TABLE robot_positions ADD INDEX idx_lat (lat) TYPE minmax GRANULARITY 4;
ALTER TABLE robot_positions ADD INDEX idx_lon (lon) TYPE minmax GRANULARITY 4;
ALTER TABLE robot_positions ADD INDEX idx_ts  (ts)  TYPE minmax GRANULARITY 4;
ALTER TABLE robot_positions MATERIALIZE INDEX idx_lat;
```

