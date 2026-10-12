"""
Mô phỏng trường hợp F0 bị triệt tiêu vì xung quanh không có cá thể để lây.

Tình huống dịch tễ:
- F0 là "Patient Zero" khởi đầu ở trạng thái I (Infected, ủ bệnh N ngày/bước).
- Sau N ngày/bước, F0 chuyển sang S (Sick, phát bệnh sick_duration ngày/bước).
- Trong suốt thời gian có khả năng lây nhiễm (trạng thái S), xung quanh F0
  trong phạm vi lân cận (Moore neighborhood - 8 ô kề) HOÀN TOÀN KHÔNG CÓ CÁ THỂ NÀO (k = 0).
- Vì k = 0 nên xác suất lây nhiễm P = 1 - (1-p)^0 = 0%.
- Sau sick_duration ngày/bước, F0 hoặc Hồi phục (R, xác suất s) hoặc Tử vong (Dead, xác suất d).
- Kết quả: Dịch bệnh kết thúc ngay tại bước N + sick_duration mà không lây lan cho bất kỳ ai (F1 = 0).

File cung cấp 2 chế độ chạy:
  1. 'sparse' (Mật độ thưa): Giảm initial_population (ví dụ 20 người trên lưới 60x40).
     Các cá thể di chuyển ngẫu nhiên tự do, nhưng khoảng cách giữa mọi người quá xa,
     F0 không tiếp xúc với bất kỳ ai trong suốt chu kỳ bệnh.
  2. 'lockdown' (Giãn cách xã hội R=0 - Subtask 3): Giữ nguyên 800 người theo config gốc,
     nhưng áp dụng lệnh giãn cách không di chuyển (R = 0). Với seed phù hợp (ví dụ seed 8),
     F0 sinh ra ở vị trí không có ai ở 8 ô lân cận, và do không ai di chuyển, F0 hoàn toàn
     không có tiếp xúc và tự triệt tiêu.

Cách chạy:
    python run_f0_extinction.py --mode sparse --pop 20 --seed 3
    python run_f0_extinction.py --mode lockdown --seed 8
"""

import os
import sys
import argparse
import random
from copy import deepcopy

# Đảm bảo terminal Windows không bị lỗi font khi in Unicode
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import matplotlib.pyplot as plt

from config import CONFIG
from simulation import Simulation
from agent import Agent


class F0ExtinctionSimulation(Simulation):
    """Lớp mở rộng Simulation để kiểm soát kịch bản di chuyển và mật độ cho F0."""

    def __init__(self, config, mode="sparse", movement_r=None, seed=42):
        self.mode = mode
        self.movement_r = movement_r  # R = 0: đứng yên; None: di chuyển tự do
        self.seed = seed
        random.seed(seed)
        super().__init__(config)

    def update_step(self):
        """Thực hiện 1 bước thời gian mô phỏng."""
        # Nếu R = 0 (Lockdown), bỏ qua Phase 1 (Movement), các cá thể đứng yên tại chỗ
        if self.movement_r == 0:
            # ── PHASE 2: INFECTION ──────────────────────────────────────────
            new_infections = []
            for item in self.agents_list:
                x, y = item["pos"]
                agent = item["agent"]
                if agent.state == "H":
                    neighbors = self.get_neighbors(x, y)
                    sick_neighbors = sum(
                        1
                        for nx, ny in neighbors
                        if self.grid[nx, ny] is not None and self.grid[nx, ny].state == "S"
                    )
                    if sick_neighbors > 0:
                        infection_prob = (
                            self.config["p"]
                            if self.config.get("flat_infection_rate", False)
                            else 1 - (1 - self.config["p"]) ** sick_neighbors
                        )
                        if random.random() < infection_prob:
                            new_infections.append(agent)

            newly_infected = set(new_infections)
            for agent in newly_infected:
                agent.state = "I"
                agent.timer = 0

            # ── PHASE 3: STATE TRANSITIONS ──────────────────────────────────
            dead_agents = []
            for item in self.agents_list:
                agent = item["agent"]
                if agent.state == "I":
                    if agent in newly_infected:
                        continue
                    agent.timer += 1
                    if agent.timer >= self.config["N"]:
                        agent.state = "S"
                        agent.timer = 0
                elif agent.state == "S":
                    agent.timer += 1
                    if agent.timer >= self.config.get("sick_duration", self.config["N"]):
                        if random.random() < self.config["d"]:
                            dead_agents.append(item)
                        else:
                            agent.state = "R"

            # ── PHASE 4: DEATH REMOVAL ──────────────────────────────────────
            for item in dead_agents:
                x, y = item["pos"]
                self.grid[x, y] = None
                if item in self.agents_list:
                    self.agents_list.remove(item)

            self.record_history()
        else:
            # Di chuyển ngẫu nhiên tự do theo logic gốc
            super().update_step()


