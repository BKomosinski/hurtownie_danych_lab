import clickhouse_connect
import time
import random
import subprocess
import numpy as np
from generate import generate_fleet_data

client = clickhouse_connect.get_client(host='localhost', port=8123, username='admin', password='admin')
NUM_RECORDS = 10_000_000
BATCH_SIZE = 1_000_000
ITERATIONS = 10
SCENARIOS = ['no_index', 'pre_index', 'post_index']

def wait_for_clickhouse():
    print("[System] Czekam na uruchomienie ClickHouse...")
    while True:
        try:
            client.command('SELECT 1')
            print("[System] ClickHouse jest gotowy!")
            break
        except Exception:
            time.sleep(2)
            print(".", end="", flush=True)

def restart_docker():
    print("\n[System] Restartowanie kontenera dla zimnego startu...")
    subprocess.run(["docker", "restart", "clickhouse-server"], check=True)
    wait_for_clickhouse()

history = {
    'no_index': [],
    'pre_index': [],
    'post_index': [],
    'gen_time': []
}
for it in range(ITERATIONS):
    restart_docker()
    print(f"\n=== ITERACJA {it + 1}/{ITERATIONS} ===")

    random.shuffle(SCENARIOS)

    start_gen = time.perf_counter()
    data = generate_fleet_data(num_rovers=100, duration_sec=10000, frequency_hz=10)[:NUM_RECORDS]
    gen_duration = time.perf_counter() - start_gen
    history['gen_time'].append(gen_duration)
    print(f"Generowanie danych zajęło: {gen_duration:.2f}s")

    for scenario in SCENARIOS:
        client.command("DROP TABLE IF EXISTS test_table")
        order_by = "ORDER BY (id, timestamp)" if scenario == 'pre_index' else "ORDER BY id"
        client.command(
            f"CREATE TABLE test_table (id UInt64, timestamp Float64, latitude Float64, longitude Float64) ENGINE = MergeTree() {order_by}")

        start = time.perf_counter()
        for i in range(0, len(data), BATCH_SIZE):
            client.insert('test_table', data[i:i + BATCH_SIZE],
                          column_names=['id', 'timestamp', 'latitude', 'longitude'])
        duration = time.perf_counter() - start

        if scenario == 'post_index':
            start_idx = time.perf_counter()
            client.command(
                "CREATE TABLE test_table_new (id UInt64, timestamp Float64, latitude Float64, longitude Float64) ENGINE = MergeTree() ORDER BY (id, timestamp)")
            client.command("INSERT INTO test_table_new SELECT * FROM test_table")
            client.command("DROP TABLE test_table")
            client.command("RENAME TABLE test_table_new TO test_table")

            duration += (time.perf_counter() - start_idx)

        history[scenario].append(duration)
        print(f"Scenariusz {scenario} zakończony: {duration:.2f}s")
        client.command("DROP TABLE test_table")


print("\n" + "="*75)
print(f"{'Scenariusz':<20} | {'Średni czas [s]':<15} | {'Std Dev':<10} | {'Wiersze/s'}")
print("-"*75)

avg_gen = np.mean(history['gen_time'])
print(f"{'GENEROWANIE':<20} | {avg_gen:<15.2f} | {np.std(history['gen_time']):<10.2f} | -")

for s in ['no_index', 'pre_index', 'post_index']:
    times = history[s]
    speed = NUM_RECORDS / np.mean(times)
    print(f"{s:<20} | {np.mean(times):<15.2f} | {np.std(times):<10.2f} | {speed:.0f}")
print("="*75)