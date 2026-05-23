#!/usr/bin/env python3

from pathlib import Path
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from rosbags.highlevel import AnyReader


TOPIC_NAME = "/sensing/imu/imu_raw"


def compute_basic_stats(series: pd.Series) -> pd.Series:
    return pd.Series({
        "count": series.count(),
        "mean": series.mean(),
        "median": series.median(),
        "std": series.std(ddof=1),
        "var": series.var(ddof=1),
        "min": series.min(),
        "max": series.max(),
        "range": series.max() - series.min(),
        "q1": series.quantile(0.25),
        "q3": series.quantile(0.75),
        "iqr": series.quantile(0.75) - series.quantile(0.25),
    })


def read_imu_data(bag_path: Path, topic_name: str) -> pd.DataFrame:
    rows = []

    with AnyReader([bag_path]) as reader:
        connections = [c for c in reader.connections if c.topic == topic_name]

        for conn, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, conn.msgtype)

            av = msg.angular_velocity
            la = msg.linear_acceleration

            rows.append({
                "timestamp": timestamp * 1e-9,  # sekundy

                "av_x": float(av.x),
                "av_y": float(av.y),
                "av_z": float(av.z),
                "av_norm": np.sqrt(av.x**2 + av.y**2 + av.z**2),

                "la_x": float(la.x),
                "la_y": float(la.y),
                "la_z": float(la.z),
                "la_norm": np.sqrt(la.x**2 + la.y**2 + la.z**2),
            })

    df = pd.DataFrame(rows)
    return df


def print_full_stats(stats: pd.DataFrame):
    print("\nStatystyki IMU:\n")

    # Wymuszenie pełnego wyświetlania
    with pd.option_context(
        'display.max_rows', None,
        'display.max_columns', None,
        'display.width', 200,
        'display.float_format', '{:.6f}'.format
    ):
        print(stats)


def plot_histograms(df: pd.DataFrame, save=False):
    cols = ["av_x", "av_y", "av_z", "av_norm",
            "la_x", "la_y", "la_z", "la_norm"]

    df[cols].hist(bins=50, figsize=(14, 8))
    plt.suptitle("Histogramy IMU")

    if save:
        plt.savefig("imu_histograms.png", dpi=150)

    plt.show()


def plot_time_series(df: pd.DataFrame, save=False):
    t = df["timestamp"] - df["timestamp"].iloc[0]

    fig, axs = plt.subplots(2, 1, figsize=(12, 8))

    # Angular velocity
    axs[0].plot(t, df["av_x"], label="x")
    axs[0].plot(t, df["av_y"], label="y")
    axs[0].plot(t, df["av_z"], label="z")
    axs[0].set_title("Angular Velocity")
    axs[0].set_xlabel("Time [s]")
    axs[0].set_ylabel("rad/s")
    axs[0].legend()
    axs[0].grid()

    # Linear acceleration
    axs[1].plot(t, df["la_x"], label="x")
    axs[1].plot(t, df["la_y"], label="y")
    axs[1].plot(t, df["la_z"], label="z")
    axs[1].set_title("Linear Acceleration")
    axs[1].set_xlabel("Time [s]")
    axs[1].set_ylabel("m/s²")
    axs[1].legend()
    axs[1].grid()

    plt.tight_layout()

    if save:
        plt.savefig("imu_timeseries.png", dpi=150)

    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag_path")
    parser.add_argument("--topic", default=TOPIC_NAME)
    parser.add_argument("--save_plots", action="store_true")

    args = parser.parse_args()

    df = read_imu_data(Path(args.bag_path), args.topic)

    stats = pd.DataFrame({
        col: compute_basic_stats(df[col])
        for col in df.columns if col != "timestamp"
    })

    print("Liczba próbek:", len(df))
    print_full_stats(stats)

    # ✅ wykresy
    plot_histograms(df, save=args.save_plots)
    plot_time_series(df, save=args.save_plots)


if __name__ == "__main__":
    main()