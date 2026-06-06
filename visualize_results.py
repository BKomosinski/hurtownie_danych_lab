import argparse
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

COLORS = {
    "geofencing":  "#2196F3",
    "proximity":   "#FF9800",
    "collision":   "#4CAF50",
}
HATCHES = {
    "geofencing": "",
    "proximity":  "//",
    "collision":  "xx",
}


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def plot_basic(df: pd.DataFrame, ax: plt.Axes):
    sub = df[df["test"] == "basic"].copy()
    queries = sub["query"].tolist()
    x = np.arange(len(queries))
    w = 0.25

    bars_avg = ax.bar(x - w, sub["avg_s"], width=w, label="Średni", color=[COLORS[q] for q in queries])
    bars_min = ax.bar(x,     sub["min_s"], width=w, label="Min",    color=[COLORS[q] for q in queries], alpha=0.6)
    bars_max = ax.bar(x + w, sub["max_s"], width=w, label="Max",    color=[COLORS[q] for q in queries], alpha=0.4)

    for bar_group in [bars_avg, bars_min, bars_max]:
        for bar in bar_group:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.002,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(queries, fontsize=10)
    ax.set_ylabel("Czas [s]")
    ax.set_title("1. Czas wykonania zapytań (min / avg / max)", fontweight="bold")
    ax.legend(fontsize=9)
    ax.set_ylim(0, sub["max_s"].max() * 1.3)
    ax.grid(axis="y", alpha=0.3)


def plot_cache(df: pd.DataFrame, ax: plt.Axes):
    cold = df[df["test"] == "cache_cold"][["query", "avg_s"]].rename(columns={"avg_s": "cold"})
    warm = df[df["test"] == "cache_warm"][["query", "avg_s"]].rename(columns={"avg_s": "warm"})
    sub = cold.merge(warm, on="query")

    queries = sub["query"].tolist()
    x = np.arange(len(queries))
    w = 0.35

    ax.bar(x - w / 2, sub["cold"], width=w, label="Zimny start (cold)",
           color=[COLORS[q] for q in queries])
    ax.bar(x + w / 2, sub["warm"], width=w, label="Ciepły start (warm)",
           color=[COLORS[q] for q in queries], alpha=0.55, hatch="//")

    for i, row in sub.iterrows():
        speedup = row["cold"] / row["warm"] if row["warm"] > 0 else 1.0
        xpos = x[list(sub["query"]).index(row["query"])]
        ax.text(xpos, max(row["cold"], row["warm"]) * 1.05,
                f"×{speedup:.1f}", ha="center", fontsize=9, color="black")

    ax.set_xticks(x)
    ax.set_xticklabels(queries, fontsize=10)
    ax.set_ylabel("Czas [s]")
    ax.set_title("2. Efekt cache (zimny vs ciepły start)", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)



def plot_concurrency(df: pd.DataFrame, ax: plt.Axes):
    sub = df[df["test"].str.startswith("concurrency_")].copy()
    if sub.empty:
        ax.set_title("3. Współbieżność – brak danych")
        return

    sub["workers"] = sub["workers"].astype(int)
    queries = sub["query"].unique()

    for q in queries:
        qdf = sub[sub["query"] == q].sort_values("workers")
        # throughput – jeśli nie ma kolumny, oblicz z avg_s i workers
        if "throughput_qs" not in qdf.columns or qdf["throughput_qs"].isna().all():
            qdf = qdf.copy()
            qdf["throughput_qs"] = qdf["workers"] / qdf["avg_s"]
        ax.plot(qdf["workers"], qdf["throughput_qs"], marker="o",
                color=COLORS.get(q, "gray"), label=q, linewidth=2)

    ax.set_xlabel("Liczba równoczesnych użytkowników")
    ax.set_ylabel("Przepustowość [zapytań/s]")
    ax.set_title("3. Wpływ współbieżności na przepustowość", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)



def plot_index(df: pd.DataFrame, ax: plt.Axes):
    no_idx = df[df["test"] == "no_index"][["query", "avg_s"]].rename(columns={"avg_s": "no_idx"})
    with_idx = df[df["test"] == "with_index"][["query", "avg_s"]].rename(columns={"avg_s": "with_idx"})
    sub = no_idx.merge(with_idx, on="query")

    if sub.empty:
        ax.set_title("4. Wpływ indeksów – brak danych")
        return

    queries = sub["query"].tolist()
    x = np.arange(len(queries))
    w = 0.35

    ax.bar(x - w / 2, sub["no_idx"],   width=w, label="Bez indeksu",
           color=[COLORS[q] for q in queries])
    ax.bar(x + w / 2, sub["with_idx"], width=w, label="Z indeksem",
           color=[COLORS[q] for q in queries], alpha=0.55, hatch="\\\\")

    for i, row in sub.iterrows():
        speedup = row["no_idx"] / row["with_idx"] if row["with_idx"] > 0 else 1.0
        xpos = x[list(sub["query"]).index(row["query"])]
        ax.text(xpos, max(row["no_idx"], row["with_idx"]) * 1.05,
                f"×{speedup:.1f}", ha="center", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(queries, fontsize=10)
    ax.set_ylabel("Czas [s]")
    ax.set_title("4. Wpływ indeksów skipping na czas zapytania", fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)


def plot_index_build(df: pd.DataFrame, ax: plt.Axes):
    sub = df[df["test"] == "index_build_time"]
    if sub.empty:
        ax.set_visible(False)
        return
    ax.bar(sub["query"], sub["avg_s"], color=[COLORS.get(q, "gray") for q in sub["query"]])
    ax.set_ylabel("Czas budowania indeksu [s]")
    ax.set_title("5. Czas budowania indeksów skipping", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="benchmark_results.csv")
    parser.add_argument("--output", default="benchmark_plots.png")
    args = parser.parse_args()

    df = load(args.input)
    print(f"Wczytano {len(df)} wierszy z {args.input}")

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Benchmark ClickHouse – Geofencing / Sensor Proximity / Collision Detection",
                 fontsize=14, fontweight="bold", y=1.01)

    plot_basic(df,       axes[0, 0])
    plot_cache(df,       axes[0, 1])
    plot_concurrency(df, axes[0, 2])
    plot_index(df,       axes[1, 0])
    plot_index_build(df, axes[1, 1])

    patches = [mpatches.Patch(color=c, label=q) for q, c in COLORS.items()]
    axes[1, 2].legend(handles=patches, loc="center", fontsize=12, title="Zapytanie", title_fontsize=11)
    axes[1, 2].axis("off")

    plt.tight_layout()
    plt.savefig(args.output, dpi=150, bbox_inches="tight")
    print(f"Wykresy zapisane w {args.output}")


if __name__ == "__main__":
    main()
