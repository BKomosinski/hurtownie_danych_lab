#!/usr/bin/env python3

from pathlib import Path
import argparse

import numpy as np
import pandas as pd

from rosbags.highlevel import AnyReader


TOPIC_NAME = "/sensing/gnss/ublox_moving_base_node/fix"


def compute_basic_stats(values: pd.Series) -> pd.Series:
    """
    Wyznacza podstawowe miary statystyczne dla jednej kolumny danych.
    """
    return pd.Series({
        "count": values.count(),
        "mean": values.mean(),
        "median": values.median(),
        "std": values.std(ddof=1),
        "var": values.var(ddof=1),
        "min": values.min(),
        "max": values.max(),
        "range": values.max() - values.min(),
        "q1": values.quantile(0.25),
        "q3": values.quantile(0.75),
        "iqr": values.quantile(0.75) - values.quantile(0.25),
    })


def read_gnss_fix_messages(bag_path: Path, topic_name: str) -> pd.DataFrame:
    """
    Odczytuje wiadomości NavSatFix z podanego tematu w pliku/katalogu rosbag2.
    Zwraca DataFrame z kolumnami: timestamp_ns, latitude, longitude, altitude.
    """
    rows = []

    with AnyReader([bag_path]) as reader:
        connections = [
            conn for conn in reader.connections
            if conn.topic == topic_name
        ]

        if not connections:
            available_topics = sorted({conn.topic for conn in reader.connections})
            raise RuntimeError(
                f"Nie znaleziono tematu: {topic_name}\n\n"
                f"Dostępne tematy w bagu:\n" +
                "\n".join(available_topics)
            )

        for connection, timestamp, rawdata in reader.messages(connections=connections):
            msg = reader.deserialize(rawdata, connection.msgtype)

            rows.append({
                "timestamp_ns": timestamp,
                "latitude": float(msg.latitude),
                "longitude": float(msg.longitude),
                "altitude": float(msg.altitude),
            })

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError(f"Temat {topic_name} istnieje, ale nie zawiera wiadomości.")

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Wyznaczanie podstawowych statystyk GNSS dla wiadomości NavSatFix z rosbag2 MCAP."
    )

    parser.add_argument(
        "bag_path",
        type=str,
        help="Ścieżka do pliku .mcap albo katalogu rosbag2."
    )

    parser.add_argument(
        "--topic",
        type=str,
        default=TOPIC_NAME,
        help=f"Nazwa tematu. Domyślnie: {TOPIC_NAME}"
    )

    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Opcjonalna ścieżka do zapisu statystyk jako CSV."
    )

    args = parser.parse_args()

    bag_path = Path(args.bag_path)

    if not bag_path.exists():
        raise FileNotFoundError(f"Nie znaleziono ścieżki: {bag_path}")

    df = read_gnss_fix_messages(bag_path, args.topic)

    stats = pd.DataFrame({
        "latitude": compute_basic_stats(df["latitude"]),
        "longitude": compute_basic_stats(df["longitude"]),
        "altitude": compute_basic_stats(df["altitude"]),
    })

    print("\nLiczba odczytanych wiadomości:", len(df))
    print("\nZakres czasu:")
    print("  timestamp_ns min:", df["timestamp_ns"].min())
    print("  timestamp_ns max:", df["timestamp_ns"].max())

    print("\nPodstawowe statystyki:")
    print(stats)

    if args.csv:
        stats.to_csv(args.csv, index=True)
        print(f"\nZapisano statystyki do pliku: {args.csv}")


if __name__ == "__main__":
    main()