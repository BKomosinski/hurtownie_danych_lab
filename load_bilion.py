import clickhouse_connect
import time
from generate import generate_fleet_data

client = clickhouse_connect.get_client(host='localhost', port=8123, username='admin', password='admin')

TARGET_RECORDS = 100_000_000
TOTAL_ROVERS = 100

client.command('''
    CREATE TABLE IF NOT EXISTS final_table (
        id UInt64,
        timestamp Float64,
        lat Float64,
        lon Float64
    ) ENGINE = MergeTree()
    ORDER BY (id, timestamp)
''')

current_count = client.command("SELECT count() FROM final_table")
max_ts = client.command("SELECT max(timestamp) FROM final_table")

base_time = max_ts if max_ts > 0 else 1714398000.0

print("--- ROZPOCZYNAM TEST (TRYB DOPISYWANIA) ---")
print(f"W tabeli znajduje się już: {current_count:,} rekordów.")
print(f"Znacznik czasu startuje od: {base_time}")

stats = {'gen': 0.0, 'ins': 0.0, 'total': 0.0}
records_inserted_this_run = 0

while records_inserted_this_run < TARGET_RECORDS:
    start_gen = time.perf_counter()

    current_start_time = base_time + (records_inserted_this_run / TOTAL_ROVERS / 10)

    data = generate_fleet_data(
        num_rovers=TOTAL_ROVERS,
        duration_sec=5000,
        frequency_hz=10,
        start_time_unix=current_start_time
    )
    gen_dur = time.perf_counter() - start_gen

    start_ins = time.perf_counter()
    client.insert('final_table', data, column_names=['id', 'timestamp', 'lat', 'lon'])
    ins_dur = time.perf_counter() - start_ins

    stats['gen'] += gen_dur
    stats['ins'] += ins_dur
    stats['total'] += (gen_dur + ins_dur)
    records_inserted_this_run += len(data)

    print(f"Postęp sesji: {records_inserted_this_run / 1e8:.3f} mld | Gen: {gen_dur:.2f}s | Ins: {ins_dur:.2f}s")

print("\n" + "=" * 60)
print(f"{'Metryka':<25} | {'Łącznie [s]':<15} | {'Śr. na punkt [µs]'}")
print("-" * 60)


def print_stat(name, total_time):
    avg_us = (total_time / TARGET_RECORDS) * 1e6
    print(f"{name:<25} | {total_time:<15.2f} | {avg_us:.3f}")


print_stat("Generowanie (CPU)", stats['gen'])
print_stat("Wstawianie (I/O)", stats['ins'])
print_stat("Łącznie (E2E)", stats['total'])
print("=" * 60)

final_count = client.command("SELECT count() FROM final_table")
print(f"Całkowita liczba rekordów w tabeli po tej sesji: {final_count:,}")