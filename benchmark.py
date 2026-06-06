import argparse
import csv
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import clickhouse_connect

from queries import ALL_QUERIES

# ──────────────────────────────────────────────────────────────────────────────
ITERATIONS = 10
CONCURRENCY_LEVELS = [1, 5, 10]
OUTPUT_CSV = "benchmark_results.csv"

INDEX_DDL = {
    "lat_idx": "ALTER TABLE robot_positions ADD INDEX IF NOT EXISTS idx_lat (lat) TYPE minmax GRANULARITY 4",
    "lon_idx": "ALTER TABLE robot_positions ADD INDEX IF NOT EXISTS idx_lon (lon) TYPE minmax GRANULARITY 4",
    "ts_idx":  "ALTER TABLE robot_positions ADD INDEX IF NOT EXISTS idx_ts  (ts)  TYPE minmax GRANULARITY 4",
}

DROP_INDEXES = [
    "ALTER TABLE robot_positions DROP INDEX IF EXISTS idx_lat",
    "ALTER TABLE robot_positions DROP INDEX IF EXISTS idx_lon",
    "ALTER TABLE robot_positions DROP INDEX IF EXISTS idx_ts",
]
# ──────────────────────────────────────────────────────────────────────────────


def get_client():
    return clickhouse_connect.get_client(
        host="localhost", port=8123, username="admin", password="admin"
    )


def run_query_once(client, sql: str, params: dict) -> float:
    t0 = time.perf_counter()
    client.query(sql, parameters=params)
    return time.perf_counter() - t0


def flush_query_cache(client):
    try:
        client.command("SYSTEM DROP QUERY CACHE")
    except Exception:
        pass


def flush_mark_cache(client):
    try:
        client.command("SYSTEM DROP MARK CACHE")
        client.command("SYSTEM DROP UNCOMPRESSED CACHE")
    except Exception:
        pass



def bench_basic(client, query_name: str, sql: str, params: dict, n: int):
    print(f"\n  [{query_name}] Podstawowy benchmark ({n} iteracji)...")
    times = []
    for i in range(n):
        flush_query_cache(client)
        t = run_query_once(client, sql, params)
        times.append(t)
        print(f"    iter {i+1:>2}/{n}: {t:.3f}s")

    result = {
        "query":   query_name,
        "test":    "basic",
        "workers": 1,
        "min_s":   min(times),
        "max_s":   max(times),
        "avg_s":   statistics.mean(times),
        "stdev_s": statistics.stdev(times) if len(times) > 1 else 0.0,
    }
    print(f"min={result['min_s']:.3f}s  avg={result['avg_s']:.3f}s  max={result['max_s']:.3f}s")
    return result



def bench_cache(client, query_name: str, sql: str, params: dict):
    print(f"\n  [{query_name}] Test cache (5 powtórzeń)...")

    flush_query_cache(client)
    flush_mark_cache(client)
    t_cold = run_query_once(client, sql, params)
    print(f"    COLD (1. wykonanie): {t_cold:.3f}s")

    warm_times = []
    for i in range(4):
        t = run_query_once(client, sql, params)
        warm_times.append(t)
        print(f"    WARM {i+1}:             {t:.3f}s")

    avg_warm = statistics.mean(warm_times)
    speedup  = t_cold / avg_warm if avg_warm > 0 else 1.0
    print(f"zimny={t_cold:.3f}s  śr.ciepły={avg_warm:.3f}s  przyspieszenie={speedup:.1f}x")

    return [
        {"query": query_name, "test": "cache_cold", "workers": 1,
         "min_s": t_cold, "max_s": t_cold, "avg_s": t_cold, "stdev_s": 0.0},
        {"query": query_name, "test": "cache_warm", "workers": 1,
         "min_s": min(warm_times), "max_s": max(warm_times), "avg_s": avg_warm,
         "stdev_s": statistics.stdev(warm_times) if len(warm_times) > 1 else 0.0},
    ]



def _worker(args):
    sql, params = args
    c = get_client()
    return run_query_once(c, sql, params)


def bench_concurrency(query_name: str, sql: str, params: dict, concurrency_levels):
    results = []
    for workers in concurrency_levels:
        print(f"\n  [{query_name}] Współbieżność {workers} użytkowników...")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            t_wall_start = time.perf_counter()
            futures = [pool.submit(_worker, (sql, params)) for _ in range(workers)]
            times = [f.result() for f in as_completed(futures)]
            wall = time.perf_counter() - t_wall_start

        avg = statistics.mean(times)
        stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        throughput = workers / wall
        print(f"    wall={wall:.3f}s  avg_per_query={avg:.3f}s  throughput={throughput:.1f} q/s")

        results.append({
            "query":        query_name,
            "test":         f"concurrency_{workers}",
            "workers":      workers,
            "min_s":        min(times),
            "max_s":        max(times),
            "avg_s":        avg,
            "stdev_s":      stdev,
            "wall_s":       wall,
            "throughput_qs": throughput,
        })
    return results

def drop_indexes(client):
    for ddl in DROP_INDEXES:
        try:
            client.command(ddl)
        except Exception:
            pass
    client.command("OPTIMIZE TABLE robot_positions FINAL")


