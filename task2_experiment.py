"""
Task 2 Experiment — Nghiên cứu ảnh hưởng của tỷ lệ tử vong (d) và hồi phục (s)
lên độ dài làn sóng dịch bệnh (epidemic wave length / duration) và số ca tử vong.

Bám sát yêu cầu đề bài Subtask 2:
1. Cố định các tham số cơ sở: p = 0.3, N = 5, sick_duration = 5 (moderate baseline).
2. Biến thiên d từ 0.0 đến 0.9 với bước nhảy 0.1, ràng buộc s = 1 - d.
3. Chạy tối thiểu 5 lần lặp độc lập (5 seeds) cho mỗi giá trị d để tính Mean ± Std.
4. Điều kiện dừng: Khi không còn ca bệnh hoạt động (active_cases == 0, tức không còn I hoặc S).
5. Ghi nhận: Thời gian kéo dài dịch bệnh (epidemic duration) và tổng số ca tử vong (total deaths).
6. Xuất deliverables: File CSV kết quả và các biểu đồ duration vs d, deaths vs d kèm error bars.
"""

import csv
import argparse
import os
import random
from copy import deepcopy
from statistics import mean, stdev

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import numpy as np

from config import CONFIG
from simulation import Simulation


# ── HẰNG SỐ & BASELINE THEO ĐỀ BÀI TASK 2 ───────────────────────────────────────
# Đề bài yêu cầu: "Choose a moderate baseline (e.g., p = 0.3, N = 5)."
# Yêu cầu chung: "Run at least 5 simulation repetitions (with different random seeds)"
TASK2_MASTER_SEED = 20260712
TASK2_DEFAULT_SEEDS = [101, 203, 307, 409, 503, 607, 709, 812, 919, 1021]  # 10 seed cố định đảm bảo tính tái lập (reproducibility)
TASK2_BASELINE = {
    "p": 0.3,             # Xác suất lây nhiễm mỗi lần tiếp xúc (moderate)
    "N": 5,               # Thời gian ủ bệnh: 5 ngày/bước
    "sick_duration": 5,   # Thời gian phát bệnh lây lan: 5 ngày/bước
    "max_steps": 1000,    # Ngưỡng an toàn chống lặp vô hạn (censoring threshold)
}


def generate_fixed_seeds(count=10):
    """Tạo ngẫu nhiên các seed khác nhau nếu cần mở rộng tập seed."""
    rng = random.Random(TASK2_MASTER_SEED)
    return rng.sample(range(1, 10000), count)


def d_values(start, end, step):
    """Tạo danh sách các giá trị d từ start đến end với bước nhảy step.
    
    Ví dụ: d_values(0.0, 0.9, 0.1) -> [0.0, 0.1, 0.2, ..., 0.9]
    Làm tròn round(x, 1) để tránh sai số dấu phẩy động của float (ví dụ 0.300000000004).
    """
    if step <= 0:
        raise ValueError("d step must be positive")
    if not 0.0 <= start <= end <= 1.0:
        raise ValueError("d range must satisfy 0 <= start <= end <= 1")
    values = []
    value = start
    while value <= end + 1e-9:
        values.append(round(value, 1))
        value += step
    return values


def build_task2_config(d_value, flat_infection_rate=None):
    """Tạo cấu hình mô phỏng cho từng kịch bản d cụ thể.
    
    Quy tắc:
    - Ưu tiên đọc các tham số cơ sở (p, N, sick_duration) trực tiếp từ CONFIG nếu người dùng tùy chỉnh.
      Nếu không có trong CONFIG thì dùng TASK2_BASELINE làm giá trị mặc định.
    - Cập nhật d và tự động suy ra s = 1.0 - d để thỏa mãn ràng buộc s + d = 1.
    - Hỗ trợ cờ flat_infection_rate nếu được chỉ định.
    """
    config = deepcopy(CONFIG)
    config["p"] = CONFIG.get("p", TASK2_BASELINE["p"])
    config["N"] = CONFIG.get("N", TASK2_BASELINE["N"])
    config["sick_duration"] = CONFIG.get("sick_duration", TASK2_BASELINE["sick_duration"])
    config["d"] = round(d_value, 1)
    config["s"] = round(1.0 - d_value, 1)
    if flat_infection_rate is not None:
        config["flat_infection_rate"] = flat_infection_rate
    return config


