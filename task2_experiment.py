import csv
import os
import random
from copy import deepcopy
from statistics import mean, stdev

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import numpy as np

from config import CONFIG
from simulation import Simulation


TASK2_MASTER_SEED = 20260712
TASK2_DEFAULT_SEEDS = [101, 203, 307, 409, 503]
TASK2_BASELINE = {
    "p": 0.3,
    "N": 5,
    "max_steps": 300,
}


def generate_fixed_seeds():
    rng = random.Random(TASK2_MASTER_SEED)
    return rng.sample(range(1, 10000), 5)


def d_values(start, end, step):
    values = []
    value = start
    while value <= end + 1e-9:
        values.append(round(value, 1))
        value += step
    return values


def build_task2_config(d_value):
    config = deepcopy(CONFIG)
    config["p"] = TASK2_BASELINE["p"]
    config["N"] = TASK2_BASELINE["N"]
    config["d"] = round(d_value, 1)
    config["s"] = round(1.0 - d_value, 1)
    return config


def create_seeded_simulation(d_value, seed):
    random.seed(seed)
    np.random.seed(seed)
    return Simulation(build_task2_config(d_value))


def current_counts(sim):
    if sim.history["H"]:
        return {
            "H": sim.history["H"][-1],
            "I": sim.history["I"][-1],
            "S": sim.history["S"][-1],
            "R": sim.history["R"][-1],
            "Dead": sim.history["Dead"][-1],
        }

    return sim.count_states()


def compute_metrics(sim, d_value, seed, duration):
    infected_plus_sick = [
        infected + sick for infected, sick in zip(sim.history["I"], sim.history["S"])
    ]
    counts = current_counts(sim)

    return {
        "d": round(d_value, 1),
        "s": round(1.0 - d_value, 1),
        "seed": seed,
        "epidemic_duration": duration,
        "total_deaths": counts["Dead"],
        "final_recovered": counts["R"],
        "peak_sick": max(sim.history["S"]) if sim.history["S"] else counts["S"],
        "peak_infected_plus_sick": (
            max(infected_plus_sick) if infected_plus_sick else counts["I"] + counts["S"]
        ),
    }


def run_setting_fast(d_value, seed):
    sim = create_seeded_simulation(d_value, seed)
    duration = TASK2_BASELINE["max_steps"]

    for step in range(1, TASK2_BASELINE["max_steps"] + 1):
        sim.update_step()
        if sim.active_cases() == 0:
            duration = step
            break

    return compute_metrics(sim, d_value, seed, duration)


def summarize_task2(raw_results):
    summary = []
    grouped = {}
    for row in raw_results:
        grouped.setdefault(row["d"], []).append(row)

    for d_value in sorted(grouped):
        rows = grouped[d_value]
        durations = [row["epidemic_duration"] for row in rows]
        deaths = [row["total_deaths"] for row in rows]
        peak_sick = [row["peak_sick"] for row in rows]
        summary.append(
            {
                "d": d_value,
                "s": round(1.0 - d_value, 1),
                "duration_mean": mean(durations),
                "duration_std": stdev(durations) if len(durations) > 1 else 0.0,
                "deaths_mean": mean(deaths),
                "deaths_std": stdev(deaths) if len(deaths) > 1 else 0.0,
                "peak_sick_mean": mean(peak_sick),
                "peak_sick_std": stdev(peak_sick) if len(peak_sick) > 1 else 0.0,
            }
        )
    return summary


def export_task2_outputs(raw_results, summary):
    os.makedirs("results", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    raw_path = "results/task2_raw_runs.csv"
    summary_path = "results/task2_summary.csv"

    with open(raw_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(raw_results[0].keys()))
        writer.writeheader()
        writer.writerows(raw_results)

    with open(summary_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    d_axis = [row["d"] for row in summary]

    plt.figure(figsize=(8, 5))
    plt.errorbar(
        d_axis,
        [row["duration_mean"] for row in summary],
        yerr=[row["duration_std"] for row in summary],
        marker="o",
        capsize=4,
    )
    plt.title("Task 2: Epidemic Duration vs Death Rate")
    plt.xlabel("Death rate d")
    plt.ylabel("Epidemic duration (steps)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig("plots/task2_duration_vs_d.png")
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.errorbar(
        d_axis,
        [row["deaths_mean"] for row in summary],
        yerr=[row["deaths_std"] for row in summary],
        marker="o",
        capsize=4,
        color="#e74c3c",
    )
    plt.title("Task 2: Total Deaths vs Death Rate")
    plt.xlabel("Death rate d")
    plt.ylabel("Total deaths")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.savefig("plots/task2_deaths_vs_d.png")
    plt.close()

    return raw_path, summary_path