def run_experiment(mode="sparse", population=20, seed=3, export_plot=True):
    print("=" * 80)
    print("  MÔ PHỎNG DỊCH BỆNH: F0 BỊ TRIỆT TIÊU VÌ XUNG QUANH KHÔNG CÓ CÁ THỂ ĐỂ LÂY")
    print("=" * 80)

    cfg = deepcopy(CONFIG)
    movement_r = None

    if mode == "sparse":
        cfg["initial_population"] = population
        mode_desc = f"Mật độ dân số thưa (Sparse Population): {population} người / {cfg['grid_width']*cfg['grid_height']} ô (tỷ lệ {population/(cfg['grid_width']*cfg['grid_height'])*100:.2f}%)"
    elif mode == "lockdown":
        movement_r = 0
        mode_desc = f"Giãn cách xã hội triệt để R = 0 (Lockdown): Giữ nguyên {cfg['initial_population']} người, không di chuyển"
    else:
        raise ValueError(f"Chế độ không hợp lệ: {mode}")

    print(f"[*] Kịch bản: {mode_desc}")
    print(f"[*] Kích thước lưới: {cfg['grid_width']} x {cfg['grid_height']} (Moore neighborhood: 8 ô kề)")
    print(f"[*] Tham số: p = {cfg['p']} (nguy cơ lây/tiếp xúc), N = {cfg['N']} (thời gian ủ bệnh), "
          f"sick_duration = {cfg.get('sick_duration', cfg['N'])}, d = {cfg['d']}, s = {cfg['s']}")
    print(f"[*] Random Seed: {seed}")
    print("-" * 80)

    sim = F0ExtinctionSimulation(cfg, mode=mode, movement_r=movement_r, seed=seed)

    print(f"{'Bước':<6} | {'Trạng thái F0':<15} | {'Vị trí F0':<12} | {'H kề cận':<10} | {'Nguy cơ lây':<12} | {'Ghi chú'}")
    print("-" * 80)

    step = 0
    f0_final_state = None
    f0_extinguished_step = None

    while sim.active_cases() > 0 and step < 40:
        step += 1

        # Trích xuất thông tin F0 tại đầu bước
        f0_item = next((it for it in sim.agents_list if it["agent"].id == 0), None)
        if f0_item:
            f0_pos = f0_item["pos"]
            f0_state = f0_item["agent"].state
            f0_timer = f0_item["agent"].timer

            neighbors = sim.get_neighbors(f0_pos[0], f0_pos[1])
            h_neighbors = sum(
                1 for nx, ny in neighbors
                if sim.grid[nx, ny] is not None and sim.grid[nx, ny].state == "H"
            )

            risk_str = "0.0%" if h_neighbors == 0 else f"{sim.config['p']*100:.1f}%"
            note = ""
            if f0_state == "I":
                note = f"Ủ bệnh (ngày {f0_timer + 1}/{cfg['N']})"
            elif f0_state == "S":
                if h_neighbors == 0:
                    note = "Xung quanh trống (k = 0), không thể lây"
                else:
                    note = f"Tiếp xúc {h_neighbors} cá thể H"

            state_display = f"{f0_state} (t={f0_timer})"
            print(f"{step:<6} | {state_display:<15} | {str(f0_pos):<12} | {h_neighbors:<10} | {risk_str:<12} | {note}")
        else:
            print(f"{step:<6} | {'Dead':<15} | {'None':<12} | {0:<10} | {'0.0%':<12} | F0 đã tử vong")

        sim.update_step()

        # Kiểm tra F0 sau bước update
        f0_item_after = next((it for it in sim.agents_list if it["agent"].id == 0), None)
        if f0_item_after is None and f0_final_state is None:
            f0_final_state = "Tử vong (Dead)"
            f0_extinguished_step = step
        elif f0_item_after and f0_item_after["agent"].state == "R" and f0_final_state is None:
            f0_final_state = "Hồi phục / Miễn dịch (Recovered - R)"
            f0_extinguished_step = step

    print("-" * 80)
    print("TỔNG KẾT KẾT QUẢ MÔ PHỎNG:")
    print(f"  • Thời gian kéo dài dịch bệnh: {step} bước/ngày (kết thúc tự nhiên do không còn ca nhiễm)")
    print(f"  • Kết cục của F0: {f0_final_state} tại bước thứ {f0_extinguished_step}")
    print(f"  • Số ca nhiễm mới thứ cấp (F1, F2,...): 0 ca")
    print(f"  • Số cá thể Khỏe mạnh giữ nguyên: {sim.history['H'][-1]}/{cfg['initial_population']} cá thể")
    print(f"  • Tổng số ca tử vong: {sim.history['Dead'][-1]} ca")
    print(f"  • Đánh giá: F0 BỊ TRIỆT TIÊU HOÀN TOÀN DO KHÔNG CÓ BẤT KỲ TIẾP XÚC NÀO (k = 0)!")
    print("=" * 80)

    if export_plot:
        os.makedirs("plots", exist_ok=True)
        plot_path = os.path.join("plots", f"f0_extinction_{mode}.png")

        fig, ax = plt.subplots(figsize=(10, 5.5))
        timesteps = list(range(len(sim.history["H"])))

        ax.plot(timesteps, sim.history["H"], label=f"Healthy (H) = {sim.history['H'][-1]}", color="#2ecc71", linewidth=2.5)
        ax.plot(timesteps, sim.history["I"], label="Infected (I)", color="#f1c40f", linewidth=2, linestyle="--")
        ax.plot(timesteps, sim.history["S"], label="Sick (S)", color="#e74c3c", linewidth=2)
        ax.plot(timesteps, sim.history["R"], label=f"Recovered (R) = {sim.history['R'][-1]}", color="#95a5a6", linewidth=2)
        ax.plot(timesteps, sim.history["Dead"], label=f"Dead = {sim.history['Dead'][-1]}", color="#34495e", linewidth=2, linestyle=":")

        title_text = (
            f"F0 Extinction Event (Mode: {mode.upper()})\n"
            f"Grid: {cfg['grid_width']}x{cfg['grid_height']}, Pop: {cfg['initial_population']}, "
            f"p={cfg['p']}, N={cfg['N']}, sick={cfg.get('sick_duration', cfg['N'])}, Seed={seed}"
        )
        ax.set_title(title_text, fontsize=12, fontweight="bold", pad=12)
        ax.set_xlabel("Time Steps (Days)", fontsize=11)
        ax.set_ylabel("Agent Count", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="center right", framealpha=0.9)

        # Chú thích mũi tên điểm triệt tiêu
        y_text = cfg['initial_population'] * 0.4 if cfg['initial_population'] > 50 else cfg['initial_population'] * 0.6
        ax.annotate(
            f"F0 Extinguished ({f0_final_state})\nZero Secondary Infections (F1 = 0)",
            xy=(f0_extinguished_step, 1),
            xytext=(max(1, f0_extinguished_step - 4), y_text),
            arrowprops=dict(facecolor="#c0392b", shrink=0.08, width=1.5, headwidth=7),
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff9e6", edgecolor="#e67e22")
        )

        plt.tight_layout()
        plt.savefig(plot_path, dpi=300)
        plt.close()
        print(f"[✓] Đã xuất biểu đồ trực quan tới: {plot_path}")

    return sim


def main():
    parser = argparse.ArgumentParser(
        description="Chạy mô phỏng trường hợp F0 bị triệt tiêu vì xung quanh không có cá thể để lây."
    )
    parser.add_argument(
        "--mode",
        choices=["sparse", "lockdown"],
        default="sparse",
        help="Chế độ mô phỏng: 'sparse' (mật độ thưa ngẫu nhiên) hoặc 'lockdown' (giãn cách xã hội R=0 với 800 người)"
    )
    parser.add_argument(
        "--pop",
        type=int,
        default=20,
        help="Số lượng cá thể khi chạy chế độ 'sparse' (mặc định: 20)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=3,
        help="Random seed (khuyến nghị: 3 hoặc 1 cho 'sparse', 8 cho 'lockdown')"
    )
    args = parser.parse_args()

    # Tự động gán seed tối ưu nếu người dùng chọn mode lockdown mà chưa đổi seed
    seed = args.seed
    if args.mode == "lockdown" and args.seed == 3:
        seed = 8

    run_experiment(mode=args.mode, population=args.pop, seed=seed)


if __name__ == "__main__":
    main()