def create_seeded_simulation(d_value, seed, flat_infection_rate=None):
    """Khởi tạo một instance Simulation với seed cố định cho cả random và numpy.
    
    Đảm bảo tính khoa học và có thể kiểm chứng lại kết quả (reproducible).
    """
    random.seed(seed)
    np.random.seed(seed)
    return Simulation(build_task2_config(d_value, flat_infection_rate=flat_infection_rate))


def current_counts(sim):
    """Lấy số lượng cá thể ở từng trạng thái tại bước cuối cùng của mô phỏng."""
    if sim.history["H"]:
        return {
            "H": sim.history["H"][-1],
            "I": sim.history["I"][-1],
            "S": sim.history["S"][-1],
            "R": sim.history["R"][-1],
            "Dead": sim.history["Dead"][-1],
        }

    return sim.count_states()


def compute_metrics(sim, d_value, seed, duration, ended_naturally=None):
    """Thu thập các chỉ số quan trọng sau khi 1 lượt chạy mô phỏng hoàn tất.
    
    Các chỉ số gồm:
    - epidemic_duration: Thời điểm dịch kết thúc tự nhiên (không còn ca I hoặc S).
    - ended_naturally: True nếu kết thúc do hết nguồn lây, False nếu chạm trần max_steps.
    - total_deaths: Tổng số cá thể đã chết tính đến khi dịch tàn.
    - final_recovered: Số cá thể hồi phục miễn dịch (R).
    - peak_sick: Đỉnh số người ốm nặng cùng lúc (tải hệ thống y tế).
    """
    infected_plus_sick = [
        infected + sick for infected, sick in zip(sim.history["I"], sim.history["S"])
    ]
    counts = current_counts(sim)
    if ended_naturally is None:
        ended_naturally = sim.active_cases() == 0

    return {
        "d": round(d_value, 1),
        "s": round(1.0 - d_value, 1),
        "seed": seed,
        "epidemic_duration": duration,
        "ended_naturally": ended_naturally,
        "total_deaths": counts["Dead"],
        "final_recovered": counts["R"],
        "peak_sick": max(sim.history["S"]) if sim.history["S"] else counts["S"],
        "peak_infected_plus_sick": (
            max(infected_plus_sick) if infected_plus_sick else counts["I"] + counts["S"]
        ),
    }


def run_setting_fast(d_value, seed, flat_infection_rate=None):
    """Chạy mô phỏng không cần giao diện đồ họa (headless) cho 1 cặp (d, seed).
    
    Logic dừng tự nhiên:
    - Mỗi bước gọi sim.update_step().
    - Kiểm tra sim.active_cases(): nếu == 0 (tức I=0 và S=0), dịch đã dập tắt.
    - Dừng ngay lập tức để ghi nhận chính xác 'epidemic_duration' theo đúng định nghĩa đề bài:
      "time steps until no Sick or Infected remain".
    """
    max_steps = CONFIG.get("max_steps", TASK2_BASELINE["max_steps"])
    sim = create_seeded_simulation(d_value, seed, flat_infection_rate=flat_infection_rate)
    duration = max_steps

    for step in range(1, max_steps + 1):
        sim.update_step()
        if sim.active_cases() == 0:
            duration = step
            break

    return compute_metrics(sim, d_value, seed, duration, sim.active_cases() == 0)


def summarize_task2(raw_results):
    """Thống kê tổng hợp (Aggregation) theo từng giá trị d qua 5 lần chạy lặp.
    
    Tính Mean (giá trị trung bình) và Std (độ lệch chuẩn) cho:
    - epidemic_duration
    - total_deaths
    - peak_sick
    Đáp ứng yêu cầu: 'report averages as well as standard deviations'.
    """
    summary = []
    grouped = {}
    for row in raw_results:
        grouped.setdefault(row["d"], []).append(row)

    for d_value in sorted(grouped):
        rows = grouped[d_value]
        durations = [row["epidemic_duration"] for row in rows]
        deaths = [row["total_deaths"] for row in rows]
        peak_sick = [row["peak_sick"] for row in rows]
        completed = [row["ended_naturally"] for row in rows]
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
                "completed_runs": sum(completed),
                "censored_runs": len(completed) - sum(completed),
            }
        )
    return summary


