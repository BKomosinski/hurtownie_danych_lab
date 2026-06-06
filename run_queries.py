
import time
import clickhouse_connect
from queries import ALL_QUERIES


def get_client():
    return clickhouse_connect.get_client(
        host="localhost", port=8123, username="admin", password="admin"
    )


def fmt_rows(rows, cols):
    if not rows:
        return "  (brak wyników)"
    header = " | ".join(f"{c:>15}" for c in cols)
    sep = "-" * len(header)
    lines = [header, sep]
    for row in rows[:20]:
        lines.append(" | ".join(f"{str(v):>15}" for v in row))
    if len(rows) > 20:
        lines.append(f"  ... i {len(rows)-20} więcej wierszy")
    return "\n".join(lines)


def main():
    client = get_client()

    cnt = client.command("SELECT count() FROM robot_positions")
    print(f"robot_positions: {cnt:,} wierszy\n")

    for qname, qfunc in ALL_QUERIES.items():
        sql, params = qfunc()
        print("=" * 60)
        print(f" {qname.upper()}")
        print("=" * 60)

        t0 = time.perf_counter()
        result = client.query(sql, parameters=params)
        elapsed = time.perf_counter() - t0

        rows = result.result_rows
        cols = result.column_names

        print(fmt_rows(rows, cols))
        print(f"\nCzas: {elapsed:.3f}s   Wyników: {len(rows)}")


if __name__ == "__main__":
    main()