def add_indexes(client):
    print("  [INDEX] Tworzę indeksy skipping...")
    for name, ddl in INDEX_DDL.items():
        t0 = time.perf_counter()
        client.command(ddl)
        print(f"    {name}: DDL OK")
    t0 = time.perf_counter()
    client.command("ALTER TABLE robot_positions MATERIALIZE INDEX idx_lat")
    client.command("ALTER TABLE robot_positions MATERIALIZE INDEX idx_lon")
    client.command("ALTER TABLE robot_positions MATERIALIZE INDEX idx_ts")
    build_time = time.perf_counter() - t0
    print(f"  [INDEX] Materializacja zakończona: {build_time:.2f}s")
    return build_time


def bench_index_impact(client, query_name: str, sql: str, params: dict, n: int = 5):
    results = []

    drop_indexes(client)
    flush_query_cache(client)
    flush_mark_cache(client)
    print(f"\n  [{query_name}] Bez indeksów ({n} iter)...")
    no_idx_times = []
    for i in range(n):
        flush_query_cache(client)
        t = run_query_once(client, sql, params)
        no_idx_times.append(t)
        print(f"    iter {i+1}: {t:.3f}s")
    results.append({
        "query":   query_name, "test": "no_index", "workers": 1,
        "min_s":   min(no_idx_times), "max_s": max(no_idx_times),
        "avg_s":   statistics.mean(no_idx_times),
        "stdev_s": statistics.stdev(no_idx_times) if len(no_idx_times) > 1 else 0.0,
    })

    # --- BUDOWANIE INDEKSÓW ---
    build_time = add_indexes(client)
    results.append({
        "query":   query_name, "test": "index_build_time", "workers": 0,
        "min_s":   build_time, "max_s": build_time, "avg_s": build_time, "stdev_s": 0.0,
    })

    # --- Z INDEKSAMI ---
    flush_query_cache(client)
    flush_mark_cache(client)
    print(f"  [{query_name}] Z indeksami ({n} iter)...")
    idx_times = []
    for i in range(n):
        flush_query_cache(client)
        t = run_query_once(client, sql, params)
        idx_times.append(t)
        print(f"    iter {i+1}: {t:.3f}s")
    results.append({
        "query":   query_name, "test": "with_index", "workers": 1,
        "min_s":   min(idx_times), "max_s": max(idx_times),
        "avg_s":   statistics.mean(idx_times),
        "stdev_s": statistics.stdev(idx_times) if len(idx_times) > 1 else 0.0,
    })

    speedup = statistics.mean(no_idx_times) / statistics.mean(idx_times) if idx_times else 1.0
    print(f"  [INDEX] Bez indeksu: {statistics.mean(no_idx_times):.3f}s  "
          f"Z indeksem: {statistics.mean(idx_times):.3f}s  "
          f"Przyspieszenie: {speedup:.2f}x")

    return results



def run_all(iterations: int, run_index: bool, run_concurrency: bool):
    client = get_client()
    all_results = []

    for qname, qfunc in ALL_QUERIES.items():
        sql, params = qfunc()
        print(f"\n{'='*60}")
        print(f" ZAPYTANIE: {qname.upper()}")
        print(f"{'='*60}")

        r = bench_basic(client, qname, sql, params, n=iterations)
        all_results.append(r)

        cache_results = bench_cache(client, qname, sql, params)
        all_results.extend(cache_results)

        if run_concurrency:
            conc_results = bench_concurrency(qname, sql, params, CONCURRENCY_LEVELS)
            all_results.extend(conc_results)

        if run_index:
            idx_results = bench_index_impact(client, qname, sql, params, n=5)
            all_results.extend(idx_results)

    return all_results


def save_csv(results: list, path: str):
    fields = ["query", "test", "workers", "min_s", "max_s", "avg_s", "stdev_s",
              "wall_s", "throughput_qs"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\n[CSV] Wyniki zapisane → {path}")


def print_summary(results: list):
    print("\n" + "="*80)
    print(f"{'PODSUMOWANIE':^80}")
    print("="*80)
    fmt = f"{'ZAPYTANIE':<14} {'TEST':<25} {'WORKERS':>7} {'AVG [s]':>8} {'MIN [s]':>8} {'MAX [s]':>8}"
    print(fmt)
    print("-"*80)
    for r in results:
        print(f"{r['query']:<14} {r['test']:<25} {r.get('workers','-'):>7} "
              f"{r.get('avg_s',0):>8.3f} {r.get('min_s',0):>8.3f} {r.get('max_s',0):>8.3f}")
    print("="*80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations",    type=int, default=ITERATIONS)
    parser.add_argument("--no-index-test", action="store_true")
    parser.add_argument("--no-concurrency", action="store_true")
    args = parser.parse_args()

    print(f"Benchmark ClickHouse – {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results = run_all(
        iterations=args.iterations,
        run_index=not args.no_index_test,
        run_concurrency=not args.no_concurrency,
    )

    print_summary(results)
    save_csv(results, OUTPUT_CSV)