def export_task2_outputs(raw_results, summary, results_dir="results", plots_dir="plots"):
    """Xuất tất cả sản phẩm nghiên cứu (deliverables) ra file:
    
    1. CSV:
       - task2_raw_runs.csv: Dữ liệu chi tiết từng lần chạy (45 hàng = 9 giá trị d * 5 seed).
       - task2_summary.csv: Bảng tổng hợp Mean ± Std cho từng mức d.
    2. Biểu đồ hình ảnh (Plots):
       - task2_duration_vs_d.png: Biểu đồ độ dài làn sóng dịch theo d có thanh sai số (error bar).
       - task2_deaths_vs_d.png: Biểu đồ tổng số ca tử vong theo d có thanh sai số (error bar).
       - task2_epidemic_curves.png: So sánh diễn biến thời gian giữa các kịch bản d khác nhau.
    """
    if not raw_results or not summary:
        raise ValueError("Task 2 output requires at least one completed run")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)

    raw_path = os.path.join(results_dir, "task2_raw_runs.csv")
    summary_path = os.path.join(results_dir, "task2_summary.csv")

    # Lưu dữ liệu thô
    with open(raw_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(raw_results[0].keys()))
        writer.writeheader()
        writer.writerows(raw_results)

    # Lưu dữ liệu tóm tắt
    with open(summary_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    d_axis = [row["d"] for row in summary]

    # --- PLOT 1: Epidemic Duration vs d ---
    plt.figure(figsize=(8, 5))
    plt.errorbar(
        d_axis,
        [row["duration_mean"] for row in summary],
        yerr=[row["duration_std"] for row in summary],
        marker="o",
        capsize=4,
        color="#2980b9",
        linewidth=2,
    )
    plt.title("Task 2: Epidemic Duration vs Death Rate (d)")
    plt.xlabel("Death rate d (with recovery s = 1 - d)")
    plt.ylabel("Epidemic duration (steps until I=0, S=0)")
    plt.grid(True, linestyle="--", alpha=0.6)
    duration_plot_path = os.path.join(plots_dir, "task2_duration_vs_d.png")
    plt.tight_layout()
    plt.savefig(duration_plot_path, dpi=160)
    plt.close()

    # --- PLOT 2: Total Deaths vs d ---
    plt.figure(figsize=(8, 5))
    plt.errorbar(
        d_axis,
        [row["deaths_mean"] for row in summary],
        yerr=[row["deaths_std"] for row in summary],
        marker="o",
        capsize=4,
        color="#e74c3c",
        linewidth=2,
    )
    plt.title("Task 2: Total Deaths vs Death Rate (d)")
    plt.xlabel("Death rate d (with recovery s = 1 - d)")
    plt.ylabel("Total deaths at end of epidemic")
    plt.grid(True, linestyle="--", alpha=0.6)
    deaths_plot_path = os.path.join(plots_dir, "task2_deaths_vs_d.png")
    plt.tight_layout()
    plt.savefig(deaths_plot_path, dpi=160)
    plt.close()

    # --- PLOT 3: Epidemic curves qua thời gian ---
    export_epidemic_curves_plot(plots_dir)

    # --- PLOT 4 & 5: Biểu đồ chi tiết cho từng Seed riêng biệt ---
    if CONFIG.get("export_seed_plots", True):
        export_seed_plots(raw_results, plots_dir)

    return raw_path, summary_path


def export_seed_plots(raw_results, plots_dir="plots"):
    """Xuất các biểu đồ chi tiết cho từng seed:
    
    1. plots/task2_seeds_comparison.png:
       Vẽ tất cả các seed trên cùng một đồ thị (mỗi seed một màu) để đối chiếu
       sự khác biệt và độ nhiễu giữa các lần chạy.
    2. plots/seeds/seed_{seed}.png:
       Tách riêng từng seed thành từng file ảnh độc lập (Duration vs d và Deaths vs d).
    """
    seeds_dir = os.path.join(plots_dir, "seeds")
    os.makedirs(seeds_dir, exist_ok=True)

    by_seed = {}
    for row in raw_results:
        by_seed.setdefault(row["seed"], []).append(row)

    palette = [
        "#e74c3c", "#3498db", "#2ecc71", "#9b59b6", "#f39c12",
        "#1abc9c", "#e67e22", "#34495e", "#16a085", "#d35400"
    ]

    # 1. BIỂU ĐỒ SO SÁNH TẤT CẢ SEEDS TRÊN CÙNG ĐỒ THỊ
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for idx, (seed, rows) in enumerate(sorted(by_seed.items())):
        rows_sorted = sorted(rows, key=lambda r: r["d"])
        d_vals = [r["d"] for r in rows_sorted]
        durations = [r["epidemic_duration"] for r in rows_sorted]
        deaths = [r["total_deaths"] for r in rows_sorted]
        color = palette[idx % len(palette)]

        axes[0].plot(
            d_vals,
            durations,
            marker="o",
            label=f"Seed {seed}",
            color=color,
            alpha=0.85,
            linewidth=1.8,
        )
        axes[1].plot(
            d_vals,
            deaths,
            marker="s",
            label=f"Seed {seed}",
            color=color,
            alpha=0.85,
            linewidth=1.8,
        )

    axes[0].set_title("Task 2: Epidemic Duration vs d (Per-Seed Comparison)")
    axes[0].set_xlabel("Death rate d")
    axes[0].set_ylabel("Epidemic duration (steps)")
    axes[0].grid(True, linestyle="--", alpha=0.6)
    axes[0].legend()

    axes[1].set_title("Task 2: Total Deaths vs d (Per-Seed Comparison)")
    axes[1].set_xlabel("Death rate d")
    axes[1].set_ylabel("Total deaths")
    axes[1].grid(True, linestyle="--", alpha=0.6)
    axes[1].legend()

    plt.tight_layout()
    comparison_path = os.path.join(plots_dir, "task2_seeds_comparison.png")
    plt.savefig(comparison_path, dpi=160)
    plt.close()

    # 2. TÁCH RIÊNG TỪNG SEED THÀNH FILE ẢNH ĐỘC LẬP
    for idx, (seed, rows) in enumerate(sorted(by_seed.items())):
        rows_sorted = sorted(rows, key=lambda r: r["d"])
        d_vals = [r["d"] for r in rows_sorted]
        durations = [r["epidemic_duration"] for r in rows_sorted]
        deaths = [r["total_deaths"] for r in rows_sorted]
        color = palette[idx % len(palette)]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.8))

        ax1.plot(d_vals, durations, marker="o", color=color, linewidth=2)
        ax1.set_title(f"Seed {seed}: Epidemic Duration vs d")
        ax1.set_xlabel("Death rate d (with recovery s = 1 - d)")
        ax1.set_ylabel("Epidemic duration (steps)")
        ax1.grid(True, linestyle="--", alpha=0.6)

        ax2.plot(d_vals, deaths, marker="s", color="#c0392b", linewidth=2)
        ax2.set_title(f"Seed {seed}: Total Deaths vs d")
        ax2.set_xlabel("Death rate d (with recovery s = 1 - d)")
        ax2.set_ylabel("Total deaths")
        ax2.grid(True, linestyle="--", alpha=0.6)

        plt.tight_layout()
        single_path = os.path.join(seeds_dir, f"seed_{seed}.png")
        plt.savefig(single_path, dpi=160)
        plt.close()


def export_epidemic_curves_plot(plots_dir="plots", d_samples=(0.1, 0.5, 0.9), seed=101):
    """Vẽ so sánh chi tiết dạng chuỗi thời gian (time series):
    
    Subplot 1: So sánh tổng số ca hoạt động (I + S) của 3 mức độ d (thấp: 0.1, vừa: 0.5, cao: 0.9).
    Subplot 2: Động thái của đầy đủ 5 trạng thái (H, I, S, R, Dead) ở mức d = 0.5.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = {0.1: "#2ecc71", 0.5: "#f39c12", 0.9: "#e74c3c"}

    max_steps = CONFIG.get("max_steps", TASK2_BASELINE["max_steps"])

    # Vẽ đường cong lây nhiễm I + S cho 3 giá trị d tiêu biểu
    for d_val in d_samples:
        sim = create_seeded_simulation(d_val, seed)
        for _ in range(max_steps):
            sim.update_step()
            if sim.active_cases() == 0:
                break
        active = [i + s for i, s in zip(sim.history["I"], sim.history["S"])]
        axes[0].plot(
            active,
            label=f"d={d_val} (s={round(1 - d_val, 1)})",
            color=colors.get(d_val, "blue"),
            linewidth=2,
        )

    axes[0].set_title("Active Cases (I + S) over Time (Seed 101)")
    axes[0].set_xlabel("Time step")
    axes[0].set_ylabel("Number of Active Cases")
    axes[0].grid(True, linestyle="--", alpha=0.6)
    axes[0].legend()

    # Vẽ toàn cảnh 5 trạng thái vĩ mô cho kịch bản cân bằng d=0.5, s=0.5
    sim_mid = create_seeded_simulation(0.5, seed)
    for _ in range(max_steps):
        sim_mid.update_step()
        if sim_mid.active_cases() == 0:
            break

    axes[1].plot(sim_mid.history["H"], label="Healthy (H)", color="#27ae60", linewidth=1.8)
    axes[1].plot(sim_mid.history["I"], label="Infected (I)", color="#f1c40f", linewidth=1.8)
    axes[1].plot(sim_mid.history["S"], label="Sick (S)", color="#e74c3c", linewidth=1.8)
    axes[1].plot(sim_mid.history["R"], label="Recovered (R)", color="#3498db", linewidth=1.8)
    axes[1].plot(sim_mid.history["Dead"], label="Dead", color="#7f8c8d", linewidth=1.8, linestyle="--")
    axes[1].set_title("Macroscopic State Dynamics (d=0.5, s=0.5, Seed 101)")
    axes[1].set_xlabel("Time step")
    axes[1].set_ylabel("Number of Agents")
    axes[1].grid(True, linestyle="--", alpha=0.6)
    axes[1].legend()

    plt.tight_layout()
    curve_path = os.path.join(plots_dir, "task2_epidemic_curves.png")
    plt.savefig(curve_path, dpi=160)
    plt.close()
    return curve_path


def run_task2_experiment(values=None, seeds=None, progress=False, flat_infection_rate=None):
    """Điều phối toàn bộ quá trình chạy thực nghiệm Task 2.
    
    Tổ chức vòng lặp 2 chiều:
    - Vòng ngoài: lặp qua từng mức tử vong d (0.0 đến 0.9).
    - Vòng trong: lặp qua các random seeds (mặc định 10 seeds) để đảm bảo tính ngẫu nhiên thống kê.
    """
    values = values if values is not None else d_values(0.0, 0.9, 0.1)
    if seeds is None:
        num_s = CONFIG.get("num_seeds", 10)
        seeds = TASK2_DEFAULT_SEEDS[:num_s] if num_s <= len(TASK2_DEFAULT_SEEDS) else generate_fixed_seeds(num_s)

    raw_results = []
    total = len(values) * len(seeds)
    for d_value in values:
        for seed in seeds:
            raw_results.append(run_setting_fast(d_value, seed, flat_infection_rate=flat_infection_rate))
            if progress:
                print(f"Completed {len(raw_results)}/{total}: d={d_value:.1f}, seed={seed}")
    return raw_results, summarize_task2(raw_results)


def main():
    """Hàm main thực thi độc lập từ dòng lệnh, không cần khởi động UI."""
    parser = argparse.ArgumentParser(description="Run the reproducible Task 2 experiment")
    parser.add_argument("--d-start", type=float, default=0.0)
    parser.add_argument("--d-end", type=float, default=0.9)
    parser.add_argument("--d-step", type=float, default=0.1)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--plots-dir", default="plots")
    parser.add_argument(
        "--num-seeds",
        type=int,
        default=CONFIG.get("num_seeds", 10),
        help="Số lượng seeds chạy thực nghiệm (mặc định: 10)",
    )
    parser.add_argument(
        "--flat-infection-rate",
        action="store_true",
        help="Sử dụng xác suất lây cố định là p khi gặp ít nhất 1 Sick (thay vì 1 - (1-p)^k)",
    )
    args = parser.parse_args()

    values = d_values(args.d_start, args.d_end, args.d_step)
    num_s = args.num_seeds
    seeds = TASK2_DEFAULT_SEEDS[:num_s] if num_s <= len(TASK2_DEFAULT_SEEDS) else generate_fixed_seeds(num_s)

    raw_results, summary = run_task2_experiment(
        values=values, seeds=seeds, progress=True, flat_infection_rate=args.flat_infection_rate
    )
    raw_path, summary_path = export_task2_outputs(
        raw_results, summary, args.results_dir, args.plots_dir
    )
    print(f"Saved raw results to {raw_path}")
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()

